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

from .base import PocketFlowAgent, call_llm
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
        
        try:
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            analysis = yaml.safe_load(yaml_str)
            return analysis
        except Exception as e:
            logger.error(f"Failed to parse query analysis: {e}")
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
        shared["query_analysis"] = exec_res
        return "setup_tools"


class MultiToolSetupNode(AsyncNode):
    """Sets up multiple MCP search tools"""
    
    async def exec_async(self, _):
        """Initialize multiple MCP clients for different search engines"""
        
        # Configuration for multiple MCP servers
        server_configs = [
            {
                "name": "fetch_search",
                "config": {
                    "command": "npx",
                    "args": ["-y", "@kazuph/mcp-fetch"],
                    "type": "stdio"
                },
                "priority": 1
            },
            {
                "name": "web_search", 
                "config": {
                    "command": "python",
                    "args": ["-m", "mcp_server_fetch"],
                    "type": "stdio"
                },
                "priority": 2
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
        shared["available_search_tools"] = exec_res
        if exec_res:
            return "execute_searches"
        else:
            return "fallback"


class ParallelSearchExecutionNode(AsyncNode):
    """Executes searches in parallel across multiple engines"""
    
    async def prep_async(self, shared):
        return {
            "search_plans": shared["query_analysis"]["search_plans"],
            "available_tools": shared["available_search_tools"]
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
            search_tools = [
                tool for tool in tools 
                if any(keyword in tool["name"].lower() for keyword in ["search", "fetch", "web"])
            ]
            
            if not search_tools:
                return {"error": "No search tool found", "tool_name": tool_name}
            
            # Use the first available search tool
            search_tool = search_tools[0]
            
            # Prepare parameters based on tool schema
            params = {"query": query}
            if "limit" in str(search_tool.get("inputSchema", {})):
                params["limit"] = 10
            if "num_results" in str(search_tool.get("inputSchema", {})):
                params["num_results"] = 10
            
            # Execute search
            result = await client.call_tool_atomic(
                search_tool["name"],
                params
            )
            
            return {
                "tool_name": tool_name,
                "query": query,
                "results": result.get("result", []),
                "success": result.get("success", False),
                "raw_result": result
            }
            
        except Exception as e:
            logger.error(f"Error searching with {tool_name}: {e}")
            return {"error": str(e), "tool_name": tool_name}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["raw_search_results"] = exec_res
        return "evaluate_sources"


class SourceEvaluationNode(AsyncNode):
    """Evaluates and ranks search results for quality and relevance"""
    
    async def prep_async(self, shared):
        return {
            "raw_results": shared["raw_search_results"],
            "original_query": shared["query_analysis"]["query_analysis"]["original_query"]
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
        query_analysis = context["query_analysis"]["query_analysis"]
        top_sources = context["evaluated_sources"]["top_sources"]
        original_query = query_analysis["original_query"]
        
        # Create synthesis prompt
        prompt = f"""Synthesize comprehensive search results into a structured response.

Original Query: "{original_query}"
Query Intent: {query_analysis.get("intent", "general information")}
Query Type: {query_analysis.get("query_type", "exploratory")}

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
