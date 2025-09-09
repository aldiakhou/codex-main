"""
Pocket Flow Agent Implementation for MindRobot
Compatible with existing MindRobot architecture while using Pocket Flow's lightweight framework
"""

from .base import (
    PocketFlowAgent, 
    StructuredOutputAgent,
    MCPIntegratedAgent,
    ToolEnhancedAgent,
    AgentRegistry,
    get_agent_registry
)

from .brainstorm import BrainstormAgent, create_brainstorm_agent
# Web search: provide compatibility aliases
from .web_search import (
    EnhancedWebSearchAgent as WebSearchAgent,
    create_enhanced_web_search_agent as create_web_search_agent,
)
from .rag import RAGAgent, create_rag_agent
# Deep research: provide compatibility aliases
from .deep_research import (
    EnhancedDeepResearchAgent as DeepResearchAgent,
    create_enhanced_deep_research_agent as create_deep_research_agent,
)
from .analysis import AnalysisAgent, create_analysis_agent
from .summary import SummaryAgent, create_summary_agent
from .tag import TagAgent, create_tag_agent
from .expand import ExpandAgent, create_expand_agent
from .live_monitoring import LiveMonitoringAgent, create_live_monitoring_agent
from .connexion import ConnectionAgent, create_connection_agent

# Unified registry initialization
from .registry import initialize_all_agents as initialize_pocket_flow_agents
from .registry import get_agent_system_status

# Quick access functions
async def process_brainstorm_request(topic: str, num_ideas: str = "4-6", style: str = "creative", context: dict = None):
    """Process brainstorm request using Pocket Flow"""
    from ..core.models import BrainstormRequest
    registry = get_agent_registry()
    request = BrainstormRequest(topic=topic, num_ideas=num_ideas, style=style, context=context)
    return await registry.process_request("brainstorm", request)

async def process_web_search_request(query: str, search_type: str = "general", max_results: int = 5):
    """Process web search request using Pocket Flow"""
    from ..core.models import AIAgentRequest
    registry = get_agent_registry()
    request = AIAgentRequest(context={
        "query": query,
        "search_type": search_type,
        "max_results": max_results
    })
    return await registry.process_request("web_search", request)

async def process_rag_request(query: str, search_type: str = "comprehensive", max_results: int = 10):
    """Process RAG request using Pocket Flow"""
    from ..core.models import AIAgentRequest
    registry = get_agent_registry()
    request = AIAgentRequest(context={
        "query": query,
        "search_type": search_type,
        "max_results": max_results
    })
    return await registry.process_request("rag", request)

__all__ = [
    # Base classes
    'PocketFlowAgent',
    'StructuredOutputAgent', 
    'MCPIntegratedAgent',
    'ToolEnhancedAgent',
    'AgentRegistry',
    'get_agent_registry',
    
    # Agent classes
    'BrainstormAgent',
    'WebSearchAgent',
    'RAGAgent',
    'DeepResearchAgent',
    'AnalysisAgent',
    'SummaryAgent',
    'TagAgent',
    'ExpandAgent',
    'LiveMonitoringAgent',
    'ConnectionAgent',
    
    # Factory functions
    'create_brainstorm_agent',
    'create_web_search_agent',
    'create_rag_agent',
    'create_deep_research_agent',
    'create_analysis_agent',
    'create_summary_agent',
    'create_tag_agent',
    'create_expand_agent',
    'create_live_monitoring_agent',
    'create_connection_agent',
    
    # Initialization
    'initialize_pocket_flow_agents',
    'get_agent_system_status',
    'process_brainstorm_request',
    'process_web_search_request',
    'process_rag_request',
]
