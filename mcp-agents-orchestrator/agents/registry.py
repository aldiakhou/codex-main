"""
Unified agent registry and initialization for MindRobot.

Registers all agent types (structured output, MCP-integrated, tool-enhanced)
into the single global base.AgentRegistry and provides status helpers.
"""
from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime
import logging

from .base import get_agent_registry
from .structured_output_agents import register_structured_agents
from .mcp_enhanced_agents import register_mcp_agents, test_mcp_connectivity

logger = logging.getLogger(__name__)


def _register_structured(registry) -> List[str]:
    before = set(registry.list_agents())
    register_structured_agents(registry)
    after = set(registry.list_agents())
    return sorted(list(after - before))


def _register_mcp_and_tools(registry, enable_mcp: bool, enable_tools: bool) -> List[str]:
    added: List[str] = []
    if enable_mcp or enable_tools:
        before = set(registry.list_agents())
        register_mcp_agents(registry)
        after = set(registry.list_agents())
        # This function registers both MCP and tool agents together
        added = sorted(list(after - before))
    return added


async def initialize_all_agents(
    enable_mcp: bool = True,
    enable_tools: bool = True,
    test_connectivity: bool = False,
) -> Dict[str, Any]:
    """Initialize all agents into the global base registry and return a summary."""
    registry = get_agent_registry()

    result: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "success": True,
        "added_agents": [],
        "warnings": [],
        "errors": [],
    }

    try:
        added_structured = _register_structured(registry)
        logger.info(f"Registered structured agents: {added_structured}")
        result["added_agents"].extend(added_structured)
    except Exception as e:
        logger.error(f"Failed to register structured agents: {e}")
        result["errors"].append(str(e))

    # Optional MCP connectivity test
    if test_connectivity and enable_mcp:
        try:
            ok = await test_mcp_connectivity()
            if not ok:
                result["warnings"].append("MCP connectivity test failed")
        except Exception as e:
            result["warnings"].append(f"MCP connectivity test error: {e}")

    try:
        added_mcp_tools = _register_mcp_and_tools(registry, enable_mcp, enable_tools)
        logger.info(f"Registered MCP/tools agents: {added_mcp_tools}")
        result["added_agents"].extend(added_mcp_tools)
    except Exception as e:
        logger.error(f"Failed to register MCP/tool agents: {e}")
        result["errors"].append(str(e))

    result["total_agents"] = len(registry.list_agents())
    result["available_agents"] = registry.list_agents()
    return result


def get_agent_system_status() -> Dict[str, Any]:
    """Return a simple snapshot of the agent system status."""
    registry = get_agent_registry()
    agents = registry.list_agents()
    return {
        "total_agents": len(agents),
        "available_agents": agents,
    }
