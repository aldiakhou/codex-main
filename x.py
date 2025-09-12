"""
Multi-agent research pipeline with Pydantic AI + OpenAI.

This program mirrors the "Multi-agent System Process" diagram:

User ─▶ System ─▶ LeadResearcher ─▶ Subagents (A,B,...) ─▶ Memory ─▶ CitationAgent ─▶ System
           ▲                            │                                        │
           └─────────────── iterative research loop ◀─────────────────────────────┘

Key design choices:
- Use pydantic_ai.Agent for each role, with type-safe structured outputs.
- Delegate to sub-agents *via tools* (the LLM can decide to call them).
- Provide simple, dependency-injected tools: web_search, fetch_url, save/recall memory.
- Keep a small, explicit iterative loop controlled by the model via a structured output.
- Finish by asking the CitationAgent to inject citations back into the final report.

Run:
    python multi_agent_research.py "Compare SMR vs LFP batteries for grid storage."

"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional

import httpx
from duckduckgo_search import DDGS  # no API key required; used as a simple search fallback
from pydantic import BaseModel, Field, HttpUrl, ValidationError
from pydantic_ai import (
    Agent,
    ModelRetry,
    ModelSettings,
    RunContext,
    UnexpectedModelBehavior,
    ToolOutput,
)

# -------------------------------
# 0) Shared types & "memory" layer
# -------------------------------

@dataclass
class MemoryStore:
    """Minimal in-process 'memory' to persist notes across the loop."""
    notes: dict[str, str] = dataclasses.field(default_factory=dict)

    def save(self, key: str, value: str) -> None:
        self.notes[key] = value

    def recall(self, key: str) -> Optional[str]:
        return self.notes.get(key)

    def all(self) -> dict[str, str]:
        return dict(self.notes)


@dataclass
class HttpTools:
    """Lightweight HTTP/search utilities injected as dependencies."""
    client: httpx.AsyncClient


@dataclass
class Deps:
    """All dependencies that any agent/tool might need."""
    http: HttpTools
    memory: MemoryStore


# ------------------------------------------
# 1) Structured output types (strict schemas)
# ------------------------------------------

class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: str


class WebSearchOutput(BaseModel):
    query: str
    results: list[SearchResult]


class FetchPageOutput(BaseModel):
    url: HttpUrl
    title: str
    text: str
    # crude citation key to use later
    cite: str


class Subtask(BaseModel):
    id: str = Field(description="Unique ID for the sub-task, short (e.g. 'A' or 'B').")
    aspect: str = Field(description="What this sub-agent should research.")
    target_depth: str = Field(
        description="Depth like 'quick scan', 'deep dive', 'verify claims'."
    )


class Plan(BaseModel):
    """Plan created by LeadResearcher for this iteration."""
    steps: list[Subtask] = Field(default_factory=list, description="Sub-tasks to execute now.")
    # Ask the model to decide if we should loop again after executing these steps.
    continue_research: bool = Field(
        description="True to continue iterative loop after current steps are done."
    )
    rationale: str


class Finding(BaseModel):
    subtask_id: str
    aspect: str
    summary: str
    # link to citations gathered while researching that subtask
    citations: list[str] = Field(default_factory=list)


class Synthesis(BaseModel):
    """LeadResearcher synthesis output from findings."""
    executive_summary: str
    findings: list[Finding]
    gaps_or_open_questions: list[str] = Field(default_factory=list)
    recommend_next_iteration: bool


class CitationRequest(BaseModel):
    """What we give the CitationAgent."""
    draft_report_markdown: str
    # (url -> "Author, Title, Year" etc.) computed from fetched pages.
    bibliography: dict[str, str]


class FinalReport(BaseModel):
    """What the CitationAgent returns after inserting citations."""
    markdown_with_citations: str


# -------------------------------------------
# 2) Sub-agent factory (research a single aspect)
# -------------------------------------------

def make_subagent() -> Agent[Deps, Finding]:
    """
    A sub-agent performs focused research for ONE aspect.
    It has two tools available: web_search and fetch_page.
    It must return a structured Finding.
    """
    sub = Agent[Deps, Finding](
        'openai:gpt-4o-mini',
        instructions=(
            "You are a precise research sub-agent. "
            "Goal: research the requested aspect, collect a few high-quality sources, "
            "quote short relevant snippets, and produce a concise summary. "
            "Avoid hallucination; prefer authoritative sources (docs, standards, journals, gov). "
            "Add a short list of citation keys (e.g., [cite:URL_HASH]) you saw during research."
        ),
        model_settings=ModelSettings(temperature=0.2, timeout=60),
    )

    @sub.tool
    async def web_search(ctx: RunContext[Deps], query: str, max_results: int = 5) -> WebSearchOutput:
        """
        Use DuckDuckGo to find relevant pages. Returns titles, URLs, and snippets.
        """
        # Simple, dependency-free search using ddg.
        results: list[SearchResult] = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, region="wt-wt", safesearch="moderate"):
                url = r.get("href") or r.get("url") or ""
                title = r.get("title") or ""
                snippet = r.get("body") or r.get("snippet") or ""
                # enforce URL validity; skip malformed
                with contextlib.suppress(ValidationError):
                    results.append(SearchResult(title=title, url=url, snippet=snippet))
        if not results:
            raise ModelRetry("No search results found; please refine the query.")
        return WebSearchOutput(query=query, results=results)

    @sub.tool
    async def fetch_page(ctx: RunContext[Deps], url: HttpUrl, max_chars: int = 6000) -> FetchPageOutput:
        """
        Fetch and extract main text of the page. Truncates to keep context compact.
        """
        # Minimal extraction using readability-lxml if available; else plain text fallback.
        text = ""
        title = ""
        async with ctx.deps.http.client.stream("GET", str(url), timeout=30) as resp:
            resp.raise_for_status()
            html = (await resp.aread()).decode(errors="ignore")
            # Try readability; if not installed, fall back to crude stripping.
            try:
                from readability import Document  # type: ignore
                doc = Document(html)
                title = doc.short_title() or ""
                text = re.sub(r"\s+", " ", doc.summary(html_partial=True))
                # kill tags quickly
                text = re.sub("<[^<]+?>", " ", text)
            except Exception:
                # crude fallback: strip tags
                title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
                title = title.group(1).strip() if title else ""
                text = re.sub("<[^<]+?>", " ", html)
                text = re.sub(r"\s+", " ", text)

        if not text:
            raise ModelRetry("The page had no extractable text; try a different source.")
        if len(text) > max_chars:
            text = text[:max_chars] + "…"

        # Build a stable, short citation key for later insertion.
        cite_key = f"[cite:{abs(hash(str(url))) % 10**8}]"
        # Persist a mapping URL->key so CitationAgent can render bibliography.
        ctx.deps.memory.save(cite_key, str(url))

        return FetchPageOutput(url=url, title=title or str(url), text=text, cite=cite_key)

    return sub


# -----------------------------------------------------
# 3) LeadResearcher: plan → delegate → synthesize cycle
# -----------------------------------------------------

LeadPlan = Plan  # alias for readability


def make_lead_researcher(subagent: Agent[Deps, Finding]) -> Agent[Deps, Synthesis]:
    lead = Agent[Deps, Synthesis](
        'openai:gpt-4o-mini',
        output_type=[ ToolOutput(LeadPlan, name='return_plan')],  # first output a Plan
        instructions=(
            "You are the Lead Researcher. Follow this loop:\n"
            "1) Given the user query and prior memory, create a tactical plan of sub-tasks.\n"
            "2) For each sub-task, call the 'delegate_to_subagent' tool with (subtask_id, aspect, depth).\n"
            "3) Synthesize all findings into an executive summary and bullet findings.\n"
            "4) Decide if another iteration is needed; keep it tight and justify explicitly.\n"
            "Always be factual and traceable; if data is missing, state it clearly."
        ),
        model_settings=ModelSettings(temperature=0.2, timeout=120),
    )

    # Tool 1: Save or recall context quickly
    @lead.tool
    def recall_context(ctx: RunContext[Deps], key: str) -> str:
        """
        Retrieve any saved note from Memory.
        """
        return ctx.deps.memory.recall(key) or ""

    # Tool 2: delegate to sub-agent
    @lead.tool
    async def delegate_to_subagent(
        ctx: RunContext[Deps], subtask_id: str, aspect: str, depth: str
    ) -> Finding:
        """
        Spin up the sub-agent to research one aspect and return a structured Finding.
        """
        prompt = (
            f"Research aspect: {aspect}\n"
            f"Target depth: {depth}\n"
            "Return a concise summary and include the citation keys you used."
        )
        result = await subagent.run(prompt, deps=ctx.deps)
        return result.output

    return lead


# -----------------------------------------------------
# 4) Citation agent: insert citations & bibliography
# -----------------------------------------------------

def make_citation_agent() -> Agent[Deps, FinalReport]:
    cite = Agent[Deps, FinalReport](
        'openai:gpt-4o-mini',
        instructions=(
            "You are a precise citation agent. "
            "Given a draft markdown and a bibliography mapping citation keys to URLs, "
            "insert citation markers after claims and compile a References section. "
            "Keep the author's wording; only add [^n] style footnotes or inline (Author, Year) "
            "and a final 'References' list. Preserve markdown formatting."
        ),
        model_settings=ModelSettings(temperature=0.1, timeout=90),
    )

    @cite.tool
    def fetch_bibliography(ctx: RunContext[Deps]) -> dict[str, str]:
        """
        Return mapping from citation keys to URLs (and any metadata we stored).
        """
        # In a richer system we would store full metadata; here we have URL only.
        return ctx.deps.memory.all()

    return cite


# -----------------------------------------------------
# 5) Orchestrator (System): iterative loop with exit/continue
# -----------------------------------------------------

class LoopDecision(BaseModel):
    plan: Plan


def build_orchestrator() -> Agent[Deps, LoopDecision]:
    """
    Tiny agent to produce a plan for the next iteration, using memory as context.
    This isolates 'planning' to a distinct step (mirrors the diagram's 'save plan').
    """
    planner = Agent[Deps, LoopDecision](
        'openai:gpt-4o-mini',
        instructions=(
            "You are a planning assistant. "
            "Given the user's query and (optional) memory notes, produce a Plan with:\n"
            "- steps: 1–3 Subtask entries (id='A','B',...) with aspect and target_depth\n"
            "- continue_research: bool (True if more work after these steps is helpful)\n"
            "- rationale: short justification."
        ),
        model_settings=ModelSettings(temperature=0.3, timeout=60),
    )
    return planner


# -----------------------------------------------------
# 6) End-to-end orchestration
# -----------------------------------------------------

async def research_pipeline(user_query: str) -> str:
    """
    End-to-end:
      1) Create dependencies (HTTP client, Memory)
      2) Create agents (Subagent, LeadResearcher, Planner, CitationAgent)
      3) Iterate: plan -> delegate -> synthesize, until plan says stop (or cap)
      4) Ask CitationAgent to insert citations and return the final report
    """
    async with httpx.AsyncClient(follow_redirects=True, headers={"User-Agent": "PydanticAI-Research/1.0"}) as client:
        deps = Deps(http=HttpTools(client=client), memory=MemoryStore())

        # Agents
        subagent = make_subagent()
        lead = make_lead_researcher(subagent)
        planner = build_orchestrator()
        citation = make_citation_agent()

        all_findings: list[Finding] = []
        max_loops = 3  # safety cap
        iteration = 0

        while iteration < max_loops:
            iteration += 1

            # --- Plan the next iteration
            plan_res = await planner.run(
                f"User query:\n{user_query}\n\nMemory:\n{json.dumps(deps.memory.all(), indent=2)}"
            )
            plan = plan_res.output
            print(f"plan{plan= }")
            # Persist the plan to memory for traceability
            deps.memory.save(f"plan_iter_{iteration}", plan.model_dump_json())

            # --- Execute plan by delegating to sub-agents
            iter_findings: list[Finding] = []
            for step in plan.steps:
                try:
                    result = await lead.run(
                        (
                            "Run delegate_to_subagent for the following subtask, "
                            "then synthesize across all subtasks at the end of this call."
                        ),
                        deps=deps,
                        # The LLM can call the delegate_to_subagent tool multiple times.
                    )
                    # That call returns a Synthesis. But we want per-step findings.
                    # So, run the delegate tool directly to ensure one Finding per step:
                    finding = await lead.tools["delegate_to_subagent"](  # type: ignore
                        ctx=None,  # pydantic_ai ignores ctx here when called directly by us
                        subtask_id=step.id, aspect=step.aspect, depth=step.target_depth
                    )
                    iter_findings.append(finding)
                except UnexpectedModelBehavior as e:
                    # Defensive: if the tool call fails in a weird way, continue.
                    iter_findings.append(
                        Finding(
                            subtask_id=step.id,
                            aspect=step.aspect,
                            summary=f"Failed to research due to error: {e}",
                            citations=[],
                        )
                    )

            all_findings.extend(iter_findings)

            # --- Synthesize for this iteration
            synth_prompt = (
                "Synthesize findings for this iteration.\n"
                f"User query: {user_query}\n"
                f"Iteration: {iteration}\n"
                f"Findings JSON:\n{json.dumps([f.model_dump() for f in iter_findings], indent=2)}\n"
            )
            synth = (await lead.run(synth_prompt, deps=deps)).output

            # Save synthesis snapshot
            deps.memory.save(f"synthesis_iter_{iteration}", synth.model_dump_json())

            # Exit/continue?
            if not plan.continue_research or not synth.recommend_next_iteration:
                break

        # --- Final drafting (single coherent report)
        draft_md_lines: list[str] = [
            f"# Research report",
            "",
            f"**User query**: {user_query}",
            "",
            "## Executive summary",
        ]

        # Aggregate the last synthesis if present, else merge all findings.
        last_synth_json = deps.memory.recall(f"synthesis_iter_{iteration}") or ""
        if last_synth_json:
            try:
                last_synth = Synthesis.model_validate_json(last_synth_json)
                draft_md_lines.append(last_synth.executive_summary)
            except ValidationError:
                pass

        draft_md_lines += ["", "## Findings"]
        for f in all_findings:
            cites = " ".join(f.citations) if f.citations else ""
            draft_md_lines.append(f"- **[{f.subtask_id}] {f.aspect}** — {f.summary} {cites}")

        draft_md = "\n".join(draft_md_lines)

        # Build a simple bibliography mapping from our memory (cite_key->URL)
        biblio: dict[str, str] = {}
        for k, v in deps.memory.all().items():
            if k.startswith("[cite:"):
                biblio[k] = v

        # Ask the CitationAgent to insert citations and references
        cite_req = CitationRequest(draft_report_markdown=draft_md, bibliography=biblio)
        final = (
            await citation.run(
                "Insert citations into the draft and add a 'References' section at the end.",
                deps=deps,
                input=cite_req,  # extra context for the LLM
            )
        ).output

        return final.markdown_with_citations


# -----------------------------------------------------
# 7) CLI entry point
# -----------------------------------------------------

def _banner() -> None:
    print("=" * 80)
    print(" Pydantic AI — Multi-agent Research Pipeline")
    print("=" * 80)

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the multi-agent research pipeline.")
    parser.add_argument("query", type=str, help="User query to research")
    args = parser.parse_args()

    missing = [name for name in ("OPENAI_API_KEY",) if not os.getenv(name)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        raise SystemExit(2)

    _banner()
    print("User query:", args.query)
    print("Model: openai:gpt-4o-mini")
    print("Loop cap:", 3)
    print("----\n")

    md = asyncio.run(research_pipeline(args.query))
    print(md)
    print("\n" + "=" * 80)
    print(" Done.")
    print("=" * 80)


if __name__ == "__main__":
    main()

# from openai import OpenAI

# client = OpenAI(
#     api_key="8d7f559e971d49579d719f5bf40589d8.eJxWWgsNZUe9Pcc9",
#     base_url="https://api.z.ai/api/paas/v4/"
# )

# completion = client.chat.completions.create(
#     model="glm-4.5",
#     messages=[
#         {"role": "system", "content": "You are a smart and creative novelist"},
#         {"role": "user", "content": "Please write a short fairy tale story as a fairy tale master"}
#     ]
# )

# print(completion.choices[0].message.content)