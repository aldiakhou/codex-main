"""
Agents package (compatibility-friendly)

Goals:
- Keep imports light to avoid hard failures on optional modules
- Provide convenience functions used by previous examples
- Expose registry access for direct agent execution
"""

from .base import (
    PocketFlowAgent,
    StructuredOutputAgent,
    MCPIntegratedAgent,
    ToolEnhancedAgent,
    AgentRegistry,
    get_agent_registry,
)

# Lazily import inside functions to avoid import-time failures

async def process_web_search_request(query: str, search_type: str = "general", max_results: int = 5, context: dict | None = None):
    """Convenience wrapper to run the web_search agent via the global registry.

    Mirrors earlier examples: from mindrobot.agents import process_web_search_request
    """
    from ..core.models import AIAgentRequest
    registry = get_agent_registry()
    ctx = {"query": query, "search_type": search_type, "max_results": max_results}
    if context:
        ctx.update(context)
    req = AIAgentRequest(context=ctx)
    return await registry.process_request("web_search", req)


async def process_rag_request(query: str, search_type: str = "comprehensive", max_results: int = 10, context: dict | None = None):
    """Convenience wrapper to run the rag agent via the global registry."""
    from ..core.models import AIAgentRequest
    registry = get_agent_registry()
    ctx = {"query": query, "search_type": search_type, "max_results": max_results}
    if context:
        ctx.update(context)
    req = AIAgentRequest(context=ctx)
    return await registry.process_request("rag", req)


# Optional: initialization helpers (re-export for compatibility)
try:
    from .registry import initialize_all_agents as initialize_pocket_flow_agents  # type: ignore
    from .registry import get_agent_system_status  # type: ignore
except Exception:  # pragma: no cover
    def initialize_pocket_flow_agents(*args, **kwargs):  # type: ignore
        return {"success": False, "error": "registry unavailable"}
    def get_agent_system_status():  # type: ignore
        return {"total_agents": 0, "available_agents": []}


__all__ = [
    # Base classes
    'PocketFlowAgent',
    'StructuredOutputAgent',
    'MCPIntegratedAgent',
    'ToolEnhancedAgent',
    'AgentRegistry',
    'get_agent_registry',
    # Convenience functions
    'process_web_search_request',
    'process_rag_request',
    # Optional helpers
    'initialize_pocket_flow_agents',
    'get_agent_system_status',
]
