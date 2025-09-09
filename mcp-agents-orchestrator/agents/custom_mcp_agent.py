"""
MCP Integrated Agents using OpenAI Agents SDK
custom mcp agent
"""
from typing import Dict, Any, List, Optional
import os
import asyncio
import logging

from .base import MCPIntegratedAgent, AgentFactory
from ..core.models import AIAgentRequest
from agents.mcp import MCPServerStdio, MCPServerSse, MCPServerStreamableHttp

logger = logging.getLogger(__name__)




class CustomMCPAgent(MCPIntegratedAgent):
    """Customizable MCP agent for specific use cases"""
    
    def __init__(self, 
                 name: str,
                 instructions: str,
                 mcp_server_configs: List[Dict[str, Any]],
                 **kwargs):
        
        # Build MCP servers from configurations
        mcp_servers = []
        for config in mcp_server_configs:
            server_type = config.get('type', 'stdio')
            
            if server_type == 'stdio':
                server = MCPServerStdio(
                    name=config.get('name', 'Custom Server'),
                    params=config.get('params', {})
                )
            elif server_type == 'sse':
                server = MCPServerSse(
                    name=config.get('name', 'Custom Server'),
                    params=config.get('params', {})
                )
            elif server_type == 'streamable_http':
                server = MCPServerStreamableHttp(
                    name=config.get('name', 'Custom Server'),
                    params=config.get('params', {})
                )
            else:
                continue
                
            mcp_servers.append(server)
        
        super().__init__(name, instructions, mcp_servers, **kwargs)


# Factory function to create a custom MCP agent
def create_custom_mcp_agent(name: str,
                            instructions: str,
                            mcp_server_configs: List[Dict[str, Any]]) -> CustomMCPAgent:
    """Create a custom MCP agent with MCP integration"""
    return CustomMCPAgent(name, instructions, mcp_server_configs)

