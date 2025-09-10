"""
Enhanced Deep Research Agent with document generation and filesystem storage
Creates comprehensive research documents using markdown
"""
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import json
import yaml
import os
import uuid
from datetime import datetime
from pathlib import Path
import hashlib

from pocketflow import AsyncNode, AsyncFlow

from .base import PocketFlowAgent, call_llm
from .utils import safe_mkdir, safe_write_text, get_sandbox_mode, emit_progress, emit_plan
from .mcp_client import PocketFlowMCPClient
from core.models import AIAgentRequest, ResearchResponse, ResearchSection
from core.logging import get_logger

logger = get_logger(__name__)

# Try to import mistune for HTML generation
try:
    import mistune
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    logger.warning("mistune not available - HTML export will be disabled")


class ResearchPlanningNode(AsyncNode):
    """Creates comprehensive research plan with subplans"""
    
    async def prep_async(self, shared):
        request = shared.get("request")
        topic = request.context.get('topic', '')
        depth = request.context.get('depth', 'comprehensive')
        focus_areas = request.context.get('focus_areas', [])
        
        return {
            "topic": topic,
            "depth": depth,
            "focus_areas": focus_areas
        }
    
    async def exec_async(self, context):
        """Create detailed research plan with subplans"""
        topic = context["topic"]
        depth = context["depth"]
        focus_areas = context["focus_areas"]
        
        prompt = f"""Create a comprehensive research plan for deep investigation.

Research Topic: "{topic}"
Depth Required: {depth}
Focus Areas: {', '.join(focus_areas) if focus_areas else 'Comprehensive coverage'}

Create a structured research plan with:
1. Main research plans (3-5 major areas)
2. Subplans for each main plan (2-4 per plan)
3. Research methodology for each subplan
4. Expected outcomes and deliverables

Return YAML format:
```yaml
research_overview:
  topic: "{topic}"
  objective: "Clear research objective"
  scope: "Research boundaries and limitations"
  methodology: "Overall approach"

main_plans:
  - plan_id: "plan_1"
    title: "First Major Research Area"
    description: "What this plan covers"
    priority: "high/medium/low"
    subplans:
      - subplan_id: "plan_1_sub_1"
        title: "Specific Research Question"
        research_queries:
          - "targeted search query 1"
          - "targeted search query 2"
        methodology: "How to research this"
        expected_findings: "What we hope to discover"
        sources_to_target:
          - "academic papers"
          - "industry reports"
      - subplan_id: "plan_1_sub_2"
        title: "Another Specific Aspect"
        research_queries:
          - "search query"
        methodology: "Research approach"
        expected_findings: "Expected outcomes"
        
  - plan_id: "plan_2"
    title: "Second Major Research Area"
    description: "Coverage area"
    priority: "high"
    subplans:
      - subplan_id: "plan_2_sub_1"
        title: "Specific focus"
        research_queries:
          - "query"
        methodology: "Approach"
        expected_findings: "Outcomes"

document_structure:
  - section: "Executive Summary"
    content_from: ["all_plans"]
  - section: "Introduction"
    content_from: ["plan_1"]
  - section: "Main Findings"
    subsections:
      - "Finding Area 1"
      - "Finding Area 2"
  - section: "Recommendations"
    content_from: ["synthesis"]
```"""
        
        response = call_llm(prompt, temperature=0.3)
        
        try:
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            plan = yaml.safe_load(yaml_str)
            
            # Add timestamp and ID
            plan["plan_id"] = hashlib.md5(topic.encode()).hexdigest()[:8]
            plan["created_at"] = datetime.now().isoformat()
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to parse research plan: {e}")
            # Fallback simple plan
            return {
                "research_overview": {
                    "topic": topic,
                    "objective": f"Research {topic}",
                    "scope": "General research",
                    "methodology": "Comprehensive web-based research"
                },
                "main_plans": [
                    {
                        "plan_id": "plan_1",
                        "title": "General Research",
                        "description": f"Comprehensive research on {topic}",
                        "priority": "high",
                        "subplans": [
                            {
                                "subplan_id": "plan_1_sub_1",
                                "title": topic,
                                "research_queries": [topic, f"{topic} overview", f"{topic} analysis"],
                                "methodology": "Web search and analysis",
                                "expected_findings": "Comprehensive understanding"
                            }
                        ]
                    }
                ],
                "plan_id": hashlib.md5(topic.encode()).hexdigest()[:8],
                "created_at": datetime.now().isoformat()
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["research_plan"] = exec_res

        # Determine base directory from request.cwd, fallback to CWD
        request = shared.get("request")
        base_dir = Path(getattr(request, "cwd", None) or os.getcwd())
        rel_dir = Path("research_output") / exec_res["plan_id"]

        # Create directory under sandbox rules
        try:
            out_dir = safe_mkdir(base_dir, rel_dir)
            shared["research_base_dir"] = str(base_dir)
            shared["research_rel_dir"] = str(rel_dir)
            shared["research_dir"] = out_dir  # absolute path convenience

            # Save research plan
            plan_rel = rel_dir / "research_plan.yaml"
            yaml_text = yaml.dump(exec_res, default_flow_style=False, allow_unicode=True)
            safe_write_text(base_dir, plan_rel, yaml_text)
            logger.info(f"Created research directory: {out_dir}")
        except PermissionError as e:
            # Sandbox is read-only: continue without writing to disk
            shared["research_base_dir"] = str(base_dir)
            shared["research_rel_dir"] = str(rel_dir)
            shared["research_dir"] = base_dir / rel_dir
            logger.warning(f"Sandbox prevents writing research files: {e}")
        # Emit plan seed and progress
        try:
            emit_progress(shared, "Research plan created")
            emit_plan(shared, [
                {"step": "Plan research", "status": "completed"},
                {"step": "Setup tools", "status": "pending"},
                {"step": "Execute subplans", "status": "pending"},
                {"step": "Generate report", "status": "pending"},
                {"step": "Prepare response", "status": "pending"},
            ], explanation="Deep research plan")
        except Exception:
            pass
        
        return "setup_research_tools"


class ResearchToolSetupNode(AsyncNode):
    """Sets up research tools including academic and web search"""
    
    async def exec_async(self, _):
        """Initialize research-focused MCP clients"""
        
        server_configs = [
            {
                "name": "py_fetch",
                "config": {
                    "command": "python",
                    "args": ["-m", "mcp_server_fetch"],
                    "type": "stdio"
                },
                "capabilities": ["web", "fetch", "content"]
            }
        ]
        
        available_tools = {}
        for server in server_configs:
            try:
                client = PocketFlowMCPClient(server["config"])
                tools = await client.list_tools_atomic()
                if tools:
                    available_tools[server["name"]] = {
                        "client": client,
                        "tools": tools,
                        "capabilities": server["capabilities"]
                    }
                    logger.info(f"Research tool {server['name']} ready with {len(tools)} tools")
            except Exception as e:
                logger.warning(f"Failed to setup {server['name']}: {e}")
        
        return available_tools
    
async def post_async(self, shared, prep_res, exec_res):
        try:
            emit_progress(shared, f"Research tools ready: {len(exec_res or {})}")
            emit_plan(shared, [
                {"step": "Plan research", "status": "completed"},
                {"step": "Setup tools", "status": "completed"},
                {"step": "Execute subplans", "status": "in_progress"},
                {"step": "Generate report", "status": "pending"},
                {"step": "Prepare response", "status": "pending"},
            ])
        except Exception:
            pass
        shared["research_tools"] = exec_res
        return "execute_subplans"


class SubplanExecutionNode(AsyncNode):
    """Executes research for each subplan and creates documents"""
    
    async def prep_async(self, shared):
        return {
            "research_plan": shared["research_plan"],
            "research_tools": shared["research_tools"],
            "research_base_dir": shared.get("research_base_dir"),
            "research_rel_dir": shared.get("research_rel_dir"),
        }
    
    async def exec_async(self, context):
        """Execute each subplan and create markdown documents"""
        research_plan = context["research_plan"]
        research_tools = context["research_tools"]
        base_dir = Path(context["research_base_dir"] or os.getcwd())
        rel_root = Path(context["research_rel_dir"] or ("research_output/" + research_plan.get("plan_id", "plan")))

        all_results = []
        
        # Process each main plan
        for main_plan in research_plan["main_plans"]:
            plan_results = {
                "plan_id": main_plan["plan_id"],
                "title": main_plan["title"],
                "subplan_results": []
            }
            
            # Create plan directory under sandbox
            plan_rel = rel_root / main_plan["plan_id"]
            try:
                plan_dir = safe_mkdir(base_dir, plan_rel)
            except PermissionError:
                plan_dir = (base_dir / plan_rel)
            
            # Process each subplan
            for subplan in main_plan["subplans"]:
                logger.info(f"Researching subplan: {subplan['title']}")
                
                # Execute research queries
                subplan_data = await self._research_subplan(
                    subplan,
                    research_tools
                )
                
                # Generate document for subplan
                doc_content = await self._generate_subplan_document(
                    subplan,
                    subplan_data,
                    main_plan["title"]
                )
                
                # Save subplan document
                doc_rel = plan_rel / f"{subplan['subplan_id']}.md"
                try:
                    doc_path = safe_write_text(base_dir, doc_rel, doc_content)
                except PermissionError:
                    doc_path = (base_dir / doc_rel)
                
                plan_results["subplan_results"].append({
                    "subplan": subplan,
                    "data": subplan_data,
                    "document_path": str(doc_path)
                })
            
            # Generate plan summary document
            plan_summary = await self._generate_plan_summary(
                main_plan,
                plan_results["subplan_results"]
            )
            
            summary_rel = plan_rel / "plan_summary.md"
            try:
                summary_path = safe_write_text(base_dir, summary_rel, plan_summary)
            except PermissionError:
                summary_path = (base_dir / summary_rel)
            
            plan_results["summary_document"] = str(summary_path)
            all_results.append(plan_results)
        
        return all_results
    
    async def _research_subplan(self, subplan, research_tools):
        """Execute research for a single subplan"""
        results = []
        
        for query in subplan["research_queries"]:
            # Prefer tools that accept a 'query' parameter; else fallback to DuckDuckGo API
            found_any = False
            for tool_name, tool_info in research_tools.items():
                try:
                    tools = tool_info.get("tools", [])
                    def has_query_param(tool):
                        schema = tool.get("inputSchema")
                        props = None
                        if isinstance(schema, dict):
                            props = schema.get("properties")
                        elif hasattr(schema, "properties"):
                            props = getattr(schema, "properties")
                        return isinstance(props, dict) and "query" in props
                    search_tools = [tool for tool in tools if has_query_param(tool)]
                    if not search_tools:
                        continue
                    st = search_tools[0]
                    params = {"query": query}
                    if "limit" in str(st.get("inputSchema", {})):
                        params["limit"] = 5
                    result = await tool_info["client"].call_tool_atomic(st["name"], params)
                    results.append({
                        "query": query,
                        "tool": st["name"],
                        "data": result.get("result", []),
                        "timestamp": datetime.now().isoformat(),
                        "success": result.get("success", False),
                    })
                    found_any = True
                except Exception as e:
                    logger.error(f"Research error for query '{query}' on {tool_name}: {e}")
            if not found_any:
                # DuckDuckGo Instant Answer fallback
                try:
                    from urllib import request as _urlreq, parse as _urlparse
                    q = _urlparse.quote(query)
                    url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
                    with _urlreq.urlopen(url, timeout=10) as resp:
                        data = json.loads(resp.read().decode('utf-8', errors='ignore'))
                    items = []
                    if isinstance(data, dict):
                        if data.get('AbstractURL'):
                            items.append({'title': data.get('Heading') or 'DuckDuckGo', 'url': data.get('AbstractURL'), 'snippet': data.get('AbstractText') or ''})
                        for t in data.get('RelatedTopics', [])[:10]:
                            if isinstance(t, dict) and t.get('FirstURL'):
                                txt = t.get('Text') or ''
                                items.append({'title': txt[:80] or 'Related', 'url': t['FirstURL'], 'snippet': txt})
                    results.append({
                        "query": query,
                        "tool": "duckduckgo",
                        "data": items,
                        "timestamp": datetime.now().isoformat(),
                        "success": True,
                    })
                    # Optionally fetch top result content if mcp_server_fetch is available
                    for tname, tinfo in research_tools.items():
                        fetch_tool = next((t for t in tinfo.get("tools", []) if t.get("name", "").lower()=="fetch"), None)
                        if fetch_tool and items:
                            url = items[0].get('url')
                            if url:
                                fetch_res = await tinfo["client"].call_tool_atomic("fetch", {"url": url, "max_length": 3000})
                                results.append({
                                    "query": url,
                                    "tool": "fetch",
                                    "data": fetch_res.get("result"),
                                    "timestamp": datetime.now().isoformat(),
                                    "success": fetch_res.get("success", False),
                                })
                            break
                except Exception as e:
                    logger.warning(f"DDG fallback failed: {e}")
        
        return results
    
    async def _generate_subplan_document(self, subplan, research_data, plan_title):
        """Generate markdown document for subplan research"""
        
        prompt = f"""Create a comprehensive research document based on the findings.

Main Research Area: {plan_title}
Subplan Topic: {subplan['title']}
Research Methodology: {subplan.get('methodology', 'General research')}
Expected Findings: {subplan.get('expected_findings', 'Comprehensive findings')}

Research Data:
{json.dumps(research_data, indent=2)}

Create a well-structured markdown document with:
1. Clear section headers
2. Comprehensive findings
3. Analysis and insights
4. Key takeaways
5. Sources and references

Use proper markdown formatting:
- # for main headers
- ## for section headers  
- ### for subsections
- **bold** for emphasis
- - bullet points
- > blockquotes for important notes
- [text](url) for links

The document should be academic in tone but accessible."""
        
        response = call_llm(prompt, temperature=0.3)
        
        # Add document header
        header = f"""# {subplan['title']}

**Research Area**: {plan_title}  
**Date**: {datetime.now().strftime('%Y-%m-%d')}  
**Document ID**: {subplan['subplan_id']}

---

"""
        
        return header + response
    
    async def _generate_plan_summary(self, main_plan, subplan_results):
        """Generate summary document for entire plan"""
        
        # Collect all subplan summaries
        subplan_summaries = []
        for result in subplan_results:
            subplan_summaries.append({
                "title": result["subplan"]["title"],
                "document_path": result["document_path"],
                "key_findings": "See detailed document"
            })
        
        prompt = f"""Create a summary document for this research plan.

Research Plan: {main_plan['title']}
Description: {main_plan['description']}

Subplans Completed:
{json.dumps(subplan_summaries, indent=2)}

Create a comprehensive summary that:
1. Synthesizes findings across all subplans
2. Identifies key themes and patterns
3. Highlights important discoveries
4. Notes any contradictions or gaps
5. Provides actionable insights

Format as a professional markdown document."""
        
        response = call_llm(prompt, temperature=0.3)
        
        header = f"""# Research Plan Summary: {main_plan['title']}

**Plan ID**: {main_plan['plan_id']}  
**Priority**: {main_plan.get('priority', 'medium')}  
**Date Completed**: {datetime.now().strftime('%Y-%m-%d')}

---

## Subplans Included

"""
        
        for result in subplan_results:
            header += f"- [{result['subplan']['title']}](./{result['subplan']['subplan_id']}.md)\n"
        
        header += "\n---\n\n"
        
        return header + response
    
async def post_async(self, shared, prep_res, exec_res):
        try:
            emit_progress(shared, "Subplans executed")
            emit_plan(shared, [
                {"step": "Plan research", "status": "completed"},
                {"step": "Setup tools", "status": "completed"},
                {"step": "Execute subplans", "status": "completed"},
                {"step": "Generate report", "status": "in_progress"},
                {"step": "Prepare response", "status": "pending"},
            ])
        except Exception:
            pass
        shared["plan_results"] = exec_res
        return "generate_final_report"


class FinalReportGenerationNode(AsyncNode):
    """Generates comprehensive final research report"""
    
    async def prep_async(self, shared):
        return {
            "research_plan": shared["research_plan"],
            "plan_results": shared["plan_results"],
            "research_dir": shared["research_dir"]
        }
    
    async def exec_async(self, context):
        """Generate final comprehensive research report"""
        research_plan = context["research_plan"]
        plan_results = context["plan_results"]
        research_dir = context["research_dir"]
        
        # Prepare summary data
        all_findings = []
        all_sources = []
        key_insights = []
        
        for plan_result in plan_results:
            all_findings.append({
                "plan": plan_result["title"],
                "findings": f"See {plan_result['summary_document']}"
            })
        
        # Generate final report
        prompt = f"""Create the final comprehensive research report.

Research Topic: {research_plan['research_overview']['topic']}
Research Objective: {research_plan['research_overview']['objective']}
Scope: {research_plan['research_overview']['scope']}

Research Plans Completed:
{json.dumps([p['title'] for p in plan_results], indent=2)}

Create a professional research report with:

1. EXECUTIVE SUMMARY
   - Key findings (3-5 bullet points)
   - Major insights
   - Recommendations

2. INTRODUCTION
   - Research background
   - Objectives and scope
   - Methodology overview

3. RESEARCH FINDINGS
   - Organized by major themes
   - Cross-referenced insights
   - Supporting evidence

4. ANALYSIS & DISCUSSION
   - Patterns and trends
   - Contradictions and debates
   - Implications

5. CONCLUSIONS
   - Summary of findings
   - Answering the research question
   - Confidence assessment

6. RECOMMENDATIONS
   - Actionable next steps
   - Areas for further research
   - Implementation suggestions

7. APPENDICES
   - Research methodology
   - List of all documents generated
   - References

Format as a professional markdown document with clear structure and citations."""
        
        response = call_llm(prompt, temperature=0.3)
        
        # Create final report with metadata
        final_report = f"""# Comprehensive Research Report

**Topic**: {research_plan['research_overview']['topic']}  
**Report ID**: {research_plan['plan_id']}  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Research Depth**: {context.get('depth', 'comprehensive')}

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Introduction](#introduction)
3. [Research Findings](#research-findings)
4. [Analysis & Discussion](#analysis--discussion)
5. [Conclusions](#conclusions)
6. [Recommendations](#recommendations)
7. [Appendices](#appendices)

---

{response}

---

## Research Documents Generated

### Main Research Plans

"""
        
        # Add links to all documents
        for plan_result in plan_results:
            plan_id = plan_result["plan_id"]
            final_report += f"\n#### {plan_result['title']}\n"
            final_report += f"- [Plan Summary](./{plan_id}/plan_summary.md)\n"
            
            for subplan_result in plan_result["subplan_results"]:
                subplan = subplan_result["subplan"]
                final_report += f"- [{subplan['title']}](./{plan_id}/{subplan['subplan_id']}.md)\n"
        
        final_report += "\n---\n\n*End of Report*"
        
        # Save final report
        report_path = research_dir / "FINAL_RESEARCH_REPORT.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(final_report)
        
        # Also save as HTML using mistune if available
        html_path = None
        if HTML_AVAILABLE:
            try:
                markdown_parser = mistune.create_markdown(
                    plugins=['strikethrough', 'footnotes', 'table', 'url']
                )
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Research Report: {research_plan['research_overview']['topic']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        h1 {{ border-bottom: 2px solid #333; padding-bottom: 10px; }}
        h2 {{ border-bottom: 1px solid #666; padding-bottom: 5px; margin-top: 30px; }}
        pre {{ background: #f4f4f4; padding: 10px; overflow-x: auto; }}
        blockquote {{ border-left: 4px solid #ccc; margin-left: 0; padding-left: 20px; color: #666; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
    </style>
</head>
<body>
{markdown_parser(final_report)}
</body>
</html>
"""
                html_path = research_dir / "FINAL_RESEARCH_REPORT.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info("Generated HTML report")
            except Exception as e:
                logger.warning(f"Failed to generate HTML: {e}")
        
        return {
            "report_path": str(report_path),
            "html_path": str(html_path) if html_path else None,
            "research_dir": str(research_dir),
            "total_documents": len(plan_results) * 3 + 2,  # subplans + summaries + final
            "topic": research_plan['research_overview']['topic']
        }
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["final_report_info"] = exec_res
        return "prepare_response"


class ResponsePreparationNode(AsyncNode):
    """Prepares final ResearchResponse"""
    
    async def prep_async(self, shared):
        return {
            "research_plan": shared["research_plan"],
            "plan_results": shared["plan_results"],
            "report_info": shared["final_report_info"]
        }
    
    async def exec_async(self, context):
        """Prepare structured ResearchResponse"""
        research_plan = context["research_plan"]
        plan_results = context["plan_results"]
        report_info = context["report_info"]
        
        # Extract key findings
        key_findings = [
            f"Comprehensive research completed with {len(plan_results)} major research areas",
            f"Generated {report_info['total_documents']} research documents",
            f"Research saved to: {report_info['research_dir']}"
        ]
        
        if report_info.get('html_path'):
            key_findings.append(f"HTML report available: {report_info['html_path']}")
        
        # Build sections
        sections = []
        for plan_result in plan_results:
            sections.append(
                ResearchSection(
                    title=plan_result["title"],
                    content=f"Research completed for {plan_result['title']}. See detailed findings in plan summary and individual subplan documents.",
                    sources=[f"{plan_result['plan_id']}/plan_summary.md"],
                    confidence_level="high"
                )
            )
        
        # Sources used
        sources_used = [
            f"Generated {report_info['total_documents']} research documents",
            f"Main report: {report_info['report_path']}"
        ]
        
        # Recommendations
        recommendations = [
            f"Review the comprehensive report at: {report_info['report_path']}",
            "Examine individual research documents for detailed findings",
            "Research documents are organized by topic and accessible via the main report"
        ]
        
        if report_info.get('html_path'):
            recommendations.append(f"Use the HTML version for better readability: {report_info['html_path']}")
        
        return {
            "research_topic": research_plan["research_overview"]["topic"],
            "executive_summary": f"Comprehensive research on '{research_plan['research_overview']['topic']}' completed successfully. Generated detailed research documents covering {len(plan_results)} major areas. Full report available at: {report_info['report_path']}",
            "sections": sections,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "sources_used": sources_used,
            "research_depth": "comprehensive"
        }
    
async def post_async(self, shared, prep_res, exec_res):
        try:
            emit_progress(shared, "Report generated; preparing response")
            emit_plan(shared, [
                {"step": "Plan research", "status": "completed"},
                {"step": "Setup tools", "status": "completed"},
                {"step": "Execute subplans", "status": "completed"},
                {"step": "Generate report", "status": "completed"},
                {"step": "Prepare response", "status": "in_progress"},
            ])
        except Exception:
            pass
        shared["response_data"] = exec_res
        return None


class EnhancedDeepResearchAgent(PocketFlowAgent):
    """Enhanced deep research agent with document generation"""
    
    def __init__(self):
        self.name = "Enhanced Deep Research Agent"
        self.output_type = ResearchResponse
        self.model = "gpt-4.1-nano-2025-04-14"
        
        # Create custom flow
        self.flow = self._create_research_flow()
        
        logger.info("Initialized Enhanced Deep Research Agent")
    
    def _create_research_flow(self):
        """Create the research flow"""
        # Create nodes
        planning = ResearchPlanningNode()
        setup_tools = ResearchToolSetupNode()
        execute_subplans = SubplanExecutionNode()
        generate_report = FinalReportGenerationNode()
        prepare_response = ResponsePreparationNode()
        
        # Connect nodes
        planning - "setup_research_tools" >> setup_tools
        setup_tools - "execute_subplans" >> execute_subplans
        execute_subplans - "generate_final_report" >> generate_report
        generate_report - "prepare_response" >> prepare_response
        
        # Create async flow
        return AsyncFlow(start=planning)
    
    async def process(self, request: AIAgentRequest) -> ResearchResponse:
        """Process research request"""
        request_id = request.request_id or str(uuid.uuid4())
        topic = request.context.get('topic', 'research topic')
        
        try:
            logger.info(f"Enhanced deep research starting for topic: {topic}")
            
            # Run research flow
            shared = {
                "request": request,
                "request_id": request_id
            }
            
            await self.flow.run_async(shared)
            
            # Get response data
            response_data = shared.get("response_data", {})
            
            logger.info(f"Enhanced research completed: {response_data.get('research_topic', topic)}")
            
            # Convert to ResearchResponse
            return ResearchResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Enhanced research failed: {e}")
            # Fallback response
            return ResearchResponse(
                research_topic=topic,
                executive_summary=f"Research on '{topic}' encountered an error: {str(e)}",
                sections=[],
                key_findings=[f"Error occurred: {str(e)}"],
                recommendations=["Please try again with a different topic or check system logs"],
                sources_used=["Error fallback"],
                research_depth="limited"
            )
    
    def get_agent_info(self):
        """Get agent information"""
        return {
            "name": self.name,
            "type": "enhanced_deep_research",
            "capabilities": [
                "comprehensive_research",
                "document_generation", 
                "multi_plan_execution",
                "markdown_reports",
                "html_export",
                "filesystem_storage",
                "research_planning"
            ],
            "output_formats": ["markdown", "html", "yaml"],
            "requires_api_key": False,
            "framework": "PocketFlow + AsyncFlow"
        }


def create_enhanced_deep_research_agent() -> EnhancedDeepResearchAgent:
    """Factory function to create enhanced deep research agent"""
    return EnhancedDeepResearchAgent()
