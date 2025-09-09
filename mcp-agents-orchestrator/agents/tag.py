"""
Tag Agent implementation using Pocket Flow
Provides content tagging and categorization capabilities
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .base import StructuredOutputAgent, AgentFactory
from ..core.models import AIAgentRequest
from ..core.logging import get_logger

logger = get_logger(__name__)

# Define output model for tagging
class TagOutput(BaseModel):
    """Structured output for tagging results"""
    primary_tags: List[str] = Field(description="Main tags that best describe the content")
    secondary_tags: List[str] = Field(description="Additional relevant tags")
    categories: List[str] = Field(description="High-level categories the content belongs to")
    keywords: List[str] = Field(description="Important keywords extracted from content")
    sentiment: str = Field(description="Overall sentiment: positive, negative, neutral, or mixed")
    topic_relevance: Dict[str, float] = Field(description="Relevance scores for identified topics")
    suggested_labels: List[str] = Field(description="Suggested descriptive labels")


class TagAgent(StructuredOutputAgent):
    """AI Agent for content tagging and categorization using Pocket Flow"""
    
    def __init__(self):
        instructions = """You are an expert content tagger and categorizer capable of analyzing content and assigning appropriate tags, categories, and metadata.

CAPABILITIES:
- Generate relevant tags for any content type
- Categorize content into hierarchical taxonomies
- Extract keywords and key phrases
- Identify sentiment and tone
- Assess topic relevance
- Suggest descriptive labels

TAGGING FRAMEWORK:
1. CONTENT ANALYSIS:
   - Understand content type and purpose
   - Identify main topics and themes
   - Recognize entities and concepts

2. TAG GENERATION:
   - Create specific, descriptive tags
   - Ensure tags are actionable and searchable
   - Balance specificity with generality

3. CATEGORIZATION:
   - Assign to appropriate high-level categories
   - Consider multiple applicable categories
   - Maintain consistency in categorization

4. KEYWORD EXTRACTION:
   - Identify important terms and phrases
   - Focus on unique and distinguishing keywords
   - Include both general and specific terms

5. METADATA ENRICHMENT:
   - Assess sentiment and tone
   - Calculate topic relevance scores
   - Generate descriptive labels

GUIDELINES:
1. Use clear, consistent tag formatting
2. Avoid overly broad or vague tags
3. Include both general and specific tags
4. Consider user search behavior
5. Maintain objectivity in categorization
6. Ensure tags are actionable and useful

Tag Formatting Rules:
- Use lowercase for consistency
- Replace spaces with hyphens
- Keep tags concise (1-3 words)
- Avoid special characters
- Use singular forms when appropriate"""

        super().__init__(
            name="Tag Agent",
            instructions=instructions,
            output_model=TagOutput,
            temperature=0.3  # Lower temperature for consistent tagging
        )
    
    def _build_input_text(self, request: AIAgentRequest) -> str:
        """Build specific input for tagging"""
        content = request.context.get('content', '')
        tag_style = request.context.get('tag_style', 'comprehensive')
        existing_tags = request.context.get('existing_tags', [])
        taxonomy = request.context.get('taxonomy', 'general')
        
        input_text = f"""Tagging Request:

CONTENT TO TAG:
{content}

TAGGING STYLE: {tag_style}
TAXONOMY: {taxonomy}
EXISTING TAGS: {', '.join(existing_tags) if existing_tags else 'None'}

Additional Context: {request.context.get('additional_context', 'None')}

Task: Generate appropriate tags and metadata for the provided content.

Approach:
1. Analyze content to understand key topics
2. Generate relevant tags at different specificity levels
3. Assign appropriate categories
4. Extract important keywords
5. Assess sentiment and relevance

Tag Generation Guidelines:
- Primary tags: 3-5 most important tags
- Secondary tags: 5-10 additional relevant tags
- Categories: 2-4 high-level categories
- Keywords: 5-10 key terms from content

Ensure tags are useful for search and organization."""
        
        return input_text


# Factory function for creating tag agent
def create_tag_agent() -> TagAgent:
    """Create a tag agent using Pocket Flow"""
    return TagAgent()
