"""
Structured Output Agents using PocketFlow with core models
Provides registry and factory functions for all mind map agents.

This module remains backward-compatible with its own lightweight factory registry
but can also register concrete agent instances into the global base.AgentRegistry.
"""
from .brainstorm import create_brainstorm_agent, BrainstormAgent
from .expand import create_expand_agent, ExpandAgent  
from .tag import create_tag_agent, TagAgent
from .summary import create_summary_agent, SummaryAgent
# Note: connections agent not available; skip import/registration to avoid import errors


# Agent registry for system integration
class AgentRegistry:
    """Registry for managing and creating agents with metadata"""
    
    def __init__(self):
        self.agents = {}
        self.metadata = {}
    
    def register_agent(self, name: str, factory_func, metadata: dict):
        """Register an agent with its factory function and metadata"""
        self.agents[name] = factory_func
        self.metadata[name] = metadata
    
    def create_agent(self, name: str):
        """Create an agent instance by name"""
        if name not in self.agents:
            raise ValueError(f"Unknown agent: {name}")
        return self.agents[name]()
    
    def get_agent_metadata(self, name: str) -> dict:
        """Get metadata for an agent"""
        return self.metadata.get(name, {})
    
    def list_agents(self) -> list:
        """List all registered agent names"""
        return list(self.agents.keys())
    
    def get_agents_by_category(self, category: str) -> list:
        """Get all agents in a specific category"""
        return [
            name for name, meta in self.metadata.items() 
            if meta.get('category') == category
        ]


# Create global registry instance
_agent_registry = AgentRegistry()


def register_structured_agents(registry: AgentRegistry = None):
    """Register all structured output agents with the registry"""
    if registry is None:
        registry = _agent_registry
    
    # Determine if the provided registry is a factory-registry (this module)
    # or the global instance registry from mindrobot.agents.base
    is_factory_registry = hasattr(registry, "create_agent") and hasattr(registry, "register_agent") and not hasattr(registry, "process_request")
    
    # Register brainstorm agent
    if is_factory_registry:
        registry.register_agent("brainstorm", create_brainstorm_agent, {
        "category": "core",
        "primary_use": "idea_generation",
        "output_format": "BrainstormResponse",
        "framework": "PocketFlow",
        "supports_creativity": True,
        "typical_runtime": "5-15s",
        "description": "Generates creative, structured ideas for mind mapping"
    })
    else:
        # Base AgentRegistry expects concrete instances
        instance = create_brainstorm_agent()
        registry.register_agent("brainstorm", instance, {
            "category": "structured_output",
            "primary_use": "idea_generation",
            "output_format": "BrainstormResponse",
            "framework": "PocketFlow",
            "supports_creativity": True,
            "typical_runtime": "5-15s",
            "description": "Generates creative, structured ideas for mind mapping"
        })
    
    # Register expand agent  
    if is_factory_registry:
        registry.register_agent("expand_node", create_expand_agent, {
            "category": "core",
            "primary_use": "content_expansion", 
            "output_format": "ExpandNodeResponse",
            "framework": "PocketFlow",
            "supports_creativity": True,
            "typical_runtime": "5-20s",
            "description": "Expands existing nodes with related ideas and connections"
        })
    else:
        instance = create_expand_agent()
        registry.register_agent("expand_node", instance, {
            "category": "structured_output",
            "primary_use": "content_expansion", 
            "output_format": "ExpandNodeResponse",
            "framework": "PocketFlow",
            "supports_creativity": True,
            "typical_runtime": "5-20s",
            "description": "Expands existing nodes with related ideas and connections"
        })
    
    # Register tag agent
    if is_factory_registry:
        registry.register_agent("tags", create_tag_agent, {
            "category": "core",
            "primary_use": "content_categorization",
            "output_format": "TagResponse", 
            "framework": "PocketFlow",
            "supports_creativity": False,
            "typical_runtime": "3-8s",
            "description": "Suggests relevant tags for improved organization"
        })
    else:
        instance = create_tag_agent()
        registry.register_agent("tags", instance, {
            "category": "structured_output",
            "primary_use": "content_categorization",
            "output_format": "TagResponse", 
            "framework": "PocketFlow",
            "supports_creativity": False,
            "typical_runtime": "3-8s",
            "description": "Suggests relevant tags for improved organization"
        })
    
    # Register summary agent
    if is_factory_registry:
        registry.register_agent("summary", create_summary_agent, {
            "category": "core", 
            "primary_use": "content_summarization",
            "output_format": "SummaryResponse",
            "framework": "PocketFlow", 
            "supports_creativity": False,
            "typical_runtime": "8-25s",
            "description": "Creates comprehensive summaries of mind map content"
        })
    else:
        instance = create_summary_agent()
        registry.register_agent("summary", instance, {
            "category": "structured_output", 
            "primary_use": "content_summarization",
            "output_format": "SummaryResponse",
            "framework": "PocketFlow", 
            "supports_creativity": False,
            "typical_runtime": "8-25s",
            "description": "Creates comprehensive summaries of mind map content"
        })
    
    # Connection agent not available currently; skip registration


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry"""
    return _agent_registry


def initialize_agents():
    """Initialize all agents and register them"""
    register_structured_agents(_agent_registry)
    return _agent_registry


def get_available_agents() -> dict:
    """Get all available agents with their metadata"""
    return {
        name: {
            "factory": factory,
            "metadata": _agent_registry.get_agent_metadata(name)
        }
        for name, factory in _agent_registry.agents.items()
    }


def create_agent_by_name(agent_name: str):
    """Create an agent instance by name - convenience function"""
    return _agent_registry.create_agent(agent_name)


# Backward compatibility functions for existing code
def create_brainstorm_agent_compat():
    """Backward compatibility wrapper"""
    return create_brainstorm_agent()


def create_expand_agent_compat():
    """Backward compatibility wrapper"""
    return create_expand_agent()


def create_tag_agent_compat():
    """Backward compatibility wrapper"""
    return create_tag_agent()


def create_summary_agent_compat():
    """Backward compatibility wrapper"""
    return create_summary_agent()


def create_connection_agent_compat():
    """Backward compatibility wrapper"""
    # Not available currently; kept for compatibility
    raise NotImplementedError("'connections' agent is not implemented in this build")


# Agent capability analysis
def get_agent_capabilities() -> dict:
    """Get comprehensive capability analysis of all agents"""
    capabilities = {}
    
    for name in _agent_registry.list_agents():
        agent = _agent_registry.create_agent(name)
        metadata = _agent_registry.get_agent_metadata(name)
        
        capabilities[name] = {
            "agent_info": agent.get_agent_info(),
            "metadata": metadata,
            "supports_requests": _get_supported_request_types(name),
            "output_structure": _get_output_structure(name)
        }
    
    return capabilities


def _get_supported_request_types(agent_name: str) -> list:
    """Get supported request types for an agent"""
    request_mapping = {
        "brainstorm": ["BrainstormRequest", "AIAgentRequest"],
        "expand_node": ["ExpandNodeRequest", "AIAgentRequest"],
        "tags": ["TagRequest", "AIAgentRequest"],
        "summary": ["SummaryRequest", "AIAgentRequest"],
        "connections": ["ConnectionRequest", "AIAgentRequest"]
    }
    return request_mapping.get(agent_name, ["AIAgentRequest"])


def _get_output_structure(agent_name: str) -> dict:
    """Get output structure information for an agent"""
    output_mapping = {
        "brainstorm": {
            "type": "BrainstormResponse",
            "fields": ["ideas", "main_theme", "connections"],
            "ideas_structure": "List[NodeIdea]"
        },
        "expand_node": {
            "type": "ExpandNodeResponse", 
            "fields": ["expansions", "new_connections", "summary"],
            "expansions_structure": "List[NodeIdea]"
        },
        "tags": {
            "type": "TagResponse",
            "fields": ["suggestions"],
            "suggestions_structure": "TagSuggestion"
        },
        "summary": {
            "type": "SummaryResponse",
            "fields": ["summary", "key_points", "main_themes"],
            "summary_structure": "str"
        },
        "connections": {
            "type": "ConnectionResponse",
            "fields": ["suggestions", "analysis"],
            "suggestions_structure": "List[ConnectionSuggestion]"
        }
    }
    return output_mapping.get(agent_name, {"type": "Unknown"})


# Performance and monitoring utilities
def validate_all_agents() -> dict:
    """Validate all registered agents can be created successfully"""
    results = {}
    
    for name in _agent_registry.list_agents():
        try:
            agent = _agent_registry.create_agent(name)
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


# Initialize agents on module import
initialize_agents()