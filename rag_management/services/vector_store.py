# app/rag_management/services/vector_store.py
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from models.rag_models import TextChunk, EmbeddingStorage, Document
from rag_management.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(db)
    
    async def similarity_search(self, 
                               query: str, 
                               document_ids: Optional[List[str]] = None,
                               top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar chunks based on vector similarity
        
        Args:
            query: The search query
            document_ids: Optional list of document IDs to restrict search
            top_k: Number of results to return
            
        Returns:
            List of chunks with similarity scores
        """
        # Generate embedding for query
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Get all embeddings (with filters if document_ids provided)
        embedding_query = self.db.query(
            EmbeddingStorage,
            TextChunk,
            Document
        ).join(
            TextChunk, EmbeddingStorage.chunk_id == TextChunk.id
        ).join(
            Document, TextChunk.document_id == Document.id
        )
        
        if document_ids:
            embedding_query = embedding_query.filter(Document.id.in_(document_ids))
        
        results = embedding_query.all()
        
        if not results:
            logger.warning(f"No embeddings found for query: {query}")
            return []
        
        # Calculate similarity scores
        similarities = []
        for embedding_obj, chunk, document in results:
            embedding_vector = np.array(embedding_obj.vector).reshape(1, -1)
            query_vector = np.array(query_embedding).reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = float(cosine_similarity(embedding_vector, query_vector)[0][0])
            
            similarities.append({
                "chunk_id": chunk.id,
                "document_id": document.id,
                "document_title": document.title,
                "content": chunk.content,
                "similarity": similarity,
                "metadata": {
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "chunk_metadata": chunk.chunk_metadata,  # Changed from 'metadata' to 'chunk_metadata'
                    "document_metadata": document.doc_metadata  # Changed from 'metadata' to 'doc_metadata'
                }
            })
        
        # Sort by similarity (highest first) and take top_k
        sorted_results = sorted(similarities, key=lambda x: x["similarity"], reverse=True)[:top_k]
        
        return sorted_results
    
    async def hybrid_search(self,
                           query: str,
                           document_ids: Optional[List[str]] = None,
                           top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Combines vector search with keyword search for better results
        
        This is a placeholder for a more advanced hybrid search implementation.
        In a production system, you might want to use a specialized search engine
        like Elasticsearch or Typesense for this.
        """
        # For now, we'll just use the vector search
        return await self.similarity_search(query, document_ids, top_k)
    
    async def delete_embeddings_for_document(self, document_id: str) -> int:
        """Delete all embeddings associated with a document"""
        # Get all chunk IDs for the document
        chunk_ids = [chunk.id for chunk in 
                     self.db.query(TextChunk).filter(TextChunk.document_id == document_id).all()]
        
        if not chunk_ids:
            return 0
        
        # Delete all embeddings for those chunks
        deleted_count = self.db.query(EmbeddingStorage).filter(
            EmbeddingStorage.chunk_id.in_(chunk_ids)
        ).delete(synchronize_session=False)
        
        self.db.commit()
        
        return deleted_count