"""
Base Agent Classes using Pocket Flow
Maintains compatibility with existing MindRobot architecture
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type, Union
from datetime import datetime
import uuid
import asyncio
import json
from contextlib import asynccontextmanager

from pocketflow import Node, Flow, AsyncNode
import os
from .mcp_client import PocketFlowMCPClient
from .mcp_result_formatter import MCPResultFormatter
from core.models import (
    AIAgentRequest, MCPToolResponse, ErrorSeverity, WebSearchResponse, ResearchResponse, RAGResponse, LiveMonitoringResponse
)
from core.logging import (
    get_logger, RequestContext, PerformanceTimer, 
    log_agent_activity, log_agent_error
)
from core.config import get_config

logger = get_logger(__name__)

# Import LLM Helper function
from .utils import call_llm

# Custom exceptions (maintain compatibility)
class AgentError(Exception):
    """Base exception for agent-related errors"""
    pass

class AgentTimeoutError(AgentError):
    """Raised when an agent operation times out"""
    pass

class AgentProcessingError(AgentError):
    """Raised when an agent fails to process a request"""
    pass

class AgentConfigurationError(AgentError):
    """Raised when an agent is misconfigured"""
    pass

class AgentValidationError(AgentError):
    """Raised when agent input validation fails"""
    pass


class BaseAgentInterface(ABC):
    """Abstract base interface for all MindRobot agents"""
    
    @abstractmethod
    async def process(self, request: AIAgentRequest) -> Union[Dict[str, Any], Any]:
        """Process agent request and return structured response"""
        pass
    
    @abstractmethod
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information and capabilities"""
        pass


class PocketFlowAgent(BaseAgentInterface):
    """Base class for Pocket Flow agents with backward compatibility"""
    
    def __init__(self, name: str, flow: Flow):
        self.name = name
        self.flow = flow
        logger.info(f"Initialized PocketFlowAgent: {name}")
    
    async def process(self, request: AIAgentRequest) -> Any:
        """Process request using Pocket Flow"""
        request_id = request.request_id or str(uuid.uuid4())
        
        with RequestContext(request_id=request_id, agent_name=self.name):
            with PerformanceTimer(logger, f"{self.name}.process", request_id=request_id):
                try:
                    log_agent_activity(self.name, "processing_request", 
                                     request_id=request_id)
                    
                    # Run the flow
                    shared = {"request": request, "request_id": request_id}
                    
                    # Run with timeout
                    config = get_config()
                    timeout = config.ai.agent_request_timeout
                    
                    # Use asyncio for timeout if needed
                    if hasattr(self.flow, 'run_async'):
                        # AsyncFlow
                        result = await asyncio.wait_for(
                            self.flow.run_async(shared),
                            timeout=timeout
                        )
                    elif asyncio.iscoroutinefunction(self.flow.run):
                        # Async Flow with run method
                        result = await asyncio.wait_for(
                            self.flow.run(shared),
                            timeout=timeout
                        )
                    else:
                        # Run sync flow in executor
                        loop = asyncio.get_event_loop()
                        result = await asyncio.wait_for(
                            loop.run_in_executor(None, self.flow.run, shared),
                            timeout=timeout
                        )
                    
                    log_agent_activity(self.name, "process_completed", 
                                     request_id=request_id)
                    
                    return shared.get("result", shared.get("output"))
                    
                except asyncio.TimeoutError as e:
                    error_context = {
                        "request_id": request_id,
                        "timeout": timeout,
                        "operation": "agent_processing"
                    }
                    log_agent_error(self.name, e, error_context)
                    raise AgentTimeoutError(f"Agent {self.name} timed out after {timeout}s") from e
                    
                except Exception as e:
                    error_context = {
                        "request_id": request_id,
                        "operation": "agent_processing"
                    }
                    log_agent_error(self.name, e, error_context)
                    raise AgentProcessingError(f"Error in {self.name}: {str(e)}") from e
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.name,
            "type": "pocket_flow",
            "framework": "PocketFlow",
            "capabilities": self._get_capabilities()
        }
    
    def _get_capabilities(self) -> List[str]:
        """Override in subclasses to provide specific capabilities"""
        return ["pocket_flow_based"]


class StructuredOutputNode(Node):
    """Node that produces structured Pydantic output"""
    
    def __init__(self, name: str, instructions: str, output_model: Type, 
                 model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7, max_tokens: int = 2000):
        super().__init__()
        self.name = name
        self.instructions = instructions
        self.output_model = output_model
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def prep(self, shared):
        """Prepare the request"""
        return shared.get("request")
    
    def exec(self, request):
        """Execute LLM call with structured output"""
        # Build prompt
        input_text = self._build_input_text(request)
        
        # Add JSON schema instruction
        schema = self.output_model.model_json_schema()
        
        prompt = f"""{self.instructions}

INPUT:
{input_text}

OUTPUT INSTRUCTIONS:
Respond with a valid JSON object that conforms to this schema:
{json.dumps(schema, indent=2)}

Ensure your response is ONLY the JSON object, no additional text."""
        
        # Call LLM
        response = call_llm(prompt, self.model, self.temperature, self.max_tokens)
        
        # Parse response
        try:
            # Clean response if needed
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse JSON and validate with Pydantic
            json_data = json.loads(response)
            return self.output_model(**json_data)
        except Exception as e:
            logger.error(f"Failed to parse structured output: {e}")
            logger.error(f"Response was: {response}")
            raise AgentProcessingError(f"Failed to parse structured output: {str(e)}")
    
    def post(self, shared, prep_res, exec_res):
        """Save result"""
        shared["result"] = exec_res
        return None
    
    def _build_input_text(self, request):
        """Override in subclasses to build specific input"""
        return str(request.model_dump())


class StructuredOutputAgent(PocketFlowAgent):
    """Agent that uses Pocket Flow with structured Pydantic output"""
    
    def __init__(self, name: str, instructions: str, output_model: Type,
                 model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7, max_tokens: int = 2000):
        
        # Create the structured output node
        node = StructuredOutputNode(name, instructions, output_model, model, temperature, max_tokens)
        
        # Create flow with single node
        flow = Flow(start=node)
        
        super().__init__(name, flow)
        
        self.output_model = output_model
        self.model = model
        
        logger.info(f"Initialized StructuredOutputAgent: {name}")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        info = super().get_agent_info()
        info.update({
            "type": "structured_output",
            "output_model": self.output_model.__name__,
            "model": self.model,
            "capabilities": ["structured_output", "pydantic_validation", "pocket_flow"]
        })
        return info


class MCPIntegratedAgent(PocketFlowAgent):
    """Agent that uses MCP servers through Pocket Flow"""
    
    def __init__(self, name: str, instructions: str, server_configs: List[Dict[str, Any]],
                 model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7, output_type: Optional[Type] = None):
        
        # Create MCP nodes
        from .mcp_nodes import create_mcp_flow
        flow = create_mcp_flow(name, instructions, server_configs, model, temperature, output_type)
        
        super().__init__(name, flow)
        
        self.server_configs = server_configs
        self.model = model
        self.output_type = output_type
        
        # Initialize MCP result formatter for consistent output formatting
        self.result_formatter = MCPResultFormatter(model=model, temperature=0.1)
        
        logger.info(f"Initialized MCPIntegratedAgent: {name} with {len(server_configs)} server configs")
    
    async def process(self, request: AIAgentRequest) -> Any:
        """Process request using MCP with proper async context management"""
        request_id = request.request_id or str(uuid.uuid4())
        
        with RequestContext(request_id=request_id, agent_name=self.name):
            try:
                log_agent_activity(self.name, "mcp_process_started", 
                                    request_id=request_id, request_context=request.context,
                                    server_count=len(self.server_configs))
                
                # Run the MCP flow
                shared = {
                    "request": request, 
                    "request_id": request_id,
                    "mcp_server_config": self.server_configs[0] if self.server_configs else None
                }
                await self.flow.run_async(shared)
                
                # Get the final result from shared data
                final_result = shared.get("final_result", {})
                
                # If no final result, format the tool result
                if not final_result and "tool_result" in shared:
                    final_result = self._format_mcp_result(shared["tool_result"], request)
                elif not final_result:
                    final_result = {"error": "No result from MCP flow", "success": False}
                
                # Apply AI-powered formatting if output_type is specified
                if final_result and self.output_type and hasattr(self, 'result_formatter'):
                    try:
                        agent_type = self._determine_agent_type()
                        if agent_type:
                            context = {
                                'query': request.context.get('query', ''),
                                'original_request': request.context
                            }
                            formatted_result = self.result_formatter.format_output(
                                final_result, agent_type, context
                            )
                            final_result = formatted_result
                            logger.info(f"Applied AI formatting for agent type: {agent_type}")
                    except Exception as e:
                        logger.warning(f"AI formatting failed, using original result: {e}")
                        # Continue with original result if formatting fails
                
                log_agent_activity(self.name, "mcp_process_completed", 
                                    request_id=request_id)
                
                # Return the final result from shared data
                return final_result
                
            except Exception as e:
                error_context = {
                    "request_id": request_id,
                    "operation": "mcp_agent_processing",
                    "server_count": len(self.server_configs)
                }
                log_agent_error(self.name, e, error_context)
                raise AgentProcessingError(f"Error in MCP agent {self.name}: {str(e)}") from e
    
    def _format_mcp_result(self, tool_result: Dict[str, Any], request: AIAgentRequest = None) -> Dict[str, Any]:
        """Format MCP tool execution result for return to user"""
        if tool_result.get("success", False):
            result_content = tool_result.get("result", "")
            
            # Format the result based on content
            formatted_result = {
                "data": result_content,
                "source": "mcp_tool",  
                "success": True,
                "agent_name": self.name
            }
            
            # Add request context if available
            if request and hasattr(request, 'context'):
                formatted_result["request_context"] = request.context
        else:
            formatted_result = {
                "error": tool_result.get("error", "Unknown error"),
                "source": "mcp_tool",
                "success": False,
                "agent_name": self.name
            }
        
        return formatted_result
    
    def _determine_agent_type(self) -> Optional[str]:
        """Determine the agent type for formatting based on agent name and capabilities"""
        agent_name_lower = self.name.lower()
        
        if "web" in agent_name_lower and "search" in agent_name_lower:
            return "web-search"
        elif "research" in agent_name_lower or "deep" in agent_name_lower:
            return "deep-research"
        elif "rag" in agent_name_lower or "document" in agent_name_lower:
            return "rag-query"
        elif "live" in agent_name_lower or "monitoring" in agent_name_lower:
            return "live-monitoring"
        else:
            # Check output type if available
            if self.output_type:
                if self.output_type == WebSearchResponse:
                    return "web-search"
                elif self.output_type == ResearchResponse:
                    return "deep-research"
                elif self.output_type == RAGResponse:
                    return "rag-query"
                elif self.output_type == LiveMonitoringResponse:
                    return "live-monitoring"
        
        # Default to None (no formatting)
        return None
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        info = super().get_agent_info()
        info.update({
            "type": "mcp_integrated",
            "server_configs": [config.get("name", f"{config.get('type', 'unknown')}_server") 
                              for config in self.server_configs],
            "model": self.model,
            "capabilities": ["mcp_integration", "external_tools", "real_time_data", "pocket_flow"]
        })
        return info


class ToolEnhancedAgent(PocketFlowAgent):
    """Agent with custom function tools using Pocket Flow"""
    
    def __init__(self, name: str, instructions: str, tools: List[Any],
                 model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7, output_type: Optional[Type] = None):
        
        # Create tool-enhanced flow
        from .tool_nodes import create_tool_flow
        flow = create_tool_flow(name, instructions, tools, model, temperature, output_type)
        
        super().__init__(name, flow)
        
        self.tools = tools
        self.model = model
        self.output_type = output_type
        
        logger.info(f"Initialized ToolEnhancedAgent: {name} with {len(tools)} tools")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        info = super().get_agent_info()
        info.update({
            "type": "tool_enhanced",
            "tools": [getattr(tool, '__name__', str(tool)) for tool in self.tools],
            "model": self.model,
            "capabilities": ["custom_tools", "function_calling", "complex_workflows", "pocket_flow"]
        })
        return info


class AgentFactory:
    """Factory for creating different types of Pocket Flow agents"""
    
    @staticmethod
    def create_structured_agent(name: str, instructions: str, output_model: Type, **kwargs) -> StructuredOutputAgent:
        """Create a structured output agent"""
        return StructuredOutputAgent(name, instructions, output_model, **kwargs)
    
    @staticmethod
    def create_mcp_agent(name: str, instructions: str, server_configs: List[Dict[str, Any]], **kwargs) -> MCPIntegratedAgent:
        """Create an MCP integrated agent"""
        return MCPIntegratedAgent(name, instructions, server_configs, **kwargs)
    
    @staticmethod
    def create_tool_agent(name: str, instructions: str, tools: List, **kwargs) -> ToolEnhancedAgent:
        """Create a tool enhanced agent"""
        return ToolEnhancedAgent(name, instructions, tools, **kwargs)


class AgentRegistry:
    """Registry for managing Pocket Flow agent instances"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgentInterface] = {}
        self.agent_configs: Dict[str, Dict] = {}
    
    def register_agent(self, agent_id: str, agent: BaseAgentInterface, config: Dict = None):
        """Register an agent instance"""
        self.agents[agent_id] = agent
        self.agent_configs[agent_id] = config or {}
        logger.info(f"Registered Pocket Flow agent: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgentInterface]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """List all registered agent IDs"""
        return list(self.agents.keys())
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent information"""
        agent = self.get_agent(agent_id)
        if agent:
            info = agent.get_agent_info()
            info.update(self.agent_configs.get(agent_id, {}))
            return info
        return None
    
    async def process_request(self, agent_id: str, request: AIAgentRequest) -> Any:
        """Process request through specified agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        return await agent.process(request)
    
    def list_agents_by_capability(self, capability: str) -> List[str]:
        """List agents with specific capability"""
        matching_agents = []
        for agent_id in self.agents:
            info = self.get_agent_info(agent_id)
            if info and capability in info.get("capabilities", []):
                matching_agents.append(agent_id)
        return matching_agents


# Global registry instance
agent_registry = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry"""
    return agent_registry


# System status functions
def get_system_status() -> Dict[str, Any]:
    """Get overall system status"""
    registry = get_agent_registry()
    return {
        "system_ready": True,
        "framework": "PocketFlow",
        "total_agents": len(registry.list_agents()),
        "available_agents": registry.list_agents(),
        "capabilities": {
            "structured_output": len(registry.list_agents_by_capability("structured_output")),
            "mcp_integration": len(registry.list_agents_by_capability("mcp_integration")),
            "custom_tools": len(registry.list_agents_by_capability("custom_tools"))
        }
    }


def check_agent_availability(agent_id: str) -> bool:
    """Check if specific agent is available"""
    registry = get_agent_registry()
    return agent_id in registry.list_agents()
