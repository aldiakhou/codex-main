"""
Intelligent RAG Agent - Advanced Implementation
Following the agentic pattern with cutting-edge algorithms for scalable document processing
"""

import asyncio
import time
import hashlib
import json
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from collections import defaultdict
import heapq

import numpy as np
import faiss
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import torch
import psutil

from agents import Agent, Runner, set_tracing_disabled

# Disable tracing for privacy
set_tracing_disabled(True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Track performance metrics for optimization"""
    total_documents: int = 0
    total_chunks: int = 0
    index_build_time: float = 0.0
    avg_query_time: float = 0.0
    memory_usage_mb: float = 0.0
    queries_processed: int = 0
    cache_hit_rate: float = 0.0

class DocumentChunk(BaseModel):
    """Enhanced document chunk with advanced metadata"""
    id: str
    content: str
    source_document: str
    chunk_index: int
    start_char: int
    end_char: int
    embedding: Optional[List[float]] = None
    keywords: List[str] = Field(default_factory=list)
    semantic_density: float = 0.0
    importance_score: float = 0.0
    cluster_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class QueryContext(BaseModel):
    """Enhanced query context with intent analysis"""
    original_query: str
    expanded_queries: List[str] = Field(default_factory=list)
    query_type: str = "general"  # factual, analytical, comparison, etc.
    key_entities: List[str] = Field(default_factory=list)
    temporal_context: Optional[str] = None
    confidence: float = 1.0

class RetrievalResult(BaseModel):
    """Enhanced retrieval result with explanation"""
    chunk: DocumentChunk
    relevance_score: float
    retrieval_method: str
    explanation: str
    context_window: List[str] = Field(default_factory=list)

class IntelligentChunker:
    """Advanced chunking with semantic awareness and adaptive sizing"""
    
    def __init__(self, embedding_model: SentenceTransformer):
        self.embedding_model = embedding_model
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight for sentence analysis
    
    def adaptive_chunk(self, text: str, target_size: int = 800, max_size: int = 1200) -> List[Dict[str, Any]]:
        """Adaptive chunking based on semantic coherence"""
        sentences = self._split_into_sentences(text)
        if len(sentences) <= 1:
            return [{"text": text, "start": 0, "end": len(text), "density": 1.0}]
        
        # Calculate sentence embeddings
        sentence_embeddings = self.sentence_model.encode(sentences)
        
        # Calculate semantic coherence between adjacent sentences
        coherence_scores = []
        for i in range(len(sentences) - 1):
            similarity = cosine_similarity(
                sentence_embeddings[i].reshape(1, -1),
                sentence_embeddings[i + 1].reshape(1, -1)
            )[0][0]
            coherence_scores.append(similarity)
        
        # Find optimal split points
        chunks = []
        current_chunk = []
        current_size = 0
        start_pos = 0
        
        for i, sentence in enumerate(sentences):
            sentence_len = len(sentence)
            
            # Check if adding this sentence would exceed max size
            if current_size + sentence_len > max_size and current_chunk:
                # Finalize current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "start": start_pos,
                    "end": start_pos + len(chunk_text),
                    "density": self._calculate_semantic_density(current_chunk)
                })
                
                # Start new chunk
                current_chunk = [sentence]
                current_size = sentence_len
                start_pos = start_pos + len(chunk_text) + 1
            else:
                # Check semantic coherence before adding
                if (current_chunk and i < len(coherence_scores) and 
                    coherence_scores[i-1] < 0.3 and current_size > target_size):
                    # Low coherence and sufficient size - split here
                    chunk_text = " ".join(current_chunk)
                    chunks.append({
                        "text": chunk_text,
                        "start": start_pos,
                        "end": start_pos + len(chunk_text),
                        "density": self._calculate_semantic_density(current_chunk)
                    })
                    
                    current_chunk = [sentence]
                    current_size = sentence_len
                    start_pos = start_pos + len(chunk_text) + 1
                else:
                    current_chunk.append(sentence)
                    current_size += sentence_len
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "start": start_pos,
                "end": start_pos + len(chunk_text),
                "density": self._calculate_semantic_density(current_chunk)
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Intelligent sentence splitting"""
        import re
        # Enhanced sentence splitting with better handling of abbreviations
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_semantic_density(self, sentences: List[str]) -> float:
        """Calculate semantic density of text chunk"""
        if len(sentences) <= 1:
            return 1.0
        
        # Simple heuristic: count unique meaningful words vs total words
        all_words = " ".join(sentences).lower().split()
        meaningful_words = [w for w in all_words if len(w) > 3 and w.isalpha()]
        
        if not all_words:
            return 0.0
        
        unique_ratio = len(set(meaningful_words)) / len(all_words) if all_words else 0.0
        return min(unique_ratio * 2, 1.0)  # Scale to 0-1

class HierarchicalFaissIndex:
    """Hierarchical FAISS indexing for massive scalability"""
    
    def __init__(self, dimension: int, max_clusters: int = 1000):
        self.dimension = dimension
        self.max_clusters = max_clusters
        self.cluster_indexes = {}  # cluster_id -> faiss.Index
        self.cluster_centroids = None
        self.cluster_assignments = {}  # vector_id -> cluster_id
        self.global_index = None
        self.cluster_model = None
    
    def build_hierarchical_index(self, embeddings: np.ndarray, chunk_ids: List[str]):
        """Build hierarchical index with clustering"""
        logger.info(f"Building hierarchical index for {len(embeddings)} vectors")
        
        # Determine optimal number of clusters
        n_vectors = len(embeddings)
        n_clusters = min(max(n_vectors // 100, 1), self.max_clusters)
        
        if n_clusters > 1:
            # Cluster embeddings
            logger.info(f"Clustering into {n_clusters} clusters")
            self.cluster_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = self.cluster_model.fit_predict(embeddings)
            self.cluster_centroids = self.cluster_model.cluster_centers_
            
            # Build cluster-specific indexes
            for cluster_id in range(n_clusters):
                cluster_mask = cluster_labels == cluster_id
                cluster_embeddings = embeddings[cluster_mask]
                cluster_chunk_ids = [chunk_ids[i] for i in range(len(chunk_ids)) if cluster_mask[i]]
                
                if len(cluster_embeddings) > 0:
                    # Create HNSW index for this cluster
                    index = faiss.IndexHNSWFlat(self.dimension, 32)
                    index.hnsw.efConstruction = 200
                    index.add(cluster_embeddings.astype('float32'))
                    self.cluster_indexes[cluster_id] = {
                        'index': index,
                        'chunk_ids': cluster_chunk_ids
                    }
                    
                    # Store assignments
                    for i, chunk_id in enumerate(cluster_chunk_ids):
                        self.cluster_assignments[chunk_id] = cluster_id
            
            # Build global centroid index
            self.global_index = faiss.IndexFlatL2(self.dimension)
            self.global_index.add(self.cluster_centroids.astype('float32'))
        else:
            # Single cluster fallback
            index = faiss.IndexHNSWFlat(self.dimension, 32)
            index.hnsw.efConstruction = 200
            index.add(embeddings.astype('float32'))
            self.cluster_indexes[0] = {
                'index': index,
                'chunk_ids': chunk_ids
            }
    
    def search(self, query_embedding: np.ndarray, top_k: int = 10, search_clusters: int = 3) -> Tuple[List[str], List[float]]:
        """Hierarchical search"""
        if self.global_index is not None:
            # Find top clusters
            _, cluster_indices = self.global_index.search(
                query_embedding.reshape(1, -1).astype('float32'), 
                search_clusters
            )
            target_clusters = cluster_indices[0]
        else:
            target_clusters = list(self.cluster_indexes.keys())
        
        # Search within selected clusters
        all_results = []
        
        for cluster_id in target_clusters:
            if cluster_id in self.cluster_indexes:
                cluster_data = self.cluster_indexes[cluster_id]
                scores, indices = cluster_data['index'].search(
                    query_embedding.reshape(1, -1).astype('float32'),
                    min(top_k * 2, len(cluster_data['chunk_ids']))
                )
                
                for score, idx in zip(scores[0], indices[0]):
                    if idx < len(cluster_data['chunk_ids']):
                        all_results.append((cluster_data['chunk_ids'][idx], float(score)))
        
        # Sort and return top results
        all_results.sort(key=lambda x: x[1])
        top_results = all_results[:top_k]
        
        return [chunk_id for chunk_id, _ in top_results], [score for _, score in top_results]

class QueryExpander:
    """Intelligent query expansion and analysis"""
    
    def __init__(self):
        self.entity_patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Person names
            r'\b\d{4}\b',  # Years
            r'\b[A-Z]{2,}\b',  # Acronyms
        ]
    
    def expand_query(self, query: str) -> QueryContext:
        """Expand query with synonyms and related terms"""
        # Analyze query type
        query_type = self._classify_query(query)
        
        # Extract entities
        entities = self._extract_entities(query)
        
        # Generate expanded queries
        expanded = self._generate_expansions(query, query_type)
        
        return QueryContext(
            original_query=query,
            expanded_queries=expanded,
            query_type=query_type,
            key_entities=entities,
            confidence=1.0
        )
    
    def _classify_query(self, query: str) -> str:
        """Classify query type for better retrieval strategy"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what', 'define', 'explain']):
            return 'factual'
        elif any(word in query_lower for word in ['compare', 'difference', 'vs', 'versus']):
            return 'comparison'
        elif any(word in query_lower for word in ['how', 'steps', 'process']):
            return 'procedural'
        elif any(word in query_lower for word in ['why', 'reason', 'cause']):
            return 'analytical'
        else:
            return 'general'
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract key entities from query"""
        import re
        entities = []
        
        for pattern in self.entity_patterns:
            matches = re.findall(pattern, query)
            entities.extend(matches)
        
        # Extract potential technical terms (capitalized words)
        tech_terms = re.findall(r'\b[A-Z][a-z]*[A-Z][a-z]*\b', query)
        entities.extend(tech_terms)
        
        return list(set(entities))
    
    def _generate_expansions(self, query: str, query_type: str) -> List[str]:
        """Generate query expansions based on type"""
        expansions = [query]
        
        # Simple synonym expansion (in production, use word embeddings or thesaurus)
        synonyms = {
            'implement': ['create', 'build', 'develop', 'code'],
            'use': ['utilize', 'employ', 'apply'],
            'method': ['approach', 'technique', 'way'],
            'system': ['framework', 'architecture', 'solution']
        }
        
        words = query.lower().split()
        for word in words:
            if word in synonyms:
                for synonym in synonyms[word]:
                    expanded_query = query.lower().replace(word, synonym)
                    expansions.append(expanded_query)
        
        return expansions[:5]  # Limit expansions

class AdvancedReranker:
    """Neural reranking with context fusion"""
    
    def __init__(self):
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.context_window = 2  # Number of neighboring chunks to consider
    
    def rerank_with_context(self, 
                          query_context: QueryContext, 
                          results: List[RetrievalResult],
                          all_chunks: Dict[str, DocumentChunk]) -> List[RetrievalResult]:
        """Advanced reranking with contextual information"""
        if not results:
            return results
        
        enhanced_results = []
        
        for result in results:
            # Get contextual chunks (neighbors)
            context_chunks = self._get_context_chunks(result.chunk, all_chunks)
            
            # Create enhanced context
            full_context = result.chunk.content
            if context_chunks:
                full_context = " ".join([c.content for c in context_chunks]) + " " + full_context
            
            # Score with cross-encoder
            pairs = [(query_context.original_query, full_context)]
            cross_scores = self.cross_encoder.predict(pairs)
            
            # Calculate contextual bonus
            context_bonus = self._calculate_context_bonus(result.chunk, context_chunks)
            
            # Calculate query type alignment
            type_bonus = self._calculate_type_alignment(query_context.query_type, result.chunk)
            
            # Combined score
            final_score = float(cross_scores[0]) + context_bonus + type_bonus
            
            enhanced_result = RetrievalResult(
                chunk=result.chunk,
                relevance_score=final_score,
                retrieval_method=f"{result.retrieval_method}+reranked",
                explanation=f"Cross-encoder: {cross_scores[0]:.3f}, Context: {context_bonus:.3f}, Type: {type_bonus:.3f}",
                context_window=[c.content[:100] + "..." for c in context_chunks]
            )
            enhanced_results.append(enhanced_result)
        
        # Sort by final score
        enhanced_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return enhanced_results
    
    def _get_context_chunks(self, target_chunk: DocumentChunk, all_chunks: Dict[str, DocumentChunk]) -> List[DocumentChunk]:
        """Get neighboring chunks for context"""
        context_chunks = []
        
        # Find chunks from same document
        same_doc_chunks = [
            chunk for chunk in all_chunks.values() 
            if chunk.source_document == target_chunk.source_document
        ]
        
        # Sort by position
        same_doc_chunks.sort(key=lambda x: x.chunk_index)
        
        # Find neighbors
        target_idx = next((i for i, c in enumerate(same_doc_chunks) if c.id == target_chunk.id), -1)
        
        if target_idx >= 0:
            start_idx = max(0, target_idx - self.context_window)
            end_idx = min(len(same_doc_chunks), target_idx + self.context_window + 1)
            
            context_chunks = [
                same_doc_chunks[i] for i in range(start_idx, end_idx)
                if i != target_idx
            ]
        
        return context_chunks
    
    def _calculate_context_bonus(self, target_chunk: DocumentChunk, context_chunks: List[DocumentChunk]) -> float:
        """Calculate bonus based on contextual coherence"""
        if not context_chunks:
            return 0.0
        
        # Simple heuristic: bonus for high semantic density in context
        avg_density = sum(c.semantic_density for c in context_chunks) / len(context_chunks)
        return min(avg_density * 0.1, 0.05)  # Small bonus
    
    def _calculate_type_alignment(self, query_type: str, chunk: DocumentChunk) -> float:
        """Calculate bonus based on query type alignment"""
        type_keywords = {
            'factual': ['definition', 'is', 'means', 'refers to'],
            'comparison': ['versus', 'compared to', 'difference', 'similar'],
            'procedural': ['step', 'process', 'how to', 'method'],
            'analytical': ['because', 'due to', 'reason', 'cause']
        }
        
        if query_type in type_keywords:
            content_lower = chunk.content.lower()
            matches = sum(1 for keyword in type_keywords[query_type] if keyword in content_lower)
            return min(matches * 0.02, 0.05)  # Small bonus
        
        return 0.0

class IntelligentCache:
    """Advanced caching with LRU and semantic similarity"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = {}
        self.access_times = {}
        self.embedding_cache = {}
        self.similarity_threshold = 0.85
    
    def get(self, query: str, embedding: np.ndarray) -> Optional[Any]:
        """Get from cache with semantic similarity"""
        # Check exact match first
        if query in self.cache:
            self.access_times[query] = time.time()
            return self.cache[query]
        
        # Check semantic similarity
        best_match = None
        best_similarity = 0.0
        
        for cached_query, cached_embedding in self.embedding_cache.items():
            similarity = cosine_similarity(
                embedding.reshape(1, -1),
                cached_embedding.reshape(1, -1)
            )[0][0]
            
            if similarity > best_similarity and similarity > self.similarity_threshold:
                best_similarity = similarity
                best_match = cached_query
        
        if best_match and best_match in self.cache:
            self.access_times[best_match] = time.time()
            return self.cache[best_match]
        
        return None
    
    def set(self, query: str, embedding: np.ndarray, result: Any):
        """Set cache with LRU eviction"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_query = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_query]
            del self.access_times[oldest_query]
            del self.embedding_cache[oldest_query]
        
        self.cache[query] = result
        self.access_times[query] = time.time()
        self.embedding_cache[query] = embedding

class IntelligentRAGAgent:
    """Advanced RAG Agent with cutting-edge algorithms"""
    
    def __init__(self, 
                 embedding_model_name: str = "sentence-transformers/all-mpnet-base-v2",
                 max_documents: int = 100000,
                 cache_size: int = 1000):
        
        # Core components
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.chunker = IntelligentChunker(self.embedding_model)
        self.query_expander = QueryExpander()
        self.reranker = AdvancedReranker()
        self.cache = IntelligentCache(cache_size)
        
        # Storage
        self.chunks = {}  # chunk_id -> DocumentChunk
        self.faiss_index = None
        self.hierarchical_index = None
        self.bm25_index = None
        self.document_embeddings = {}
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.lock = threading.RLock()
        
        # Parallel processing
        self.max_workers = min(32, psutil.cpu_count())
        
        logger.info(f"Initialized IntelligentRAGAgent with {self.max_workers} workers")
    
    async def load_documents(self, document_paths: List[str]) -> Dict[str, Any]:
        """Load and process documents with parallel processing"""
        start_time = time.time()
        
        logger.info(f"Loading {len(document_paths)} documents...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Process documents in parallel
            futures = [
                executor.submit(self._process_single_document, doc_path, i)
                for i, doc_path in enumerate(document_paths)
            ]
            
            all_chunks = []
            for future in futures:
                try:
                    doc_chunks = future.result()
                    all_chunks.extend(doc_chunks)
                except Exception as e:
                    logger.error(f"Error processing document: {e}")
        
        # Store chunks
        for chunk in all_chunks:
            self.chunks[chunk.id] = chunk
        
        # Build indexes
        await self._build_indexes()
        
        processing_time = time.time() - start_time
        
        # Update metrics
        self.metrics.total_documents = len(document_paths)
        self.metrics.total_chunks = len(all_chunks)
        self.metrics.index_build_time = processing_time
        self.metrics.memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
        
        logger.info(f"Processed {len(all_chunks)} chunks in {processing_time:.2f}s")
        
        return {
            "total_documents": len(document_paths),
            "total_chunks": len(all_chunks),
            "processing_time": processing_time,
            "memory_usage_mb": self.metrics.memory_usage_mb
        }
    
    def _process_single_document(self, doc_path: str, doc_index: int) -> List[DocumentChunk]:
        """Process a single document"""
        try:
            # Load document content
            content = self._load_document_content(doc_path)
            
            # Adaptive chunking
            chunk_data = self.chunker.adaptive_chunk(content)
            
            chunks = []
            for i, chunk_info in enumerate(chunk_data):
                # Extract keywords
                keywords = self._extract_keywords(chunk_info["text"])
                
                # Calculate importance score
                importance = self._calculate_importance(chunk_info["text"], keywords)
                
                chunk = DocumentChunk(
                    id=f"doc{doc_index}_chunk{i}_{hashlib.md5(chunk_info['text'].encode()).hexdigest()[:8]}",
                    content=chunk_info["text"],
                    source_document=doc_path,
                    chunk_index=i,
                    start_char=chunk_info["start"],
                    end_char=chunk_info["end"],
                    keywords=keywords,
                    semantic_density=chunk_info["density"],
                    importance_score=importance,
                    metadata={
                        "document_index": doc_index,
                        "file_size": len(content),
                        "chunk_ratio": len(chunk_info["text"]) / len(content)
                    }
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing {doc_path}: {e}")
            return []
    
    def _load_document_content(self, doc_path: str) -> str:
        """Load document content with format detection"""
        path = Path(doc_path)
        
        try:
            if path.suffix.lower() == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif path.suffix.lower() == '.pdf':
                try:
                    import PyPDF2
                    with open(path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                        return text
                except ImportError:
                    logger.warning("PyPDF2 not available, skipping PDF")
                    return ""
            elif path.suffix.lower() in ['.md', '.markdown']:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # Try as text
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
                except UnicodeDecodeError:
                    with open(path, 'r', encoding='latin-1') as f:
                        return f.read()
        except Exception as e:
            logger.error(f"Error loading {doc_path}: {e}")
            return ""
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords using simple TF-IDF approach"""
        import re
        from collections import Counter
        
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'these', 'those', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Get most frequent words
        word_counts = Counter(filtered_words)
        keywords = [word for word, count in word_counts.most_common(10)]
        
        return keywords
    
    def _calculate_importance(self, text: str, keywords: List[str]) -> float:
        """Calculate importance score for chunk"""
        # Factors: length, keyword density, sentence complexity
        text_length = len(text)
        keyword_density = len(keywords) / max(len(text.split()), 1)
        
        # Sentence complexity (average sentence length)
        sentences = text.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # Normalize and combine
        length_score = min(text_length / 1000, 1.0)
        keyword_score = min(keyword_density * 10, 1.0)
        complexity_score = min(avg_sentence_length / 20, 1.0)
        
        return (length_score + keyword_score + complexity_score) / 3
    
    async def _build_indexes(self):
        """Build all indexes with optimization"""
        if not self.chunks:
            return
        
        logger.info("Building advanced indexes...")
        
        # Generate embeddings in batches
        chunk_list = list(self.chunks.values())
        texts = [chunk.content for chunk in chunk_list]
        
        # Batch embedding generation
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(
                batch_texts,
                show_progress_bar=True,
                normalize_embeddings=True
            )
            all_embeddings.extend(batch_embeddings)
        
        # Store embeddings in chunks
        for chunk, embedding in zip(chunk_list, all_embeddings):
            chunk.embedding = embedding.tolist()
        
        # Build hierarchical FAISS index
        embeddings_array = np.array(all_embeddings)
        chunk_ids = [chunk.id for chunk in chunk_list]
        
        self.hierarchical_index = HierarchicalFaissIndex(
            dimension=embeddings_array.shape[1],
            max_clusters=min(1000, len(chunk_list) // 10)
        )
        self.hierarchical_index.build_hierarchical_index(embeddings_array, chunk_ids)
        
        # Build BM25 index
        tokenized_docs = [chunk.content.lower().split() for chunk in chunk_list]
        self.bm25_index = BM25Okapi(tokenized_docs)
        
        logger.info("Indexes built successfully")
    
    async def search(self, query: str, top_k: int = 10, use_cache: bool = True) -> Dict[str, Any]:
        """Advanced search with multiple algorithms"""
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)[0]
        
        # Check cache
        if use_cache:
            cached_result = self.cache.get(query, query_embedding)
            if cached_result is not None:
                self.metrics.cache_hit_rate = (self.metrics.cache_hit_rate * self.metrics.queries_processed + 1) / (self.metrics.queries_processed + 1)
                return cached_result
        
        # Expand query
        query_context = self.query_expander.expand_query(query)
        
        # Multi-algorithm retrieval
        retrieval_results = await self._multi_algorithm_retrieval(query_context, query_embedding, top_k * 3)
        
        # Advanced reranking
        final_results = self.reranker.rerank_with_context(query_context, retrieval_results, self.chunks)
        
        # Limit to top_k
        final_results = final_results[:top_k]
        
        # Calculate metrics
        search_time = (time.time() - start_time) * 1000
        
        result = {
            "query": query,
            "query_context": query_context.dict(),
            "results": [r.dict() for r in final_results],
            "total_results": len(final_results),
            "search_time_ms": search_time,
            "performance_metrics": {
                "total_chunks_searched": len(self.chunks),
                "algorithms_used": ["hierarchical_vector", "bm25", "hybrid_fusion", "neural_reranking"],
                "memory_usage_mb": self.metrics.memory_usage_mb
            }
        }
        
        # Update metrics
        self.metrics.queries_processed += 1
        self.metrics.avg_query_time = (self.metrics.avg_query_time * (self.metrics.queries_processed - 1) + search_time) / self.metrics.queries_processed
        
        # Cache result
        if use_cache:
            self.cache.set(query, query_embedding, result)
        
        return result
    
    async def _multi_algorithm_retrieval(self, 
                                       query_context: QueryContext, 
                                       query_embedding: np.ndarray, 
                                       top_k: int) -> List[RetrievalResult]:
        """Multi-algorithm retrieval with fusion"""
        all_results = []
        
        # 1. Hierarchical vector search
        if self.hierarchical_index:
            chunk_ids, scores = self.hierarchical_index.search(query_embedding, top_k)
            for chunk_id, score in zip(chunk_ids, scores):
                if chunk_id in self.chunks:
                    result = RetrievalResult(
                        chunk=self.chunks[chunk_id],
                        relevance_score=1.0 / (1.0 + score),  # Convert distance to similarity
                        retrieval_method="hierarchical_vector",
                        explanation=f"Vector similarity: {1.0 / (1.0 + score):.3f}"
                    )
                    all_results.append(result)
        
        # 2. BM25 keyword search
        if self.bm25_index:
            tokenized_query = query_context.original_query.lower().split()
            bm25_scores = self.bm25_index.get_scores(tokenized_query)
            
            # Get top BM25 results
            chunk_list = list(self.chunks.values())
            top_bm25_indices = np.argsort(bm25_scores)[::-1][:top_k]
            
            for idx in top_bm25_indices:
                if idx < len(chunk_list):
                    chunk = chunk_list[idx]
                    result = RetrievalResult(
                        chunk=chunk,
                        relevance_score=float(bm25_scores[idx]),
                        retrieval_method="bm25",
                        explanation=f"BM25 score: {bm25_scores[idx]:.3f}"
                    )
                    all_results.append(result)
        
        # 3. Expanded query search
        for expanded_query in query_context.expanded_queries[1:3]:  # Use first 2 expansions
            expanded_embedding = self.embedding_model.encode([expanded_query], normalize_embeddings=True)[0]
            if self.hierarchical_index:
                chunk_ids, scores = self.hierarchical_index.search(expanded_embedding, top_k // 2)
                for chunk_id, score in zip(chunk_ids, scores):
                    if chunk_id in self.chunks:
                        result = RetrievalResult(
                            chunk=self.chunks[chunk_id],
                            relevance_score=0.8 * (1.0 / (1.0 + score)),  # Slightly lower weight
                            retrieval_method="expanded_query",
                            explanation=f"Expanded query match: {0.8 * (1.0 / (1.0 + score)):.3f}"
                        )
                        all_results.append(result)
        
        # 4. Importance-based boosting
        for result in all_results:
            importance_boost = result.chunk.importance_score * 0.1
            result.relevance_score += importance_boost
            result.explanation += f", Importance boost: {importance_boost:.3f}"
        
        # Remove duplicates and merge scores
        unique_results = {}
        for result in all_results:
            if result.chunk.id in unique_results:
                # Merge scores using maximum
                existing = unique_results[result.chunk.id]
                if result.relevance_score > existing.relevance_score:
                    unique_results[result.chunk.id] = result
            else:
                unique_results[result.chunk.id] = result
        
        # Sort by relevance
        final_results = list(unique_results.values())
        final_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return final_results[:top_k]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "total_documents": self.metrics.total_documents,
            "total_chunks": self.metrics.total_chunks,
            "index_build_time": self.metrics.index_build_time,
            "avg_query_time_ms": self.metrics.avg_query_time,
            "queries_processed": self.metrics.queries_processed,
            "cache_hit_rate": self.metrics.cache_hit_rate,
            "memory_usage_mb": self.metrics.memory_usage_mb,
            "cache_size": len(self.cache.cache),
            "cluster_count": len(self.hierarchical_index.cluster_indexes) if self.hierarchical_index else 0
        }
    
    def save_state(self, save_path: str):
        """Save RAG agent state"""
        save_dir = Path(save_path)
        save_dir.mkdir(exist_ok=True)
        
        # Save chunks
        with open(save_dir / "chunks.pkl", 'wb') as f:
            pickle.dump(self.chunks, f)
        
        # Save hierarchical index
        if self.hierarchical_index:
            with open(save_dir / "hierarchical_index.pkl", 'wb') as f:
                pickle.dump(self.hierarchical_index, f)
        
        # Save BM25 index
        if self.bm25_index:
            with open(save_dir / "bm25_index.pkl", 'wb') as f:
                pickle.dump(self.bm25_index, f)
        
        # Save metrics
        with open(save_dir / "metrics.json", 'w') as f:
            json.dump(self.get_metrics(), f, indent=2)
        
        logger.info(f"RAG agent state saved to {save_path}")
    
    def load_state(self, load_path: str):
        """Load RAG agent state"""
        load_dir = Path(load_path)
        
        # Load chunks
        with open(load_dir / "chunks.pkl", 'rb') as f:
            self.chunks = pickle.load(f)
        
        # Load hierarchical index
        hierarchical_path = load_dir / "hierarchical_index.pkl"
        if hierarchical_path.exists():
            with open(hierarchical_path, 'rb') as f:
                self.hierarchical_index = pickle.load(f)
        
        # Load BM25 index
        bm25_path = load_dir / "bm25_index.pkl"
        if bm25_path.exists():
            with open(bm25_path, 'rb') as f:
                self.bm25_index = pickle.load(f)
        
        logger.info(f"RAG agent state loaded from {load_path}")

# Agent Integration for OpenAI Agents SDK
intelligent_rag_agent_instance = IntelligentRAGAgent()

# Define the agent using OpenAI Agents SDK
intelligent_rag_agent = Agent(
    name="Intelligent RAG Agent",
    model="gpt-4o",
    instructions=(
        "You are an advanced RAG (Retrieval-Augmented Generation) agent with cutting-edge capabilities. "
        "You can process documents of any size and number using hierarchical indexing, adaptive chunking, "
        "and multi-algorithm retrieval. Your responses should be accurate, contextual, and well-sourced. "
        "When answering questions, always reference the specific documents and chunks you retrieved. "
        "Use your advanced algorithms to provide the most relevant and comprehensive answers."
    ),
    tools=[
        {
            "name": "load_documents",
            "description": "Load and process documents for RAG retrieval",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of document file paths to process"
                    }
                },
                "required": ["document_paths"]
            }
        },
        {
            "name": "search_documents", 
            "description": "Search processed documents using advanced RAG algorithms",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_metrics",
            "description": "Get performance metrics and statistics",
            "parameters": {"type": "object", "properties": {}}
        }
    ]
)

# Function implementations for the agent
async def load_documents(document_paths: List[str]) -> Dict[str, Any]:
    """Load documents function for the agent"""
    return await intelligent_rag_agent_instance.load_documents(document_paths)

async def search_documents(query: str, top_k: int = 10) -> Dict[str, Any]:
    """Search documents function for the agent"""
    return await intelligent_rag_agent_instance.search(query, top_k)

def get_metrics() -> Dict[str, Any]:
    """Get metrics function for the agent"""
    return intelligent_rag_agent_instance.get_metrics()