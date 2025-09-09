"""
Tool Node implementations for Pocket Flow
Handles custom function tools for enhanced agent capabilities using AsyncNode patterns
"""
from typing import Dict, Any, List, Optional, Type, Callable
import json
import inspect
import asyncio
from pocketflow import Node, Flow, AsyncNode, AsyncFlow

from ..core.logging import get_logger
from .base import call_llm

logger = get_logger(__name__)


class AnalyzeToolsNode(AsyncNode):
    """AsyncNode to analyze available tools and their capabilities"""
    
    def __init__(self, tools: List[Callable]):
        super().__init__()
        self.tools = tools
        self.tool_map = {tool.__name__: tool for tool in tools}
    
    async def prep_async(self, shared):
        """Extract tool information"""
        tool_info = []
        for tool in self.tools:
            # Get function signature and docstring
            sig = inspect.signature(tool)
            doc = inspect.getdoc(tool) or "No description available"
            
            # Extract parameters
            params = []
            for param_name, param in sig.parameters.items():
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else "Any"
                params.append({
                    "name": param_name,
                    "type": str(param_type),
                    "required": param.default == inspect.Parameter.empty
                })
            
            tool_info.append({
                "name": tool.__name__,
                "description": doc,
                "parameters": params,
                "is_async": inspect.iscoroutinefunction(tool)
            })
        
        return tool_info
    
    async def exec_async(self, tool_info):
        """Store tool information"""
        return tool_info
    
    async def post_async(self, shared, prep_res, exec_res):
        """Save tool info and continue"""
        shared["tool_info"] = exec_res
        shared["tool_map"] = self.tool_map
        return "decide"


class DecideToolNode(AsyncNode):
    """AsyncNode to decide which tool to use based on request"""
    
    def __init__(self, instructions: str, model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7):
        super().__init__()
        self.instructions = instructions
        self.model = model
        self.temperature = temperature
    
    async def prep_async(self, shared):
        """Prepare context for decision"""
        return {
            "request": shared.get("request"),
            "tool_info": shared.get("tool_info", [])
        }
    
    async def exec_async(self, context):
        """Decide tool usage strategy"""
        request = context["request"]
        tool_info = context["tool_info"]
        
        # Format tool descriptions with async indicators
        tool_descriptions = []
        for tool in tool_info:
            params = ", ".join([f"{p['name']}: {p['type']}" for p in tool["parameters"]])
            async_indicator = " (ASYNC)" if tool.get("is_async", False) else ""
            tool_descriptions.append(f"- {tool['name']}({params}){async_indicator}: {tool['description']}")
        
        prompt = f"""{self.instructions}

Available Tools:
{chr(10).join(tool_descriptions)}

User Request: {request}

Analyze the request and decide which tools to use.
You can use multiple tools in sequence if needed.
Tools marked with (ASYNC) are asynchronous and may take longer to execute.

Return JSON:
{{
    "strategy": "description of approach",
    "tool_calls": [
        {{
            "tool_name": "function_name",
            "arguments": {{"param": "value"}},
            "purpose": "why using this tool"
        }}
    ],
    "use_tools": true/false
}}"""
        
        response = call_llm(prompt, self.model, self.temperature)
        
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3]
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse tool decision: {e}")
            return {"use_tools": False, "tool_calls": []}
    
    async def post_async(self, shared, prep_res, exec_res):
        """Route based on decision"""
        shared["tool_strategy"] = exec_res
        if exec_res.get("use_tools", False) and exec_res.get("tool_calls"):
            return "execute"
        return "answer"


class ExecuteToolsNode(AsyncNode):
    """AsyncNode to execute selected tools with proper async support"""
    
    async def prep_async(self, shared):
        """Prepare tool execution plan"""
        return {
            "tool_calls": shared.get("tool_strategy", {}).get("tool_calls", []),
            "tool_map": shared.get("tool_map", {})
        }
    
    async def exec_async(self, context):
        """Execute tools in sequence with proper async/sync handling"""
        tool_calls = context["tool_calls"]
        tool_map = context["tool_map"]
        results = []
        
        for call in tool_calls:
            tool_name = call.get("tool_name")
            arguments = call.get("arguments", {})
            
            if tool_name not in tool_map:
                results.append({
                    "tool": tool_name,
                    "error": f"Tool {tool_name} not found",
                    "result": None,
                    "success": False
                })
                continue
            
            try:
                # Execute tool with proper async/sync handling
                tool = tool_map[tool_name]
                
                # Handle async and sync tools properly
                if inspect.iscoroutinefunction(tool):
                    logger.info(f"Executing async tool: {tool_name}")
                    result = await tool(**arguments)
                else:
                    logger.info(f"Executing sync tool: {tool_name}")
                    result = tool(**arguments)
                
                results.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"Tool execution failed for {tool_name}: {e}")
                results.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    async def post_async(self, shared, prep_res, exec_res):
        """Save tool results"""
        shared["tool_results"] = exec_res
        return "answer"


class ToolAnswerNode(AsyncNode):
    """AsyncNode to generate final answer based on tool results"""
    
    def __init__(self, instructions: str, output_type: Optional[Type] = None,
                 model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7):
        super().__init__()
        self.instructions = instructions
        self.output_type = output_type
        self.model = model
        self.temperature = temperature
    
    async def prep_async(self, shared):
        """Prepare context for final answer"""
        return {
            "request": shared.get("request"),
            "tool_results": shared.get("tool_results", []),
            "strategy": shared.get("tool_strategy", {})
        }
    
    async def exec_async(self, context):
        """Generate final answer"""
        request = context["request"]
        tool_results = context["tool_results"]
        strategy = context["strategy"]
        
        # Build context from tool results
        if tool_results:
            results_text = []
            for result in tool_results:
                if result.get("success"):
                    results_text.append(f"Tool: {result['tool']}\nResult: {result['result']}")
                else:
                    results_text.append(f"Tool: {result['tool']}\nError: {result.get('error', 'Unknown error')}")
            
            prompt = f"""{self.instructions}

User Request: {request}

Tool Execution Strategy: {strategy.get('strategy', 'Direct execution')}

Tool Results:
{chr(10).join(results_text)}

Generate a comprehensive answer based on the tool results."""
        else:
            prompt = f"""{self.instructions}

User Request: {request}

No tools were used. Generate a comprehensive answer based on your knowledge."""
        
        # Add output format if specified
        if self.output_type:
            schema = self.output_type.model_json_schema()
            prompt += f"""

Return response as JSON matching this schema:
{json.dumps(schema, indent=2)}"""
        
        response = call_llm(prompt, self.model, self.temperature)
        
        # Parse if output type specified
        if self.output_type:
            try:
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:-3]
                json_data = json.loads(response)
                return self.output_type(**json_data)
            except Exception as e:
                logger.error(f"Failed to parse structured output: {e}")
                return response
        
        return response
    
    async def post_async(self, shared, prep_res, exec_res):
        """Save final result"""
        shared["result"] = exec_res
        return None


def create_tool_flow(name: str, instructions: str, tools: List[Callable],
                     model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7,
                     output_type: Optional[Type] = None) -> AsyncFlow:
    """Create an async flow with tool integration"""
    
    # Create async nodes
    analyze = AnalyzeToolsNode(tools)
    decide = DecideToolNode(instructions, model, temperature)
    execute = ExecuteToolsNode()
    answer = ToolAnswerNode(instructions, output_type, model, temperature)
    
    # Connect nodes with proper routing
    analyze - "decide" >> decide
    decide - "execute" >> execute
    decide - "answer" >> answer
    execute - "answer" >> answer
    
    # Create async flow
    return AsyncFlow(start=analyze)
