"""
MCP Result Formatter - AI-powered formatter for MCP tool outputs
Uses PocketFlow structured output pattern to ensure consistent response schemas
"""
import yaml
import logging
from typing import Dict, Any, Optional, Union, Type
from pydantic import BaseModel
from core.models import WebSearchResponse, ResearchResponse, RAGResponse, LiveMonitoringResponse
from .utils import call_llm

logger = logging.getLogger(__name__)


class MCPResultFormatter:
    """
    AI-powered formatter that converts raw MCP tool outputs to structured response models.
    Uses cost-effective LLM to ensure frontend always receives properly formatted data.
    """
    
    def __init__(self, model: str = "gpt-4.1-nano-2025-04-14", temperature: float = 0.1):
        """
        Initialize the MCP result formatter.
        
        Args:
            model: LLM model to use for formatting (cost-effective by default)
            temperature: Low temperature for consistent formatting
        """
        self.model = model
        self.temperature = temperature
        
    def format_output(self, raw_output: Any, agent_type: str, context: Optional[Dict[str, Any]] = None) -> Union[WebSearchResponse, ResearchResponse, RAGResponse, LiveMonitoringResponse]:
        """
        Main method to format raw MCP output based on agent type.
        
        Args:
            raw_output: Raw output from MCP tools (can be dict, string, etc.)
            agent_type: Type of agent ('web-search', 'deep-research', 'rag-query', 'live-monitoring')
            context: Optional context from the original request
            
        Returns:
            Properly formatted response model
        """
        try:
            if agent_type == 'web-search':
                return self.format_web_search(raw_output, context)
            elif agent_type == 'deep-research':
                return self.format_deep_research(raw_output, context)
            elif agent_type == 'rag-query':
                return self.format_rag_query(raw_output, context)
            elif agent_type == 'live-monitoring':
                return self.format_live_monitoring(raw_output, context)
            else:
                logger.warning(f"Unknown agent type: {agent_type}, returning raw output")
                return raw_output
                
        except Exception as e:
            logger.error(f"Error formatting {agent_type} output: {e}")
            # Return a fallback response
            return self._create_fallback_response(agent_type, raw_output, context, str(e))
    
    def format_web_search(self, raw_output: Any, context: Optional[Dict[str, Any]] = None) -> WebSearchResponse:
        """Format raw output to WebSearchResponse schema."""
        query = context.get('query', 'unknown query') if context else 'unknown query'
        
        # Build formatting prompt using PocketFlow structured output pattern
        prompt = f"""
You are a data formatter that converts raw search results into a specific YAML structure.

Raw MCP tool output:
{raw_output}

Original query: {query}

Your task is to format this into a proper web search response. Extract or infer the following information:
- Search results with title, url, snippet, and relevance_score (0.0-1.0)
- Total number of results
- Search execution time
- Related query suggestions

Output the result in this exact YAML format:

```yaml
query: "{query}"
results:
  - title: "Result title"
    url: "https://example.com"
    snippet: "Brief description of the result"
    relevance_score: 0.95
    source_type: "web"
total_results: 10
search_time: 1.23
search_engine: "mcp_fetch"
related_queries:
  - "related query 1"
  - "related query 2"
```

Important:
- If raw data is incomplete, create reasonable values
- Ensure relevance_score is between 0.0 and 1.0
- Keep snippets under 200 characters
- Include at least 1 result, maximum 20 results
"""

        try:
            response = call_llm(prompt, model=self.model, temperature=self.temperature)
            yaml_str = self._extract_yaml(response)
            structured_result = yaml.safe_load(yaml_str)
            
            # Validate and create WebSearchResponse
            return WebSearchResponse(**structured_result)
            
        except Exception as e:
            logger.error(f"Error in format_web_search: {e}")
            return self._create_fallback_web_search(query, raw_output)
    
    def format_deep_research(self, raw_output: Any, context: Optional[Dict[str, Any]] = None) -> ResearchResponse:
        """Format raw output to ResearchResponse schema."""
        research_topic = context.get('query', 'unknown topic') if context else 'unknown topic'
        
        prompt = f"""
You are a research data formatter that converts raw research content into a structured YAML format.

Raw MCP tool output:
{raw_output}

Research topic: {research_topic}

Format this into a comprehensive research response with these components:
- Executive summary (2-3 sentences)
- Detailed sections with sources
- Key findings (bullet points)
- Recommendations based on findings
- All sources used

Output in this exact YAML format:

```yaml
research_topic: "{research_topic}"
executive_summary: "Comprehensive summary of research findings in 2-3 sentences."
sections:
  - title: "Section 1 Title"
    content: "Detailed content for this section..."
    sources:
      - "https://source1.com"
      - "https://source2.com"
    confidence_level: "high"
  - title: "Section 2 Title"
    content: "More detailed content..."
    sources:
      - "https://source3.com"
    confidence_level: "medium"
key_findings:
  - "Key finding 1"
  - "Key finding 2"
  - "Key finding 3"
recommendations:
  - "Recommendation 1"
  - "Recommendation 2"
sources_used:
  - "https://source1.com"
  - "https://source2.com"
  - "https://source3.com"
research_depth: "comprehensive"
```

Important:
- Create meaningful sections that cover different aspects
- Include confidence levels: "high", "medium", or "low"
- Ensure sources are valid URLs or descriptive source names
- Provide actionable recommendations
"""

        try:
            response = call_llm(prompt, model=self.model, temperature=self.temperature)
            yaml_str = self._extract_yaml(response)
            structured_result = yaml.safe_load(yaml_str)
            
            return ResearchResponse(**structured_result)
            
        except Exception as e:
            logger.error(f"Error in format_deep_research: {e}")
            return self._create_fallback_research(research_topic, raw_output)
    
    def format_rag_query(self, raw_output: Any, context: Optional[Dict[str, Any]] = None) -> RAGResponse:
        """Format raw output to RAGResponse schema."""
        query = context.get('query', 'unknown query') if context else 'unknown query'
        
        prompt = f"""
You are a RAG (Retrieval-Augmented Generation) formatter that structures document query results.

Raw MCP tool output:
{raw_output}

Original query: {query}

Format this into a proper RAG response with retrieved document information:

```yaml
query: "{query}"
answer: "Comprehensive answer based on retrieved documents..."
sources:
  - "document1.pdf"
  - "document2.txt"
  - "document3.docx"
relevant_chunks:
  - "First relevant text chunk from documents..."
  - "Second relevant text chunk..."
  - "Third relevant text chunk..."
confidence_score: 0.87
document_info:
  - filename: "document1.pdf"
    chunk_count: 45
    last_updated: "2024-01-15T10:30:00Z"
  - filename: "document2.txt"
    chunk_count: 23
    last_updated: "2024-01-14T15:20:00Z"
retrieval_method: "semantic_search"
```

Important:
- Provide a comprehensive answer based on the documents
- Include specific text chunks that support the answer
- Confidence score should be between 0.0 and 1.0
- Include realistic document metadata
- Keep relevant_chunks under 500 characters each
"""

        try:
            response = call_llm(prompt, model=self.model, temperature=self.temperature)
            yaml_str = self._extract_yaml(response)
            structured_result = yaml.safe_load(yaml_str)
            
            return RAGResponse(**structured_result)
            
        except Exception as e:
            logger.error(f"Error in format_rag_query: {e}")
            return self._create_fallback_rag(query, raw_output)
    
    def format_live_monitoring(self, raw_output: Any, context: Optional[Dict[str, Any]] = None) -> LiveMonitoringResponse:
        """Format raw output to LiveMonitoringResponse schema."""
        monitoring_target = context.get('monitoring_target', 'unknown target') if context else 'unknown target'
        
        prompt = f"""
You are a live monitoring data formatter that structures real-time monitoring results.

Raw MCP tool output:
{raw_output}

Monitoring target: {monitoring_target}

Format this into a proper live monitoring response with real-time status and alerts:

```yaml
monitoring_target: "{monitoring_target}"
status: "active"
last_updated: "2024-01-15T10:30:00Z"
data_points:
  - source: "api_endpoint"
    value: 150
    timestamp: "2024-01-15T10:30:00Z"
    metric: "response_time_ms"
  - source: "database"
    value: 85
    timestamp: "2024-01-15T10:29:00Z"
    metric: "cpu_usage_percent"
alerts:
  - level: "warning"
    message: "Response time above threshold"
    timestamp: "2024-01-15T10:25:00Z"
    source: "performance_monitor"
  - level: "info"
    message: "System operating normally"
    timestamp: "2024-01-15T10:20:00Z"
    source: "health_check"
trends:
  - "Response times increasing over last hour"
  - "CPU usage stable"
  - "Memory usage within normal range"
next_check: "2024-01-15T10:35:00Z"
```

Important:
- Use ISO 8601 timestamp format
- Include realistic metric values and alerts
- Provide meaningful trend analysis
- Use appropriate alert levels: "info", "warning", "error", "critical"
- Include data sources and context
"""

        try:
            response = call_llm(prompt, model=self.model, temperature=self.temperature)
            yaml_str = self._extract_yaml(response)
            structured_result = yaml.safe_load(yaml_str)
            
            return LiveMonitoringResponse(**structured_result)
            
        except Exception as e:
            logger.error(f"Error in format_live_monitoring: {e}")
            return self._create_fallback_live_monitoring(monitoring_target, raw_output)
    
    def _extract_yaml(self, response: str) -> str:
        """Extract YAML content from LLM response using PocketFlow pattern."""
        try:
            # Look for YAML code blocks
            if "```yaml" in response:
                yaml_str = response.split("```yaml")[1].split("```")[0].strip()
                return yaml_str
            elif "```" in response:
                # Fallback: assume first code block is YAML
                yaml_str = response.split("```")[1].split("```")[0].strip()
                return yaml_str
            else:
                # No code blocks found, treat entire response as YAML
                return response.strip()
        except Exception as e:
            logger.error(f"Error extracting YAML: {e}")
            raise ValueError(f"Could not extract YAML from response: {response[:200]}...")
    
    def _create_fallback_response(self, agent_type: str, raw_output: Any, context: Optional[Dict[str, Any]], error: str) -> Any:
        """Create a fallback response when formatting fails."""
        if agent_type == 'web-search':
            query = context.get('query', 'unknown query') if context else 'unknown query'
            return self._create_fallback_web_search(query, raw_output)
        elif agent_type == 'deep-research':
            topic = context.get('query', 'unknown topic') if context else 'unknown topic'
            return self._create_fallback_research(topic, raw_output)
        elif agent_type == 'rag-query':
            query = context.get('query', 'unknown query') if context else 'unknown query'
            return self._create_fallback_rag(query, raw_output)
        elif agent_type == 'live-monitoring':
            monitoring_target = context.get('monitoring_target', 'unknown target') if context else 'unknown target'
            return self._create_fallback_live_monitoring(monitoring_target, raw_output)
        else:
            return raw_output
    
    def _create_fallback_web_search(self, query: str, raw_output: Any) -> WebSearchResponse:
        """Create fallback WebSearchResponse when formatting fails."""
        return WebSearchResponse(
            query=query,
            results=[
                {
                    "title": f"Results for: {query}",
                    "url": "https://example.com/search-results",
                    "snippet": f"Raw MCP output: {str(raw_output)[:150]}...",
                    "relevance_score": 0.5,
                    "source_type": "fallback"
                }
            ],
            total_results=1,
            search_time=0.0,
            search_engine="mcp_fallback",
            related_queries=[]
        )
    
    def _create_fallback_research(self, research_topic: str, raw_output: Any) -> ResearchResponse:
        """Create fallback ResearchResponse when formatting fails."""
        return ResearchResponse(
            research_topic=research_topic,
            executive_summary=f"Research conducted on {research_topic}. Raw data available for manual review.",
            sections=[
                {
                    "title": "Raw MCP Output",
                    "content": str(raw_output)[:1000] + "..." if len(str(raw_output)) > 1000 else str(raw_output),
                    "sources": ["mcp_tool_output"],
                    "confidence_level": "low"
                }
            ],
            key_findings=[f"Research topic: {research_topic}", "Raw MCP data available"],
            recommendations=["Review raw MCP output for detailed findings"],
            sources_used=["mcp_tool_output"],
            research_depth="basic"
        )
    
    def _create_fallback_rag(self, query: str, raw_output: Any) -> RAGResponse:
        """Create fallback RAGResponse when formatting fails."""
        return RAGResponse(
            query=query,
            answer=f"Query processed: {query}. Raw results available for review.",
            sources=["mcp_tool_output"],
            relevant_chunks=[str(raw_output)[:500] + "..." if len(str(raw_output)) > 500 else str(raw_output)],
            confidence_score=0.3,
            document_info=[],
            retrieval_method="mcp_fallback"
        )
    
    def _create_fallback_live_monitoring(self, monitoring_target: str, raw_output: Any) -> LiveMonitoringResponse:
        """Create fallback LiveMonitoringResponse when formatting fails."""
        from datetime import datetime
        
        current_time = datetime.utcnow().isoformat() + "Z"
        
        return LiveMonitoringResponse(
            monitoring_target=monitoring_target,
            status="unknown",
            last_updated=current_time,
            data_points=[
                {
                    "source": "mcp_tool_output",
                    "value": str(raw_output)[:100] + "..." if len(str(raw_output)) > 100 else str(raw_output),
                    "timestamp": current_time,
                    "metric": "raw_data"
                }
            ],
            alerts=[
                {
                    "level": "info",
                    "message": f"Raw monitoring data available for {monitoring_target}",
                    "timestamp": current_time,
                    "source": "mcp_fallback"
                }
            ],
            trends=[f"Raw MCP data captured for {monitoring_target}"],
            next_check=current_time
        )


def create_mcp_result_formatter(**kwargs) -> MCPResultFormatter:
    """Factory function to create MCPResultFormatter with default settings."""
    return MCPResultFormatter(**kwargs)
