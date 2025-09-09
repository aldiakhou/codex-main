"""
MCP nodes for PocketFlow agents
Implements correct conditional flow control and proper MCP SDK usage
"""
from pocketflow import Node, Flow, AsyncNode, AsyncFlow
from .mcp_client import PocketFlowMCPClient
from .base import call_llm
import yaml
import json
import os
import sys
import builtins

# When running under MCP stdio server, ensure print() does not write to stdout
if os.environ.get("MCP_STDIO_MODE", "").lower() in ("1", "true", "yes"):
    _original_print = print
    def _safe_print(*args, **kwargs):
        kwargs.setdefault("file", sys.stderr)
        return _original_print(*args, **kwargs)
    builtins.print = _safe_print
from typing import Dict, Any, List, Optional, Type, Union

from ..core.logging import get_logger

logger = get_logger(__name__)

# Removed global tool_list - will use shared dict instead

def extract_query_from_shared(shared) -> str:
    """Helper function to consistently extract query from shared data"""
    request = shared.get("request")
    
    if not request:
        return ""
    
    # Try different ways to get the query based on agent type
    if hasattr(request, 'context') and request.context:
        # Web search agent - look for 'query' key
        if 'query' in request.context:
            return request.context['query']
        # Deep research agent - look for 'topic' key  
        elif 'topic' in request.context:
            return request.context['topic']
        # Live monitoring agent - look for 'monitoring_target' key
        elif 'monitoring_target' in request.context:
            return request.context['monitoring_target']
    
    # Fallback: return empty string
    return ""

class GetToolsNode(AsyncNode):
    """Get MCP tools from server at runtime using AsyncNode"""

    async def prep_async(self, shared):
        # Get MCP config from shared data
        mcp_config = shared.get("mcp_server_config")
        return mcp_config

    async def exec_async(self, mcp_config):
        """Get MCP tools using atomic operation"""
        if not mcp_config:
            return [], None
        
        try:
            # Create client for atomic operation
            mcp_client = PocketFlowMCPClient(mcp_config)
            
            # Get tools atomically (handles full connection lifecycle)
            tools = await mcp_client.list_tools_atomic()
            
            # Return tools and client for potential tool execution
            return tools, mcp_client
            
        except Exception as e:
            print(f"Failed to get MCP tools: {e}")
            return [], None

    async def post_async(self, shared, prep_res, exec_res):
        tools, mcp_client = exec_res
        
        # Store tools and client in shared dict
        shared["available_tools"] = tools
        shared["mcp_client"] = mcp_client
        
        if tools:
            print(f"Found {len(tools)} MCP tools: {[t['name'] for t in tools]}")
            return "decide"  # SUCCESS: go to decide node
        else:
            print("No MCP tools available")
            return "fallback" # FAILURE: go to fallback


class DecideToolNode(AsyncNode):
    """LLM decides which MCP tool to use and with what parameters"""

    async def prep_async(self, shared):
        tools = shared["available_tools"]
        query = extract_query_from_shared(shared)
        return tools, query

    async def exec_async(self, inputs):
        """LLM chooses best tool and parameters"""
        tools, query = inputs

        # Format tools for LLM
        tools_desc = []
        for tool in tools:
            schema = tool.get("inputSchema", {})
            props = schema.get("properties", {})
            required = schema.get("required", [])

            params_desc = []
            for param_name, param_info in props.items():
                param_type = param_info.get("type", "unknown")
                is_required = "(required)" if param_name in required else "(optional)"
                params_desc.append(f"  - {param_name}: {param_type} {is_required}")

            tool_desc = f"- {tool['name']}: {tool.get('description', 'No description')}"
            if params_desc:
                tool_desc += "\n" + "\n".join(params_desc)

            tools_desc.append(tool_desc)

        prompt = f"""You are a web search agent. Choose the best MCP tool for this query.

Available Tools:
{chr(10).join(tools_desc)}

User Query: "{query}"

Analyze the query and choose the most appropriate tool. Return YAML format:

```yaml
tool_name: <exact_tool_name>
arguments:
  <param_name>: <param_value>
reasoning: <why you chose this tool and these parameters>
```

Make sure to use exact tool names and provide all required parameters."""

        response = call_llm(prompt)

        try:
            # Parse YAML response
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            decision = yaml.safe_load(yaml_str)

            # Validate decision
            tool_name = decision.get("tool_name")
            if not tool_name:
                raise ValueError("No tool_name in decision")

            # Check if tool exists
            available_tool_names = [t["name"] for t in tools]
            if tool_name not in available_tool_names:
                raise ValueError(f"Tool {tool_name} not in available tools: {available_tool_names}")

            return decision

        except Exception as e:
            print(f"❌ Failed to parse tool decision: {e}")
            print(f"LLM Response: {response}")
            return {
                "tool_name": "fallback",
                "arguments": {},
                "reasoning": f"Failed to parse decision: {str(e)}"
            }

    async def post_async(self, shared, prep_res, exec_res):
        shared["selected_tool"] = exec_res
        tool_name = exec_res.get("tool_name", "fallback")

        if tool_name != "fallback":
            print(f"Selected tool: {tool_name}")
            print(f"Arguments: {exec_res.get('arguments', {})}")
            return "execute"  # SUCCESS: execute the tool
        else:
            print("Falling back to direct search")
            return "fallback"  # FAILURE: go to fallback


class ExecuteToolNode(AsyncNode):
    """Execute the selected MCP tool"""

    async def prep_async(self, shared):
        return shared["selected_tool"], shared.get("mcp_client")

    async def exec_async(self, inputs):
        """Execute MCP tool with provided arguments using atomic operation"""
        tool_info, mcp_client = inputs
        tool_name = tool_info["tool_name"]
        arguments = tool_info["arguments"]

        print(f"Executing MCP tool: {tool_name}")
        print(f"Arguments: {json.dumps(arguments, indent=2)}")

        if not mcp_client:
            return {
                "error": "No MCP client available",
                "success": False
            }

        try:
            # Execute tool atomically (handles full connection lifecycle)
            result = await mcp_client.call_tool_atomic(tool_name, arguments)
            return result
            
        except Exception as e:
            print(f"Tool execution failed: {e}")
            return {
                "error": str(e),
                "success": False
            }

    async def post_async(self, shared, prep_res, exec_res):
        shared["tool_result"] = exec_res

        if exec_res.get("success", False):
            print("MCP tool executed successfully")
            return "default"  # SUCCESS: continue (using >> operator)
        else:
            error = exec_res.get("error", "Unknown error")
            print(f"MCP tool execution failed: {error}")
            return "fallback"  # FAILURE: go to fallback


class FormatResultNode(Node):
    """Format the final result from MCP tool execution"""

    def prep(self, shared):
        tool_result = shared.get("tool_result", {})
        return tool_result

    def exec(self, tool_result):
        """Format the result for return to user"""
        if tool_result.get("success", False):
            result_content = tool_result.get("result", "")

            # Format the web search result
            formatted_result = {
                "search_results": result_content,
                "source": "mcp_web_fetch",  
                "success": True
            }
        else:
            formatted_result = {
                "error": tool_result.get("error", "Unknown error"),
                "source": "mcp_web_fetch",
                "success": False
            }

        return formatted_result

    def post(self, shared, prep_res, exec_res):
        shared["final_result"] = exec_res
        return "default"  # End of flow


class FallbackSearchNode(Node):
    """Fallback when MCP fails - direct search or error"""

    def prep(self, shared):
        query = extract_query_from_shared(shared)
        return query

    def exec(self, query):
        """Provide fallback response when MCP fails"""
        return {
            "search_results": f"Unable to perform web search for '{query}'. MCP server not available.",
            "source": "fallback",
            "success": False,
            "message": "Web search functionality requires MCP server connection"
        }

    def post(self, shared, prep_res, exec_res):
        shared["final_result"] = exec_res
        return "default"  # End of flow


def create_mcp_flow(name: str, instructions: str, server_configs: list,
                   model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7, output_type = None):
    """Create MCP-integrated flow with proper conditional routing"""
    # Get server config (use first server config)
    server_config = server_configs[0] if server_configs else {
        "command": "npx",
        "args": ["-y", "@kazuph/mcp-fetch"]
    }
    # Create nodes
    get_tools = GetToolsNode()
    decide_tool = DecideToolNode()
    execute_tool = ExecuteToolNode()
    format_result = FormatResultNode()
    fallback_search = FallbackSearchNode()

    # Build flow connections using correct PocketFlow syntax
    # Main success path
    get_tools - "decide" >> decide_tool             # If get_tools.post() returns "decide"
    decide_tool - "execute" >> execute_tool         # If decide_tool.post() returns "execute"
    execute_tool >> format_result                   # Default flow (execute_tool.post() returns "default")
    
    # Fallback routes - all lead to fallback_search
    get_tools - "fallback" >> fallback_search       # If get_tools.post() returns "fallback"
    decide_tool - "fallback" >> fallback_search     # If decide_tool.post() returns "fallback"
    execute_tool - "fallback" >> fallback_search    # If execute_tool.post() returns "fallback"

    # Create async flow starting with get_tools
    main_flow = AsyncFlow(start=get_tools)
    
    return main_flow
