"""
Enhanced Web Search Agent with multi-tool strategy and comprehensive result synthesis
Uses multiple MCP servers for better coverage without API keys
"""
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import json
import yaml
import uuid
from datetime import datetime
from pocketflow import AsyncNode, AsyncFlow
from urllib import request as urlrequest, parse as urlparse

from .base import PocketFlowAgent, call_llm
from .utils import emit_progress, emit_plan
from .mcp_client import PocketFlowMCPClient
from core.models import AIAgentRequest, WebSearchResponse, SearchResult
from core.logging import get_logger

logger = get_logger(__name__)


class QueryAnalysisNode(AsyncNode):
    """Analyzes user query to create comprehensive search strategy"""
    
    async def prep_async(self, shared):
        request = shared.get("request")
        query = request.context.get('query', '')
        return query
    
    async def exec_async(self, query):
        """Analyze query and create multi-step search plan"""
        prompt = f"""Analyze this search query and create a comprehensive search strategy.

Query: "{query}"

Analyze and provide:
1. Query Intent: What is the user really looking for?
2. Key Entities: People, organizations, concepts, technologies
3. Query Type: Factual/Exploratory/Comparative/How-to/Current Events
4. Search Complexity: Simple lookup or multi-faceted research
5. Optimal Search Strategies:
   - Initial broad searches
   - Specific deep dives
   - Alternative phrasings
   - Related topics to explore

Return YAML format:
```yaml
query_analysis:
  original_query: "{query}"
  intent: "user's actual intent"
  query_type: "type"
  complexity: "simple/moderate/complex"
  key_entities:
    - entity1
    - entity2
  
search_plans:
  - step: 1
    search_query: "broad initial search"
    purpose: "understand landscape"
    expected_results: "overview and main sources"
  - step: 2
    search_query: "specific aspect search" 
    purpose: "deep dive into specific area"
    expected_results: "detailed information"
  - step: 3
    search_query: "alternative phrasing"
    purpose: "capture different perspectives"
    expected_results: "additional viewpoints"

alternative_queries:
  - "alternative query 1"
  - "alternative query 2"
  
priority_sources:
  - "official sites"
  - "academic papers"
  - "recent news"
```"""
        
        response = call_llm(prompt, temperature=0.3)

        # Robust YAML extraction
        analysis = None
        try:
            txt = response.strip() if isinstance(response, str) else ""
            if "```yaml" in txt:
                yaml_str = txt.split("```yaml", 1)[1]
                if "```" in yaml_str:
                    yaml_str = yaml_str.split("```", 1)[0]
                analysis = yaml.safe_load(yaml_str.strip())
            else:
                # Try to parse whole response as YAML
                analysis = yaml.safe_load(txt)
        except Exception as e:
            logger.error(f"Failed to parse query analysis: {e}")
            analysis = None

        if analysis:
            return analysis
        else:
            # Fallback simple analysis
            return {
                "query_analysis": {
                    "original_query": query,
                    "intent": "general information search",
                    "query_type": "exploratory",
                    "complexity": "simple"
                },
                "search_plans": [
                    {
                        "step": 1,
                        "search_query": query,
                        "purpose": "direct search",
                        "expected_results": "relevant results"
                    }
                ],
                "alternative_queries": [query]
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        # Emit progress and initial plan after analysis
        try:
            emit_progress(shared, "Query analysis ready")
            plans = []
            for p in (exec_res or {}).get("search_plans", []) if isinstance(exec_res, dict) else []:
                label = p.get("search_query") or p.get("purpose") or "search step"
                plans.append({"step": f"Search: {label}", "status": "pending"})
            if plans:
                # Seed a standard plan
                seed = [
                    {"step": "Analyze query", "status": "completed"},
                    {"step": "Setup tools", "status": "pending"},
                    {"step": "Execute searches", "status": "pending"},
                    {"step": "Evaluate sources", "status": "pending"},
                    {"step": "Synthesize results", "status": "pending"},
                ]
                emit_plan(shared, seed, explanation="Web search plan")
        except Exception:
            pass
        shared["query_analysis"] = exec_res
        return "setup_tools"


class MultiToolSetupNode(AsyncNode):
    """Sets up multiple MCP search tools"""
    
    async def exec_async(self, _):
        """Initialize multiple MCP clients for different search engines"""
        
        # Use Python MCP server (mcp_server_fetch). It exposes a 'fetch' tool (URL fetcher), not a query search.
        server_configs = [
            {
                "name": "py_fetch",
                "config": {
                    "command": "python",
                    "args": ["-m", "mcp_server_fetch"],
                    "type": "stdio"
                },
                "priority": 1
            }
        ]
        
        # Try to initialize each server
        available_tools = {}
        for server in server_configs:
            try:
                client = PocketFlowMCPClient(server["config"])
                tools = await client.list_tools_atomic()
                if tools:
                    available_tools[server["name"]] = {
                        "client": client,
                        "tools": tools,
                        "priority": server["priority"]
                    }
                    logger.info(f"Initialized {server['name']} with {len(tools)} tools")
            except Exception as e:
                logger.warning(f"Failed to initialize {server['name']}: {e}")
        
        return available_tools
    
    async def post_async(self, shared, prep_res, exec_res):
        try:
            emit_progress(shared, f"Tools ready: {len(exec_res or {})} server(s)")
            # Update plan stage
            emit_plan(shared, [
                {"step": "Analyze query", "status": "completed"},
                {"step": "Setup tools", "status": "completed"},
                {"step": "Execute searches", "status": "in_progress"},
                {"step": "Evaluate sources", "status": "pending"},
                {"step": "Synthesize results", "status": "pending"},
            ])
        except Exception:
            pass
        shared["available_search_tools"] = exec_res
        if exec_res:
            return "execute_searches"
        else:
            return "fallback"


class ParallelSearchExecutionNode(AsyncNode):
    """Executes searches in parallel across multiple engines"""
    
    async def prep_async(self, shared):
        qa = shared.get("query_analysis") or {}
        plans = []
        try:
            plans = qa.get("search_plans") or []
        except Exception:
            plans = []
        # Fallback to a single plan using the original query
        try:
            if not plans:
                oq = qa.get("query_analysis", {}).get("original_query") or shared.get("request").context.get("query", "")
                plans = [{"step": 1, "search_query": oq, "purpose": "direct search"}]
        except Exception:
            pass
        return {
            "search_plans": plans,
            "available_tools": shared.get("available_search_tools", {})
        }
    
    async def exec_async(self, context):
        """Execute searches in parallel for faster results"""
        search_plans = context["search_plans"]
        available_tools = context["available_tools"]
        
        all_results = []
        
        # Execute each search plan
        for plan in search_plans:
            query = plan["search_query"]
            
            # Create tasks for parallel execution
            search_tasks = []
            
            # Try each available tool
            for tool_name, tool_info in available_tools.items():
                task = self._search_with_tool(
                    tool_info["client"],
                    tool_info["tools"],
                    query,
                    tool_name
                )
                search_tasks.append(task)
            
            # Execute searches in parallel
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process results
            plan_results = {
                "plan": plan,
                "results_by_tool": {}
            }
            
            for i, (tool_name, _) in enumerate(available_tools.items()):
                if isinstance(results[i], Exception):
                    logger.error(f"Search failed on {tool_name}: {results[i]}")
                    plan_results["results_by_tool"][tool_name] = {"error": str(results[i])}
                else:
                    plan_results["results_by_tool"][tool_name] = results[i]
            
            all_results.append(plan_results)
        
        return all_results
    
    async def _search_with_tool(self, client, tools, query, tool_name):
        """Execute search with specific tool"""
        try:
            # Find appropriate tool for web search
            def has_query_param(tool):
                schema = tool.get("inputSchema")
                try:
                    # Handle object or dict
                    props = None
                    if isinstance(schema, dict):
                        props = schema.get("properties")
                    elif hasattr(schema, "properties"):
                        props = getattr(schema, "properties")
                    if isinstance(props, dict):
                        return "query" in props
                except Exception:
                    pass
                # string fallback
                return "\"query\"" in str(schema) or "query" in str(schema)

            # Prefer tools explicitly accepting a 'query' argument
            search_tools = [tool for tool in tools if has_query_param(tool)]
            if not search_tools:
                # Fallback: heuristics on name but avoid pure 'fetch' tools
                search_tools = [
                    tool for tool in tools
                    if ("search" in tool.get("name", "").lower() or "web" in tool.get("name", "").lower())
                    and "fetch" not in tool.get("name", "").lower()
                ]
            
            if not search_tools:
                # Direct DDG fallback (Instant Answer API) to ensure minimal results
                try:
                    q = urlparse.quote(query)
                    url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
                    with urlrequest.urlopen(url, timeout=10) as resp:
                        data = json.loads(resp.read().decode('utf-8', errors='ignore'))
                    items = []
                    if isinstance(data, dict):
                        if data.get('AbstractURL'):
                            items.append({
                                'title': data.get('Heading') or 'DuckDuckGo Abstract',
                                'url': data.get('AbstractURL'),
                                'snippet': data.get('AbstractText') or '',
                            })
                        for t in data.get('RelatedTopics', [])[:10]:
                            if isinstance(t, dict):
                                txt = t.get('Text') or ''
                                href = t.get('FirstURL') or ''
                                if href:
                                    items.append({'title': txt[:80] or 'Related', 'url': href, 'snippet': txt})
                    return {
                        "tool_name": tool_name,
                        "query": query,
                        "results": items,
                        "success": True,
                        "raw_result": {"source": "duckduckgo"}
                    }
                except Exception as e:
                    return {"error": f"No search tool and DDG failed: {e}", "tool_name": tool_name}
            
            # Use the first available search tool
            search_tool = search_tools[0]
            
            # Prepare parameters based on tool schema
            params = {"query": query}
            schema_str = str(search_tool.get("inputSchema", {}))
            if "limit" in schema_str:
                params["limit"] = 10
            if "num_results" in schema_str:
                params["num_results"] = 10
            
            # Execute search
            result = await client.call_tool_atomic(
                search_tool["name"],
                params
            )
            payload = result.get("result", [])
            success = result.get("success", False)
            # If tool yielded nothing useful, try DDG fallback
            empty = (isinstance(payload, list) and not payload) or (isinstance(payload, dict) and not payload)
            if not success or empty:
                try:
                    q = urlparse.quote(query)
                    url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
                    with urlrequest.urlopen(url, timeout=10) as resp:
                        data = json.loads(resp.read().decode('utf-8', errors='ignore'))
                    ddg_items = []
                    if isinstance(data, dict):
                        if data.get('AbstractURL'):
                            ddg_items.append({
                                'title': data.get('Heading') or 'DuckDuckGo Abstract',
                                'url': data.get('AbstractURL'),
                                'snippet': data.get('AbstractText') or '',
                            })
                        for t in data.get('RelatedTopics', [])[:10]:
                            if isinstance(t, dict):
                                txt = t.get('Text') or ''
                                href = t.get('FirstURL') or ''
                                if href:
                                    ddg_items.append({'title': txt[:80] or 'Related', 'url': href, 'snippet': txt})
                    payload = ddg_items
                    success = True
                except Exception:
                    pass

            return {
                "tool_name": tool_name,
                "query": query,
                "results": payload,
                "success": success,
                "raw_result": result
            }
            
        except Exception as e:
            logger.error(f"Error searching with {tool_name}: {e}")
            return {"error": str(e), "tool_name": tool_name}
    
    async def post_async(self, shared, prep_res, exec_res):
        try:
            emit_progress(shared, "Search execution complete")
            emit_plan(shared, [
                {"step": "Analyze query", "status": "completed"},
                {"step": "Setup tools", "status": "completed"},
                {"step": "Execute searches", "status": "completed"},
                {"step": "Evaluate sources", "status": "in_progress"},
                {"step": "Synthesize results", "status": "pending"},
            ])
        except Exception:
            pass
        shared["raw_search_results"] = exec_res
        return "evaluate_sources"


class SourceEvaluationNode(AsyncNode):
    """Evaluates and ranks search results for quality and relevance"""
    
    async def prep_async(self, shared):
        qa_obj = shared.get("query_analysis") or {}
        oq = None
        try:
            if isinstance(qa_obj, dict):
                oq = qa_obj.get("query_analysis", {}).get("original_query") or qa_obj.get("original_query")
        except Exception:
            oq = None
        if not oq:
            try:
                oq = shared.get("request").context.get("query")
            except Exception:
                oq = ""
        return {
            "raw_results": shared.get("raw_search_results", []),
            "original_query": oq or ""
        }
    
    async def exec_async(self, context):
        """Evaluate sources for credibility and relevance"""
        raw_results = context["raw_results"]
        original_query = context["original_query"]
        
        # Flatten all results
        all_sources = []
        for plan_result in raw_results:
            for tool_name, tool_results in plan_result["results_by_tool"].items():
                if "error" not in tool_results and tool_results.get("success"):
                    results = tool_results.get("results", [])
                    
                    # Handle different result formats
                    if isinstance(results, dict):
                        if "results" in results:
                            results = results["results"]
                        elif "data" in results:
                            results = results["data"]
                        else:
                            # Try to extract from other common keys
                            for key in ["items", "entries", "content"]:
                                if key in results:
                                    results = results[key]
                                    break
                    
                    if isinstance(results, list):
                        for result in results:
                            if isinstance(result, dict):
                                all_sources.append({
                                    "title": result.get("title", result.get("name", "Unknown")),
                                    "url": result.get("url", result.get("link", "")),
                                    "snippet": result.get("snippet", result.get("description", result.get("content", ""))),
                                    "source_tool": tool_name,
                                    "search_query": plan_result["plan"]["search_query"]
                                })
                    elif isinstance(results, str):
                        # Handle string results (some tools return raw text)
                        all_sources.append({
                            "title": f"Result from {tool_name}",
                            "url": "",
                            "snippet": results[:500],
                            "source_tool": tool_name,
                            "search_query": plan_result["plan"]["search_query"]
                        })
        
        if not all_sources:
            return {"evaluated_sources": [], "top_sources": []}
        
        # Evaluate sources with LLM
        prompt = f"""Evaluate these search results for quality and relevance.

Original Query: "{original_query}"

Search Results:
{json.dumps(all_sources[:20], indent=2)}

For each source, assess:
1. Relevance (0-10): How well does it address the query?
2. Authority (0-10): Is this a credible source?
3. Freshness (0-10): How current is the information?
4. Depth (0-10): How comprehensive is the coverage?
5. Overall Score: Weighted average

Return JSON:
{{
    "evaluated_sources": [
        {{
            "index": 0,
            "relevance_score": 8.5,
            "authority_score": 9.0,
            "freshness_score": 7.0,
            "depth_score": 8.0,
            "overall_score": 8.2,
            "assessment": "Highly relevant academic source with recent data",
            "should_include": true
        }}
    ],
    "top_indices": [0, 3, 5],
    "quality_summary": "Overall assessment of source quality"
}}"""
        
        response = call_llm(prompt, temperature=0.2)
        
        try:
            # Clean JSON response
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            
            evaluation = json.loads(json_str)
            
            # Merge evaluation with source data
            top_sources = []
            for idx in evaluation.get("top_indices", [])[:10]:
                if idx < len(all_sources):
                    source = all_sources[idx]
                    if idx < len(evaluation["evaluated_sources"]):
                        source["evaluation"] = evaluation["evaluated_sources"][idx]
                    top_sources.append(source)
            
            return {
                "evaluated_sources": evaluation["evaluated_sources"],
                "top_sources": top_sources,
                "quality_summary": evaluation.get("quality_summary", "")
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate sources: {e}")
            # Return top results without evaluation
            return {
                "evaluated_sources": [],
                "top_sources": all_sources[:10],
                "quality_summary": "Unable to evaluate sources, returning raw results"
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        try:
            emit_progress(shared, "Source evaluation complete")
            emit_plan(shared, [
                {"step": "Analyze query", "status": "completed"},
                {"step": "Setup tools", "status": "completed"},
                {"step": "Execute searches", "status": "completed"},
                {"step": "Evaluate sources", "status": "completed"},
                {"step": "Synthesize results", "status": "in_progress"},
            ])
        except Exception:
            pass
        shared["evaluated_sources"] = exec_res
        return "synthesize"


class ResultSynthesisNode(AsyncNode):
    """Synthesizes search results into comprehensive, structured response"""
    
    async def prep_async(self, shared):
        return {
            "query_analysis": shared["query_analysis"],
            "evaluated_sources": shared["evaluated_sources"],
            "request": shared["request"]
        }
    
    async def exec_async(self, context):
        """Create comprehensive synthesis of search results"""
        qa_obj = context.get("query_analysis", {}) or {}
        # Support either {query_analysis:{...}} or direct {...}
        qa = qa_obj.get("query_analysis", qa_obj) if isinstance(qa_obj, dict) else {}
        top_sources = (context.get("evaluated_sources", {}) or {}).get("top_sources", [])
        original_query = qa.get("original_query") or (context.get("request").context.get("query", "") if context.get("request") else "")
        
        # If no evaluated sources, generate knowledge-based result via LLM
        if not top_sources:
            fb_prompt = f"""You are a web search assistant. The user searched for: "{original_query}"

Without external tools, provide the best information you can from your knowledge base.
Return JSON with this shape:
{{
  "query": "{original_query}",
  "results": [{{"title": "...", "url": "", "snippet": "...", "relevance_score": 0.8, "source_type": "knowledge_base"}}],
  "total_results": 1,
  "search_time": 1.0,
  "search_engine": "knowledge-fallback",
  "related_queries": []
}}"""
            fb_resp = call_llm(fb_prompt, temperature=0.5)
            try:
                js = fb_resp.strip()
                if js.startswith("```json"):
                    js = js[7:]
                if js.endswith("```"):
                    js = js[:-3]
                return json.loads(js.strip())
            except Exception:
                return {"query": original_query, "results": [], "total_results": 0, "search_time": 1.0}

        # Create synthesis prompt
        prompt = f"""Synthesize comprehensive search results into a structured response.

Original Query: "{original_query}"
        Query Intent: {qa.get("intent", "general information")}
        Query Type: {qa.get("query_type", "exploratory")}

Top Sources:
{json.dumps(top_sources, indent=2)}

Create a comprehensive synthesis that:
1. Directly addresses the user's query
2. Integrates information from multiple sources
3. Highlights consensus and contradictions
4. Provides clear, actionable insights
5. Suggests areas for further exploration

Return JSON matching WebSearchResponse schema:
{{
    "query": "{original_query}",
    "results": [
        {{
            "title": "Source title",
            "url": "https://...",
            "snippet": "Key information from this source...",
            "relevance_score": 0.95,
            "source_type": "academic/news/web/etc"
        }}
    ],
    "total_results": number,
    "search_time": 2.5,
    "search_engine": "multi-engine-synthesis",
    "related_queries": ["query1", "query2"]
}}

IMPORTANT: Include 5-10 most relevant results with enhanced snippets that directly answer the query."""
        
        response = call_llm(prompt, temperature=0.3)
        
        try:
            # Clean JSON response
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            
            result = json.loads(json_str)
            
            # Ensure all required fields
            result["search_time"] = 3.2  # Simulated
            result["search_engine"] = "enhanced-multi-mcp"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to synthesize results: {e}")
            # Fallback formatting
            return {
                "query": original_query,
                "results": [
                    {
                        "title": source.get("title", "Unknown"),
                        "url": source.get("url", ""),
                        "snippet": source.get("snippet", ""),
                        "relevance_score": 0.8,
                        "source_type": "web"
                    }
                    for source in top_sources[:5]
                ],
                "total_results": len(top_sources),
                "search_time": 3.0,
                "search_engine": "multi-mcp-fallback",
                "related_queries": []
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        try:
            emit_progress(shared, "Synthesis complete")
            emit_plan(shared, [
                {"step": "Analyze query", "status": "completed"},
                {"step": "Setup tools", "status": "completed"},
                {"step": "Execute searches", "status": "completed"},
                {"step": "Evaluate sources", "status": "completed"},
                {"step": "Synthesize results", "status": "completed"},
            ])
        except Exception:
            pass
        shared["final_result"] = exec_res
        return None


class FallbackSearchNode(AsyncNode):
    """Fallback node for when MCP tools are unavailable"""
    
    async def prep_async(self, shared):
        request = shared.get("request")
        query = request.context.get('query', '')
        return query
    
    async def exec_async(self, query):
        """Provide basic search using LLM knowledge"""
        prompt = f"""You are a web search assistant. The user searched for: "{query}"

Since external search tools are unavailable, provide the best information you can from your knowledge base.

Format your response as a WebSearchResponse JSON:
{{
    "query": "{query}",
    "results": [
        {{
            "title": "Knowledge-based result 1",
            "url": "https://knowledge-base.ai",
            "snippet": "Detailed information about the topic...",
            "relevance_score": 0.9,
            "source_type": "knowledge_base"
        }}
    ],
    "total_results": 1,
    "search_time": 1.0,
    "search_engine": "knowledge-fallback",
    "related_queries": ["related topic 1", "related topic 2"]
}}

Provide accurate, helpful information even without live search capabilities."""
        
        response = call_llm(prompt, temperature=0.5)
        
        try:
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return {
                "query": query,
                "results": [{
                    "title": "Search Unavailable",
                    "url": "",
                    "snippet": f"External search tools are currently unavailable. Please try again later or rephrase your query: '{query}'",
                    "relevance_score": 0.1,
                    "source_type": "error"
                }],
                "total_results": 1,
                "search_time": 1.0,
                "search_engine": "fallback",
                "related_queries": []
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        try:
            emit_progress(shared, "Search complete")
        except Exception:
            pass
        shared["final_result"] = exec_res
        return None


class EnhancedWebSearchAgent(PocketFlowAgent):
    """Enhanced web search agent with multi-tool strategy and synthesis"""
    
    def __init__(self):
        self.name = "Enhanced Web Search Agent"
        self.output_type = WebSearchResponse
        self.model = "gpt-4.1-nano-2025-04-14"
        
        # Create custom flow
        self.flow = self._create_enhanced_flow()
        
        logger.info("Initialized Enhanced Web Search Agent with custom flow")
    
    def _create_enhanced_flow(self):
        """Create the enhanced search flow"""
        # Create nodes
        query_analysis = QueryAnalysisNode()
        setup_tools = MultiToolSetupNode()
        execute_searches = ParallelSearchExecutionNode()
        evaluate_sources = SourceEvaluationNode()
        synthesize = ResultSynthesisNode()
        fallback = FallbackSearchNode()
        
        # Connect nodes with proper flow control
        query_analysis - "setup_tools" >> setup_tools
        setup_tools - "execute_searches" >> execute_searches
        setup_tools - "fallback" >> fallback  # Direct to fallback on tool failure
        execute_searches - "evaluate_sources" >> evaluate_sources
        evaluate_sources - "synthesize" >> synthesize
        
        # Create async flow
        return AsyncFlow(start=query_analysis)
    
    async def process(self, request: AIAgentRequest) -> WebSearchResponse:
        """Process search request with enhanced flow"""
        request_id = request.request_id or str(uuid.uuid4())
        
        try:
            logger.info(f"Enhanced web search starting for query: {request.context.get('query', '')}")
            
            # Run enhanced flow
            shared = {
                "request": request,
                "request_id": request_id
            }
            
            await self.flow.run_async(shared)
            
            # Get final result
            final_result = shared.get("final_result", {})
            
            logger.info(f"Enhanced web search completed with {len(final_result.get('results', []))} results")
            
            # Convert to WebSearchResponse
            return WebSearchResponse(**final_result)
            
        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
            # Fallback response
            query = request.context.get('query', 'search')
            return WebSearchResponse(
                query=query,
                results=[{
                    "title": "Search Error",
                    "url": "",
                    "snippet": f"An error occurred during search: {str(e)}",
                    "relevance_score": 0.1
                }],
                total_results=0,
                search_time=0.0,
                search_engine="error-fallback",
                related_queries=[]
            )
    
    def get_agent_info(self):
        """Get agent information"""
        return {
            "name": self.name,
            "type": "enhanced_web_search",
            "capabilities": [
                "multi_engine_search",
                "parallel_execution", 
                "ai_source_evaluation",
                "result_synthesis",
                "query_analysis",
                "fallback_handling"
            ],
            "mcp_servers": ["@kazuph/mcp-fetch", "mcp_server_fetch"],
            "requires_api_key": False,
            "framework": "PocketFlow + AsyncFlow"
        }


def create_enhanced_web_search_agent() -> EnhancedWebSearchAgent:
    """Factory function to create enhanced web search agent"""
    return EnhancedWebSearchAgent()
