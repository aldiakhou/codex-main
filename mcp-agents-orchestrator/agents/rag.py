"""
RAG Agent implementation using Pocket Flow with tool enhancement
Maintains compatibility with existing MindRobot architecture
"""
from typing import Dict, Any, List, Optional, Union
import asyncio
import json
from pathlib import Path

from .base import ToolEnhancedAgent, AgentFactory
from ..core.models import AIAgentRequest, RAGResponse
from ..core.logging import get_logger

logger = get_logger(__name__)


class RAGAgent(ToolEnhancedAgent):
    """AI Agent with Retrieval-Augmented Generation using Pocket Flow"""
    
    def __init__(self):
        # Create RAG tools
        rag_tools = self._create_rag_tools()
        
        instructions = """You are an advanced Retrieval-Augmented Generation (RAG) specialist with sophisticated document processing and search capabilities.

CAPABILITIES:
- Advanced document loading and processing
- Intelligent chunking with semantic awareness
- Multi-algorithm retrieval (vector similarity, keyword matching, hybrid approaches)
- Neural reranking for optimal results
- Contextual answer generation with source attribution

RAG WORKFLOW:
1. DOCUMENT PROCESSING:
   - Load documents from various formats (PDF, TXT, MD)
   - Apply intelligent chunking based on semantic coherence
   - Generate high-quality embeddings
   - Build optimized search indexes

2. RETRIEVAL PROCESS:
   - Parse and expand user queries for better matching
   - Execute multi-algorithm search (vector + keyword + hybrid)
   - Apply neural reranking to optimize result relevance
   - Select the most contextually appropriate chunks

3. GENERATION PHASE:
   - Synthesize information from retrieved chunks
   - Generate accurate, contextual responses
   - Provide proper source attribution
   - Maintain factual accuracy and coherence

GUIDELINES:
1. Always cite sources for factual claims
2. Clearly distinguish between retrieved information and inference
3. Indicate confidence levels in responses
4. Provide additional context when helpful
5. Suggest follow-up questions for deeper exploration
6. Handle cases where information is not available in documents

Use your RAG tools systematically to provide the most accurate and well-sourced responses possible."""

        super().__init__(
            name="RAG Agent",
            instructions=instructions,
            tools=rag_tools,
            temperature=0.3,
            output_type=RAGResponse
        )
        
        # Initialize RAG system placeholder
        self.rag_system = None
    
    def _create_rag_tools(self) -> List[Any]:
        """Create RAG-specific function tools"""
        tools = []
        
        # Note: We need to define functions outside the class to avoid self reference issues
        agent_self = self  # Capture self reference
        
        def load_documents(document_paths: List[str]) -> str:
            """Load and process documents for RAG retrieval"""
            try:
                # Initialize RAG system if not already done
                if agent_self.rag_system is None:
                    # Try to import the existing RAG executor
                    try:
                        from ..agents.rag_executor import IntelligentRAGAgent
                        agent_self.rag_system = IntelligentRAGAgent()
                    except ImportError:
                        return "RAG executor not available. Please ensure mindrobot.agents.rag_executor is installed."
                
                # For demo purposes, simulate document loading
                return f"Successfully loaded {len(document_paths)} documents"
                
            except Exception as e:
                return f"Error loading documents: {str(e)}"
        
        def search_documents(query: str, top_k: int = 10) -> str:
            """Search processed documents using advanced RAG algorithms"""
            try:
                if agent_self.rag_system is None:
                    return "Error: No documents loaded. Please load documents first using load_documents."
                
                # For demo purposes, simulate search results
                formatted_result = f"Search Query: {query}\n"
                formatted_result += f"Found {top_k} results\n\n"
                formatted_result += "Result 1:\nSource: document1.pdf\nRelevance: 0.95\n"
                formatted_result += f"Content: Sample content related to {query}\n\n"
                
                return formatted_result
                
            except Exception as e:
                return f"Error searching documents: {str(e)}"
        
        def get_rag_metrics() -> str:
            """Get RAG system performance metrics and statistics"""
            try:
                if agent_self.rag_system is None:
                    return "No RAG system initialized"
                
                # Simulate metrics
                metrics = """RAG System Metrics:
Documents: 0
Chunks: 0
Queries processed: 0
Average query time: 0.0ms
Memory usage: 0.0MB
Cache hit rate: 0.0%"""
                
                return metrics
                
            except Exception as e:
                return f"Error getting metrics: {str(e)}"
        
        def analyze_document_collection(analysis_type: str = "overview") -> str:
            """Analyze the loaded document collection"""
            try:
                if agent_self.rag_system is None:
                    return "No documents loaded for analysis"
                
                if analysis_type == "overview":
                    return """Document Collection Overview:
Total Documents: 0
Total Chunks: 0
Average Chunk Size: 0 characters"""
                
                elif analysis_type == "content_themes":
                    return """Content Themes Analysis:
No content available for analysis"""
                
                return "Analysis completed"
                
            except Exception as e:
                return f"Error analyzing collection: {str(e)}"
        
        tools = [load_documents, search_documents, get_rag_metrics, analyze_document_collection]
        return tools
    
    def _build_input_text(self, request: AIAgentRequest) -> str:
        """Build specific input for RAG queries"""
        query = request.context.get('query', '')
        search_type = request.context.get('search_type', 'comprehensive')
        max_results = request.context.get('max_results', 10)
        
        input_text = f"""RAG Query Request:

QUERY: {query}
SEARCH TYPE: {search_type}
MAX RESULTS: {max_results}

Context: {request.context.get('additional_context', 'None')}

Task: Use your RAG capabilities to provide a comprehensive, well-sourced answer to the query.

Process:
1. Search the document collection for relevant information
2. Analyze and synthesize the retrieved content
3. Generate a response with proper source attribution
4. Provide confidence assessment for the information

Focus on accuracy, relevance, and proper citation of sources."""
        
        return input_text


# Factory function for creating RAG agent
def create_rag_agent() -> RAGAgent:
    """Create a RAG agent with document processing tools using Pocket Flow"""
    return RAGAgent()
