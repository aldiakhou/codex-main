"""
Expand Agent implementation using Pocket Flow
Provides node expansion capabilities for mind maps
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .base import StructuredOutputAgent, AgentFactory
from core.models import AIAgentRequest
from core.logging import get_logger

logger = get_logger(__name__)

# Define output model for node expansion
class ExpandOutput(BaseModel):
    """Structured output for node expansion results"""
    expanded_nodes: List[Dict[str, Any]] = Field(description="List of new nodes to add")
    connections: List[Dict[str, str]] = Field(description="Connections between nodes")
    expansion_strategy: str = Field(description="Strategy used for expansion")
    depth_recommendation: int = Field(description="Recommended depth for further expansion")
    
    class Config:
        json_schema_extra = {
            "example": {
                "expanded_nodes": [
                    {
                        "id": "node_1",
                        "label": "Machine Learning",
                        "content": "Subset of AI focused on algorithms that improve through experience",
                        "type": "concept",
                        "tags": ["ai", "technology"],
                        "priority": "high"
                    }
                ],
                "connections": [
                    {"from": "parent_node", "to": "node_1", "relationship": "subtopic"}
                ],
                "expansion_strategy": "hierarchical",
                "depth_recommendation": 2
            }
        }


class ExpandAgent(StructuredOutputAgent):
    """AI Agent for expanding mind map nodes using Pocket Flow"""
    
    def __init__(self):
        instructions = """You are a mind map expansion specialist capable of intelligently expanding nodes with relevant subtopics, related concepts, and connections.

CAPABILITIES:
- Expand nodes with relevant subtopics
- Identify related concepts and connections
- Maintain hierarchical structure
- Create cross-connections between ideas
- Suggest appropriate expansion depth
- Generate diverse expansion types

EXPANSION STRATEGIES:
1. HIERARCHICAL EXPANSION:
   - Break down concepts into components
   - Create logical subcategories
   - Maintain parent-child relationships

2. ASSOCIATIVE EXPANSION:
   - Find related concepts
   - Identify lateral connections
   - Create cross-domain links

3. FUNCTIONAL EXPANSION:
   - Add practical applications
   - Include examples and use cases
   - Connect to real-world scenarios

4. ANALYTICAL EXPANSION:
   - Add pros/cons branches
   - Include comparative elements
   - Create evaluation criteria

GUIDELINES:
1. Maintain coherent relationships between nodes
2. Ensure expanded nodes are at appropriate detail level
3. Avoid redundancy with existing nodes
4. Create meaningful connections
5. Balance breadth and depth of expansion
6. Consider user's context and goals

Node Properties:
- Label: Clear, concise node title
- Content: Brief description or details
- Type: concept, example, question, action, etc.
- Tags: Relevant categorization tags
- Priority: high, medium, or low
- Connections: Relationships to other nodes"""

        super().__init__(
            name="Expand Agent",
            instructions=instructions,
            output_model=ExpandOutput,
            temperature=0.6  # Moderate temperature for creative but coherent expansion
        )
    
    def _build_input_text(self, request: AIAgentRequest) -> str:
        """Build specific input for node expansion"""
        node_id = request.context.get('node_id', '')
        node_content = request.context.get('node_content', '')
        expansion_type = request.context.get('expansion_type', 'hierarchical')
        depth = request.context.get('depth', 1)
        existing_nodes = request.context.get('existing_nodes', [])
        mind_map_context = request.context.get('mind_map_context', {})
        
        input_text = f"""Node Expansion Request:

NODE TO EXPAND:
ID: {node_id}
Content: {node_content}

EXPANSION TYPE: {expansion_type}
EXPANSION DEPTH: {depth}

EXISTING NODES IN MIND MAP:
{chr(10).join([f"- {node}" for node in existing_nodes[:10]])}
{f"... and {len(existing_nodes) - 10} more" if len(existing_nodes) > 10 else ""}

MIND MAP CONTEXT:
Purpose: {mind_map_context.get('purpose', 'General knowledge mapping')}
Domain: {mind_map_context.get('domain', 'General')}
Target Audience: {mind_map_context.get('audience', 'General')}

Task: Expand the given node with relevant subtopics and connections.

Expansion Requirements:
1. Generate 3-7 new nodes based on expansion type
2. Create meaningful relationships between nodes
3. Ensure coherence with existing mind map structure
4. Vary node types for richness
5. Include practical and theoretical aspects

Expansion Types:
- hierarchical: Break down into components/subcategories
- related: Find associated concepts and ideas
- examples: Provide concrete examples and applications
- questions: Generate thought-provoking questions
- practical: Focus on applications and use cases"""
        
        return input_text


# Factory function for creating expand agent
def create_expand_agent() -> ExpandAgent:
    """Create an expand agent using Pocket Flow"""
    return ExpandAgent()
