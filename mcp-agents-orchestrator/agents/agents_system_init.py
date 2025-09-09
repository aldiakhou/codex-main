"""
Complete Agent System Initialization for MindRobot
Follows the enhancement implementation guide with proper OpenAI Agents SDK integration
"""
import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

# Import agent modules
from .base import get_agent_registry, BaseAgentInterface
from .registry import initialize_all_agents, get_agent_system_status

# Import core models
from ..core.models import (
    AIAgentRequest, BrainstormRequest, ExpandNodeRequest, 
    MCPToolResponse
)

# OpenAI Agents SDK
from agents import set_tracing_disabled

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable tracing for privacy
set_tracing_disabled(True)


class MindRobotAgentSystem:
    """Complete agent system manager for MindRobot following enhancement guide"""
    
    def __init__(self):
        self.registry = get_agent_registry()
        self.initialization_status = {}
        self.agent_categories = {
            "structured_output": [],
            "mcp_integrated": [], 
            "tool_enhanced": []
        }
    
    async def initialize_system(self, 
                              enable_mcp: bool = True,
                              enable_tools: bool = True,
                              test_connectivity: bool = True) -> Dict[str, Any]:
        """Initialize the complete agent system"""
        logger.info("🚀 Initializing MindRobot Agent System...")
        
        try:
            result = await initialize_all_agents(
                enable_mcp=enable_mcp,
                enable_tools=enable_tools,
                test_connectivity=test_connectivity,
            )
            self.initialization_status = result
            # Derive categories from registry metadata
            for agent_id in self.registry.list_agents():
                info = self.registry.get_agent_info(agent_id) or {}
                category = info.get("category") or info.get("type")
                if category in self.agent_categories:
                    self.agent_categories[category].append(agent_id)
            result["system_status"] = "ready" if result.get("success") else "failed"
            result["categories"] = self.agent_categories
            result["total_agents"] = len(self.registry.list_agents())
            logger.info(f"🎉 Agent system initialized with {result['total_agents']} agents")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to initialize agent system: {e}")
            return {
                "system_status": "failed",
                "errors": [str(e)],
            }
    
    async def process_agent_request(self, 
                                  agent_id: str, 
                                  request: Union[AIAgentRequest, Dict[str, Any]]) -> Any:
        """Process a request through the specified agent"""
        try:
            # Convert dict to proper request object if needed
            if isinstance(request, dict):
                if agent_id == "brainstorm":
                    request = BrainstormRequest(**request)
                elif agent_id == "expand_node":
                    request = ExpandNodeRequest(**request)
                else:
                    request = AIAgentRequest(**request)
            
            # Process through registry
            result = await self.registry.process_request(agent_id, request)
            
            return MCPToolResponse(
                success=True,
                data=result if isinstance(result, dict) else {"output": str(result)},
                metadata={
                    "agent_id": agent_id,
                    "request_id": getattr(request, 'request_id', 'unknown'),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing request for {agent_id}: {e}")
            return MCPToolResponse(
                success=False,
                error=str(e),
                metadata={
                    "agent_id": agent_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and capabilities"""
        status = get_agent_system_status()
        return {
            "system_ready": status.get("total_agents", 0) > 0,
            "total_agents": status.get("total_agents", 0),
            "available_agents": status.get("available_agents", []),
            "agents_by_category": self.agent_categories,
        }


# Global agent system instance
agent_system = MindRobotAgentSystem()


# Convenience functions for integration

async def initialize_mindrobot_agents(
    enable_mcp: bool = True,
    enable_tools: bool = True,
    test_connectivity: bool = True
) -> Dict[str, Any]:
    """Initialize the complete MindRobot agent system"""
    return await agent_system.initialize_system(
        enable_mcp=enable_mcp,
        enable_tools=enable_tools, 
        test_connectivity=test_connectivity
    )


def get_system_status() -> Dict[str, Any]:
    """Get current agent system status"""
    return agent_system.get_system_status()