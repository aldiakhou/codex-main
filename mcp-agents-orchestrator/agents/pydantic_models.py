# --- Imports ---
# Use try-except for agents SDK availability if needed, though backend likely requires it

from pydantic import BaseModel, Field
from typing import List, Optional


# --- Node Colors (Can be shared with frontend via API if needed) ---
NODE_COLORS = {
    "topic": "#FFD700", "main_idea": "#ADD8E6", "sub_idea": "#90EE90",
    "detail": "#FFA07A", "question": "#E6E6FA", "resource": "#F0E68C",
    "default": "#D3D3D3" # Default color for unknown types
}

# --- Pydantic Models (Copied/Adapted from original) ---
# Ensure these match what the agents expect and what the backend logic uses


class NodeIdea(BaseModel):
    label: str = Field(..., description="A short, concise label or title for the idea node (max 5-10 words). Should be unique among the generated ideas.")
    content: str = Field(default="", description="Description, explanation, or details about the idea (1-3 sentences).")
    tags: List[str] = Field(default_factory=list, description="List of 1-3 relevant single-word keywords or tags.")
    type: str = Field(default="sub_idea", description=f"Classification of the node. Suggested values: {list(NODE_COLORS.keys())}.")

class BrainstormingOutput(BaseModel):
    ideas: List[NodeIdea] = Field(..., description="A list of distinct brainstormed ideas, each suitable for a mind map node.")
    main_theme: str = Field(..., description="Main theme or topic that connects all the generated ideas.")

class ConnectionSuggestion(BaseModel):
    source_id: int = Field(..., description="The ID of the source node.")
    target_id: int = Field(..., description="The ID of the target node.")
    reason: str = Field(..., description="A brief explanation of why these nodes should be connected.")

class ConnectionSuggestionsOutput(BaseModel):
    suggestions: List[ConnectionSuggestion] = Field(..., description="A list of suggested connections between existing nodes.")

class TagSuggestion(BaseModel):
    tags: List[str] = Field(..., description="A list of 3-5 relevant tags for the node.")
    explanation: Optional[str] = Field(None, description="Optional explanation of why these tags are relevant.")

class SummaryOutput(BaseModel):
    summary: str = Field(..., description="A concise summary of the provided mind map content.")
    key_points: Optional[List[str]] = Field(None, description="Optional list of key takeaways or bullet points.")
