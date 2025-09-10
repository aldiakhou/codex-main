from __future__ import annotations

import json
from typing import Any, Dict, Optional
from pathlib import Path
import uuid
import os
import requests

from .base import AgentRegistry
from mcp_agents_orchestrator.auth import get_provider_context
try:
    # When running as `python -m mcp_agents_orchestrator`, package import works
    from core.models import AIAgentRequest
except Exception:  # pragma: no cover
    # Fallback for local dev where parent dir was injected into sys.path
    from core.models import AIAgentRequest  # type: ignore


_BASE_PROMPT_CACHE: Optional[str] = None


def _load_base_prompt() -> str:
    global _BASE_PROMPT_CACHE
    if _BASE_PROMPT_CACHE is not None:
        return _BASE_PROMPT_CACHE
    try:
        here = Path(__file__).resolve().parent
        prompt_path = here / "codex_base_prompt.md"
        _BASE_PROMPT_CACHE = prompt_path.read_text(encoding="utf-8")
        return _BASE_PROMPT_CACHE
    except Exception:
        # Fallback minimal, but try to keep shape valid
        _BASE_PROMPT_CACHE = "You are a precise, safe coding agent."
        return _BASE_PROMPT_CACHE


def _responses_call(model: str, text: str, store: bool = False) -> Dict[str, Any]:
    ctx = get_provider_context()
    base_url = ctx["base_url"].rstrip("/")
    url = f"{base_url}/responses"
    headers = {
        "Authorization": ctx["authorization"],
        # For streaming you'd use Accept: text/event-stream + stream=True
        "Content-Type": "application/json",
        # Align with Rust client behavior
        "OpenAI-Beta": "responses=experimental",
        "originator": "codex_mcp_agents",
    }
    # Add session + UA headers matching codex-rs
    headers["User-Agent"] = "codex_mcp_agents/0.1"
    headers["session_id"] = str(uuid.uuid4())
    if ctx.get("account_id") and ctx.get("mode") == "chatgpt":
        headers["chatgpt-account-id"] = ctx["account_id"]

    # Full Codex base instructions (+ optional apply_patch guidance)
    base_instructions = _load_base_prompt()
    try:
        here = Path(__file__).resolve().parent
        ap = here / "prompt.md"
        if ap.exists():
            apply_patch_text = ap.read_text(encoding="utf-8")
            if apply_patch_text.strip():
                base_instructions = f"{apply_patch_text}"
    except Exception:
        pass
    payload: Dict[str, Any] = {
        "model": model,
        "instructions": base_instructions,
        "input": [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"<user_instructions>\n\n{text}\n\n</user_instructions>"},
                ],
            }
        ],
        "tools": [],
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "store": bool(store),
        "stream": True,
        "include": [],
        "prompt_cache_key": headers["session_id"],
    }
    if model.startswith("gpt-5") or model == "gpt-5":
        payload["text"] = {"verbosity": "medium"}

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
    if not resp.ok:
        raise RuntimeError(f"Responses API error: {resp.status_code} {resp.text}")
    return resp.json()


def _simple_agent_handler(req: AIAgentRequest) -> Dict[str, Any]:
    model = str((req.context or {}).get("model") or os.environ.get("AGENT_MODEL") or "gpt-5")
    text = req.text or json.dumps(req.context or {})
    data = _responses_call(model=model, text=text, store=False)
    # Extract a friendly summary from the output when possible
    summary = None
    try:
        out = data.get("output") or []
        # Find last output_text, else raw dump
        for item in reversed(out):
            if item.get("type") == "message":
                parts = item.get("content") or []
                for p in reversed(parts):
                    if p.get("type") == "output_text":
                        summary = p.get("text")
                        break
            if summary:
                break
    except Exception:
        summary = None
    return {"summary": summary or "(see raw)", "raw": data}


def register_mcp_agents(registry: AgentRegistry) -> None:
    info = {
        "name": "Simple OpenAI Agent",
        "description": "Calls the OpenAI Responses API using Codex auth",
        "capabilities": ["responses-api"],
        # UIs can surface required config based on provider
        "server_configs_detail": None,
    }
    registry.register("simple", _simple_agent_handler, info=info)

    # Demo agent that exercises exec + apply_patch approval flows via MCP notifications
    def _demo_exec_patch_handler(req: AIAgentRequest) -> Dict[str, Any]:
        # Import bridge helpers lazily to avoid circular imports
        # __main__ lives inside the mcp_agents_orchestrator package
        from mcp_agents_orchestrator import __main__ as bridge  # type: ignore
        import uuid as _uuid
        import os as _os
        import json as _json

        result: Dict[str, Any] = {
            "summary": "demo_exec_patch completed",
            "exec": {},
            "patch": {},
        }

        # ---- Exec flow ----
        call_id_exec = f"demo_exec_{_uuid.uuid4().hex[:8]}"
        cwd = req.cwd or _os.getcwd()
        cmd = ["echo", "Hello from demo"]
        try:
            bridge.exec_approval_request(call_id_exec, cmd, cwd, reason="demo exec")
            submission_id = bridge.get_submission_id_for_call(call_id_exec)
            decision = None
            if submission_id:
                decision = bridge.wait_for_decision(submission_id, timeout_secs=60.0)
            result["exec"]["decision"] = decision or "none"
            if decision in ("approved", "approved_for_session"):
                bridge.exec_command_begin(call_id_exec, cmd, cwd)
                # Minimal output
                bridge.exec_command_output_delta(call_id_exec, "stdout", b"Hello from demo\n")
                formatted = _json.dumps({
                    "output": "Hello from demo\n",
                    "metadata": {"exit_code": 0, "duration_seconds": 0.1},
                })
                bridge.exec_command_end(call_id_exec, 0, stdout="Hello from demo\n", stderr="", formatted_output=formatted, duration_ms=100)
                result["exec"]["status"] = "executed"
            else:
                result["exec"]["status"] = "skipped"
        except Exception as e:
            result["exec"]["error"] = str(e)

        # ---- Apply patch flow ----
        call_id_patch = f"demo_patch_{_uuid.uuid4().hex[:8]}"
        demo_path = _os.path.join(cwd, "DEMO.txt")
        changes = {
            demo_path: {"type": "add", "content": "Demo content\n"}
        }
        try:
            bridge.apply_patch_approval_request(call_id_patch, changes, reason="demo patch")
            submission_id2 = bridge.get_submission_id_for_call(call_id_patch)
            decision2 = None
            if submission_id2:
                decision2 = bridge.wait_for_decision(submission_id2, timeout_secs=60.0)
            result["patch"]["decision"] = decision2 or "none"
            if decision2 in ("approved", "approved_for_session"):
                bridge.patch_apply_begin(call_id_patch, changes, auto_approved=False)
                # Simulate success
                bridge.patch_apply_end(call_id_patch, success=True, stdout="1 file added", stderr="")
                result["patch"]["status"] = "applied"
            else:
                result["patch"]["status"] = "skipped"
        except Exception as e:
            result["patch"]["error"] = str(e)

        return result

    registry.register(
        "demo_exec_patch",
        _demo_exec_patch_handler,
        info={
            "name": "Demo Exec+Patch Agent",
            "description": "Demonstrates exec and apply_patch approval flows via MCP notifications",
            "capabilities": ["exec", "apply_patch"],
        },
    )


if __name__ == "__main__":  # pragma: no cover
    # load prompt test
    print("Base prompt:")
    print(_load_base_prompt())
    print("----")
    print("Responses call test:")
    print( _responses_call(model="gpt-5", text="Write a Python function that adds two numbers.", store=False) )