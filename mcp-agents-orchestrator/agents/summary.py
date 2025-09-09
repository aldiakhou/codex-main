"""
Summary Agent implementation using Pocket Flow
Provides content summarization and synthesis capabilities
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .base import StructuredOutputAgent, AgentFactory
from ..core.models import AIAgentRequest
from ..core.logging import get_logger

logger = get_logger(__name__)

# Define output model for summaries
class SummaryOutput(BaseModel):
    """Structured output for summary results"""
    executive_summary: str = Field(description="High-level summary in 2-3 sentences")
    key_points: List[str] = Field(description="Main points from the content")
    detailed_summary: str = Field(description="Comprehensive summary preserving important details")
    themes: List[str] = Field(description="Major themes identified in the content")
    action_items: List[str] = Field(description="Any action items or next steps mentioned")
    important_quotes: List[str] = Field(description="Notable quotes or statements if any")


class SummaryAgent(StructuredOutputAgent):
    """AI Agent for content summarization using Pocket Flow"""
    
    def __init__(self):
        instructions = """You are an expert content summarizer capable of distilling complex information into clear, concise summaries.

CAPABILITIES:
- Summarize documents of any length
- Extract key points and themes
- Preserve critical information
- Adapt summary style to purpose
- Identify action items and decisions
- Highlight important quotes or statements

SUMMARIZATION FRAMEWORK:
1. CONTENT ANALYSIS:
   - Identify document structure and organization
   - Recognize main arguments and supporting points
   - Determine content type and purpose

2. KEY POINT EXTRACTION:
   - Identify central themes and messages
   - Extract supporting evidence and examples
   - Note important decisions or conclusions

3. SYNTHESIS:
   - Combine related points coherently
   - Maintain logical flow and structure
   - Preserve essential context

4. SUMMARY CREATION:
   - Create multi-level summaries (executive, detailed)
   - Ensure accuracy and completeness
   - Maintain original tone and intent

GUIDELINES:
1. Preserve the original meaning and intent
2. Prioritize information by importance
3. Maintain objectivity and neutrality
4. Use clear, accessible language
5. Include specific details when critical
6. Avoid adding interpretation unless requested

Summary Structure:
- Executive Summary: 2-3 sentence overview
- Key Points: Bulleted list of main ideas
- Detailed Summary: Comprehensive paragraph form
- Themes: Major topics covered
- Action Items: Any next steps mentioned
- Important Quotes: Notable statements"""

        super().__init__(
            name="Summary Agent",
            instructions=instructions,
            output_model=SummaryOutput,
            temperature=0.3  # Lower temperature for accurate summarization
        )
    
    def _build_input_text(self, request: AIAgentRequest) -> str:
        """Build specific input for summarization"""
        content = request.context.get('content', '')
        summary_type = request.context.get('summary_type', 'comprehensive')
        target_length = request.context.get('target_length', 'medium')
        focus_areas = request.context.get('focus_areas', [])
        
        input_text = f"""Summarization Request:

CONTENT TO SUMMARIZE:
{content}

SUMMARY TYPE: {summary_type}
TARGET LENGTH: {target_length}
FOCUS AREAS: {', '.join(focus_areas) if focus_areas else 'General summary'}

Additional Requirements: {request.context.get('additional_requirements', 'None')}

Task: Create a comprehensive summary of the provided content.

Approach:
1. Analyze the content structure and main ideas
2. Extract key points and supporting details
3. Identify themes and patterns
4. Create summaries at multiple levels of detail

Length Guidelines:
- short: Focus on absolute essentials only
- medium: Balance between brevity and completeness
- long: Preserve most important details

Ensure the summary accurately represents the original content."""
        
        return input_text


# Factory function for creating summary agent
def create_summary_agent() -> SummaryAgent:
    """Create a summary agent using Pocket Flow"""
    return SummaryAgent()
