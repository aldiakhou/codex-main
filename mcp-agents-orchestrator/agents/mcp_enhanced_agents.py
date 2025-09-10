"""
MCP Enhanced Agents Registry using PocketFlow
Provides registration helpers for MCP-integrated and tool-enhanced agents.

Primary entrypoint for MindRobot: register_mcp_agents(base_registry).
"""
from typing import Dict, Any, List, Optional
import os
import logging

# Import MCP agents
from .web_search import (
    EnhancedWebSearchAgent as WebSearchAgent,
    create_enhanced_web_search_agent as create_web_search_agent,
)
from .deep_research import (
    EnhancedDeepResearchAgent as DeepResearchAgent,
    create_enhanced_deep_research_agent as create_deep_research_agent,
)
# Live monitoring is optional in this build; wrap import
try:
    from .live_monitoring import LiveMonitoringAgent, create_live_monitoring_agent  # type: ignore
    _HAS_LIVE = True
except Exception:
    LiveMonitoringAgent = None  # type: ignore
    create_live_monitoring_agent = None  # type: ignore
    _HAS_LIVE = False
from .rag import RAGAgent, create_rag_agent
from .analysis import AnalysisAgent, create_analysis_agent
from .demo_exec_patch import create_demo_exec_patch_agent

# Import from pocket_flow_agent for registry functionality
# Note: we register into mindrobot.agents.base.AgentRegistry (instances),
# but keep internal factory registry utilities for optional capability inspection.

logger = logging.getLogger(__name__)

# Enhanced agents configuration
ENHANCED_AGENTS_CONFIG = {
    "use_enhanced_web_search": os.getenv("USE_ENHANCED_WEB_SEARCH", "false").lower() == "true",
    "use_enhanced_deep_research": os.getenv("USE_ENHANCED_DEEP_RESEARCH", "false").lower() == "true",
    "research_output_dir": os.getenv("RESEARCH_OUTPUT_DIR", "research_output"),
    "max_parallel_searches": int(os.getenv("MAX_PARALLEL_SEARCHES", "3")),
}


def _check_enhanced_requirements() -> bool:
    """Check if enhanced agents can be used"""
    try:
        import mistune
        import yaml
        return True
    except ImportError:
        logger.warning("Enhanced agents require: pip install mistune pyyaml")
        return False


def _enhanced_available() -> bool:
    """Check if enhanced agents are available and enabled"""
    return _check_enhanced_requirements()


def create_enhanced_web_search_agent(force_enhanced: bool = False):
    """Create web search agent with optional enhanced mode"""
    use_enhanced = force_enhanced or ENHANCED_AGENTS_CONFIG["use_enhanced_web_search"]
    
    if use_enhanced and _enhanced_available():
        try:
            import importlib
            mod = importlib.import_module('.enhanced.web_search_enhanced', package=__package__)
            logger.info("Using enhanced web search agent")
            return getattr(mod, 'create_enhanced_web_search_agent')()
        except Exception as e:
            logger.warning(f"Enhanced web search not available: {e}")
    
    logger.info("Using standard web search agent")
    return create_web_search_agent()


def create_enhanced_deep_research_agent(force_enhanced: bool = False):
    """Create deep research agent with optional enhanced mode"""
    use_enhanced = force_enhanced or ENHANCED_AGENTS_CONFIG["use_enhanced_deep_research"]
    
    if use_enhanced and _enhanced_available():
        try:
            import importlib
            mod = importlib.import_module('.enhanced.deep_research_enhanced', package=__package__)
            logger.info("Using enhanced deep research agent")
            return getattr(mod, 'create_enhanced_deep_research_agent')()
        except Exception as e:
            logger.warning(f"Enhanced deep research not available: {e}")
    
    logger.info("Using standard deep research agent")
    return create_deep_research_agent()


class MCPAgentRegistry:
    """Registry for managing MCP and tool-enhanced agents with metadata"""
    
    def __init__(self):
        self.agents = {}
        self.metadata = {}
        self.server_configs = {}
    
    def register_agent(self, name: str, factory_func, metadata: dict, server_config: dict = None):
        """Register an MCP agent with its factory function, metadata, and server configuration"""
        self.agents[name] = factory_func
        self.metadata[name] = metadata
        if server_config:
            self.server_configs[name] = server_config
    
    def create_agent(self, name: str):
        """Create an agent instance by name"""
        if name not in self.agents:
            raise ValueError(f"Unknown MCP agent: {name}")
        return self.agents[name]()
    
    def get_agent(self, name: str):
        """Get an agent factory function by name (alias for create_agent for compatibility)"""
        return self.create_agent(name)
    
    def get_agent_metadata(self, name: str) -> dict:
        """Get metadata for an agent"""
        return self.metadata.get(name, {})
    
    def get_server_config(self, name: str) -> dict:
        """Get MCP server configuration for an agent"""
        return self.server_configs.get(name, {})
    
    def list_agents(self) -> list:
        """List all registered agent names"""
        return list(self.agents.keys())
    
    def get_agents_by_category(self, category: str) -> list:
        """Get all agents in a specific category"""
        return [
            name for name, meta in self.metadata.items() 
            if meta.get('category') == category
        ]
    
    def get_agents_by_capability(self, capability: str) -> list:
        """Get all agents with a specific capability"""
        return [
            name for name, meta in self.metadata.items() 
            if capability in meta.get('capabilities', [])
        ]


# Create global MCP registry instance
_mcp_agent_registry = MCPAgentRegistry()


def register_mcp_enhanced_agents(registry: MCPAgentRegistry = None):
    """Register all MCP and tool-enhanced agents with the registry"""
    if registry is None:
        registry = _mcp_agent_registry
    
    # Register enhanced web search agent (auto-selects enhanced or standard)
    registry.register_agent("web_search", create_enhanced_web_search_agent, {
        "category": "mcp_integrated",
        "primary_use": "web_search",
        "output_format": "WebSearchResponse",
        "framework": "PocketFlow + Enhanced",
        "capabilities": ["web_search", "url_fetch", "real_time_data", "multi_engine_search", "source_evaluation"],
        "requires_internet": True,
        "typical_runtime": "3-15s",
        "description": "Enhanced web search with multi-engine support and AI evaluation",
        "enhanced_features": ["parallel_search", "source_ranking", "result_synthesis"]
    }, {
        "name": "mcp_fetch",
        "command": "npx",
        "args": ["-y", "@kazuph/mcp-fetch"],
        "type": "stdio"
    })
    
    # Register enhanced deep research agent (auto-selects enhanced or standard)
    registry.register_agent("deep_research", create_enhanced_deep_research_agent, {
        "category": "mcp_integrated",
        "primary_use": "comprehensive_research",
        "output_format": "ResearchResponse",
        "framework": "PocketFlow + Enhanced",
        "capabilities": ["deep_research", "academic_sources", "multi_source_analysis", "document_generation", "research_planning"],
        "requires_internet": True,
        "typical_runtime": "15-60s",
        "description": "Conduct comprehensive research using multiple sources"
    }, {
        "name": "research_server",
        "command": "npx",
        "args": ["-y", "@kazuph/mcp-fetch"],
        "type": "stdio"
    })
    
    # Register live monitoring agent
    registry.register_agent("live_monitoring", create_live_monitoring_agent, {
        "category": "mcp_integrated",
        "primary_use": "real_time_monitoring",
        "output_format": "LiveMonitoringResponse",
        "framework": "PocketFlow",
        "capabilities": ["real_time_monitoring", "alerts", "trend_analysis"],
        "requires_internet": True,
        "typical_runtime": "2-8s",
        "description": "Monitor live data sources and generate alerts"
    }, {
        "name": "monitoring_server",
        "command": "npx",
        "args": ["-y", "@kazuph/mcp-fetch"],
        "type": "stdio"
    })
    
    # Register RAG agent
    registry.register_agent("rag", create_rag_agent, {
        "category": "tool_enhanced",
        "primary_use": "document_qa",
        "output_format": "RAGResponse",
        "framework": "PocketFlow",
        "capabilities": ["document_processing", "retrieval", "generation", "citations"],
        "requires_internet": False,
        "typical_runtime": "5-20s",
        "description": "Retrieval-Augmented Generation for document-based Q&A"
    })
    
    # Register analysis agent
    registry.register_agent("analysis", create_analysis_agent, {
        "category": "tool_enhanced",
        "primary_use": "data_analysis",
        "output_format": "AnalysisResponse",
        "framework": "PocketFlow",
        "capabilities": ["data_analysis", "pattern_recognition", "insights"],
        "requires_internet": False,
        "typical_runtime": "8-25s",
        "description": "Analyze data and generate insights with recommendations"
    })


def get_mcp_agent_registry() -> MCPAgentRegistry:
    """Get the global MCP agent registry"""
    return _mcp_agent_registry


def initialize_mcp_agents():
    """Initialize all MCP agents and register them"""
    register_mcp_enhanced_agents(_mcp_agent_registry)
    return _mcp_agent_registry


def get_available_mcp_agents() -> dict:
    """Get all available MCP agents with their metadata"""
    return {
        name: {
            "factory": factory,
            "metadata": _mcp_agent_registry.get_agent_metadata(name),
            "server_config": _mcp_agent_registry.get_server_config(name)
        }
        for name, factory in _mcp_agent_registry.agents.items()
    }


def create_mcp_agent_by_name(agent_name: str):
    """Create an MCP agent instance by name - convenience function"""
    return _mcp_agent_registry.create_agent(agent_name)


def get_mcp_agents_by_type(agent_type: str) -> list:
    """Get MCP agents by type (mcp_integrated or tool_enhanced)"""
    return _mcp_agent_registry.get_agents_by_category(agent_type)


def get_agents_with_capability(capability: str) -> list:
    """Get agents that have a specific capability"""
    return _mcp_agent_registry.get_agents_by_capability(capability)


# Agent capability analysis for MCP agents
def get_mcp_agent_capabilities() -> dict:
    """Get comprehensive capability analysis of all MCP agents"""
    capabilities = {}
    
    for name in _mcp_agent_registry.list_agents():
        try:
            agent = _mcp_agent_registry.create_agent(name)
            metadata = _mcp_agent_registry.get_agent_metadata(name)
            server_config = _mcp_agent_registry.get_server_config(name)
            
            capabilities[name] = {
                "agent_info": agent.get_agent_info(),
                "metadata": metadata,
                "server_config": server_config,
                "supports_requests": _get_supported_mcp_request_types(name),
                "output_structure": _get_mcp_output_structure(name)
            }
        except Exception as e:
            capabilities[name] = {
                "status": "error",
                "error": str(e)
            }
    
    return capabilities


def _get_supported_mcp_request_types(agent_name: str) -> list:
    """Get supported request types for an MCP agent"""
    # All MCP agents support AIAgentRequest as base
    return ["AIAgentRequest"]


def _get_mcp_output_structure(agent_name: str) -> dict:
    """Get output structure information for an MCP agent"""
    output_mapping = {
        "web_search": {
            "type": "WebSearchResponse",
            "fields": ["query", "results", "total_results", "search_time"],
            "results_structure": "List[SearchResult]"
        },
        "deep_research": {
            "type": "ResearchResponse",
            "fields": ["research_topic", "executive_summary", "sections", "key_findings"],
            "sections_structure": "List[ResearchSection]"
        },
        "live_monitoring": {
            "type": "LiveMonitoringResponse",
            "fields": ["monitoring_target", "status", "data_points", "alerts"],
            "alerts_structure": "List[MonitoringAlert]"
        },
        "rag": {
            "type": "RAGResponse",
            "fields": ["query", "answer", "sources", "confidence_score"],
            "sources_structure": "List[str]"
        },
        "analysis": {
            "type": "AnalysisResponse",
            "fields": ["analysis_type", "summary", "key_insights", "metrics"],
            "metrics_structure": "List[MetricData]"
        }
    }
    return output_mapping.get(agent_name, {"type": "Unknown"})


# Performance and monitoring utilities
def validate_all_mcp_agents() -> dict:
    """Validate all registered MCP agents can be created successfully"""
    results = {}
    
    for name in _mcp_agent_registry.list_agents():
        try:
            agent = _mcp_agent_registry.create_agent(name)
            agent_info = agent.get_agent_info()
            results[name] = {
                "status": "success",
                "agent_info": agent_info
            }
        except Exception as e:
            results[name] = {
                "status": "error",
                "error": str(e)
            }
    
    return results


# Server configuration helpers
def get_mcp_server_requirements() -> dict:
    """Get all MCP server requirements for the registered agents"""
    servers = {}
    
    for name in _mcp_agent_registry.list_agents():
        server_config = _mcp_agent_registry.get_server_config(name)
        if server_config:
            server_name = server_config.get("name", f"{name}_server")
            servers[server_name] = server_config
    
    return servers


def generate_mcp_setup_instructions() -> str:
    """Generate setup instructions for all required MCP servers"""
    servers = get_mcp_server_requirements()
    instructions = []
    
    instructions.append("# MCP Server Setup Instructions")
    instructions.append("## Required MCP Servers:")
    
    for server_name, config in servers.items():
        command = config.get("command", "")
        args = " ".join(config.get("args", []))
        instructions.append(f"\n### {server_name}")
        instructions.append(f"Command: `{command} {args}`")
        instructions.append(f"Type: {config.get('type', 'stdio')}")
    
    instructions.append("\n## Installation:")
    instructions.append("```bash")
    instructions.append("# Install npm packages globally")
    instructions.append("npm install -g @kazuph/mcp-fetch")
    instructions.append("```")
    
    return "\n".join(instructions)


# Initialize agents on module import
initialize_mcp_agents()


# =============================
# MindRobot integration helpers
# =============================

def register_mcp_agents(base_registry) -> None:
    """Register MCP and tool-enhanced agents into the base AgentRegistry (instances).

    Registration is best-effort: failures for one agent do not prevent others.
    """
    def _safe_register(agent_id: str, factory):
        try:
            base_registry.register_agent(agent_id, factory, {"category": "mcp_integrated" if agent_id in {"web_search","deep_research","live_monitoring"} else "tool_enhanced"})
            logger.info(f"Registered agent: {agent_id}")
        except Exception as e:
            logger.warning(f"Skipping agent {agent_id}: {e}")

    _safe_register("web_search", create_enhanced_web_search_agent())
    _safe_register("deep_research", create_enhanced_deep_research_agent())
    if _HAS_LIVE and callable(create_live_monitoring_agent):
        _safe_register("live_monitoring", create_live_monitoring_agent())
    _safe_register("rag", create_rag_agent())
    _safe_register("analysis", create_analysis_agent())
    _safe_register("demo_exec_patch", create_demo_exec_patch_agent())


async def test_mcp_connectivity() -> bool:
    """Lightweight connectivity stub.
    Real implementation could attempt an MCP client session and list_tools.
    """
    return True
