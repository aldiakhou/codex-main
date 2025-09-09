"""
Brainstorming agent implementation using Pocket Flow
Maintains full compatibility with existing MindRobot architecture
"""
from typing import Dict, Any, List
from pocketflow import Node
from .base import StructuredOutputAgent, AgentFactory
from ..core.models import BrainstormRequest, BrainstormResponse

# Import the existing Pydantic models
try:
    from ..agents.pydantic_models import (
        BrainstormingOutput,  
        NODE_COLORS
    )
except ImportError:
    # Fallback models if original not available
    from pydantic import BaseModel, Field
    
    class BrainstormingOutput(BaseModel):
        ideas: List[Dict[str, Any]] = Field(description="Generated brainstorming ideas")
        main_theme: str = Field(description="Main theme identified")

    NODE_COLORS = {
        "idea": "#FFE6E6",
        "task": "#E6F3FF", 
        "research": "#E6FFE6",
        "goal": "#FFFFE6",
        "note": "#F0E6FF"
    }


class BrainstormNode(Node):
    """Custom node for brainstorming that extends StructuredOutputNode functionality"""
    
    def __init__(self, instructions: str, output_model, model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.7):
        super().__init__()
        self.instructions = instructions
        self.output_model = output_model
        self.model = model
        self.temperature = temperature
    
    def _build_input_text(self, request: BrainstormRequest) -> str:
        """Build specific input for brainstorming"""
        input_text = f"""Topic: {request.topic}
Number of ideas: {request.num_ideas}
Style: {request.style}

Context: {request.context if request.context else 'None provided'}

Generate brainstorming ideas for this topic. Ensure variety and depth.
Adapt the style as follows:
- creative: Focus on innovative, out-of-the-box ideas
- analytical: Focus on systematic, data-driven ideas  
- practical: Focus on actionable, implementable ideas

Return exactly what was requested in the proper format."""
        
        return input_text


class BrainstormAgent(StructuredOutputAgent):
    """AI Agent for brainstorming ideas using Pocket Flow with structured output"""
    
    def __init__(self):
        instructions = f"""You are an AI assistant helping brainstorm initial ideas for a mind map based on a given topic.

TASK: Generate a specified number of distinct, relevant, and concise ideas (suitable as node labels).

GUIDELINES:
1. Generate ideas that are concrete and actionable
2. Ensure ideas cover different aspects/angles of the topic  
3. Include both conventional and creative/unconventional ideas
4. Make connections between ideas when relevant
5. Organize ideas in a logical structure

For each idea, provide:
- A clear, concise label (suitable for mind map nodes)
- Optional brief description (content)
- 1-3 single-word tags for categorization
- Classify type from: {list(NODE_COLORS.keys())}
- Priority level: high, medium, or low

Ensure the generated labels are unique and avoid repetition.
Focus on creating ideas that would form a coherent, useful mind map structure."""

        # Initialize with StructuredOutputAgent
        super().__init__(
            name="Topic Brainstormer",
            instructions=instructions,
            output_model=BrainstormingOutput,
            temperature=0.7
        )
        
        # Override the node to use our custom BrainstormNode
        # This maintains the same functionality but with our specific build_input_text
        self.flow.start_node._build_input_text = self._build_input_text
    
    def _build_input_text(self, request) -> str:
        """Build specific input for brainstorming"""
        if isinstance(request, BrainstormRequest):
            input_text = f"""Topic: {request.topic}
Number of ideas: {request.num_ideas}
Style: {request.style}

Context: {request.context if request.context else 'None provided'}

Generate brainstorming ideas for this topic. Ensure variety and depth.
Adapt the style as follows:
- creative: Focus on innovative, out-of-the-box ideas
- analytical: Focus on systematic, data-driven ideas  
- practical: Focus on actionable, implementable ideas

Return exactly what was requested in the proper format."""
        else:
            # Handle AIAgentRequest format
            context = request.context if hasattr(request, 'context') else {}
            input_text = f"""Topic: {context.get('topic', 'General')}
Number of ideas: {context.get('num_ideas', '4-6')}
Style: {context.get('style', 'creative')}

Context: {context.get('additional_context', 'None provided')}

Generate brainstorming ideas for this topic."""
        
        return input_text


# Factory function for easy agent creation
def create_brainstorm_agent() -> BrainstormAgent:
    """Create a brainstorming agent using Pocket Flow"""
    return BrainstormAgent()
