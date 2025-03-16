# app/rag_management/services/embedding_service.py
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import numpy as np
import asyncio
import time

from models.rag_models import TextChunk, EmbeddingStorage, Document
from config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_model = self._load_embedding_model()
        self.embedding_dimension = 1536  # Default for OpenAI ada-002, adjust based on your model
        self.batch_size = 10  # Number of chunks to process at once
    
    def _load_embedding_model(self):
        """Load and return the embedding model"""
        # This is a placeholder. Implement based on your chosen embedding method
        # Example implementations:
        # 1. OpenAI embeddings
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            return client
        except ImportError:
            logger.warning("OpenAI package not installed, using fallback embedding model")
        
        # 2. Sentence Transformers fallback
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            return model
        except ImportError:
            logger.warning("SentenceTransformer package not installed")
        
        # 3. Bare minimum fallback
        class DummyEmbedder:
            def embed(self, text):
                # Generate random embedding for testing
                return np.random.randn(1536).astype(np.float32).tolist()
                
        logger.warning("Using dummy embedder - replace with real embedding model in production")
        return DummyEmbedder()
    
    async def generate_embeddings_for_chunks(self, chunk_ids: List[str]) -> None:
        """Generate embeddings for multiple chunks"""
        # Process in batches to avoid memory issues with large documents
        for i in range(0, len(chunk_ids), self.batch_size):
            batch_ids = chunk_ids[i:i+self.batch_size]
            chunks = self.db.query(TextChunk).filter(TextChunk.id.in_(batch_ids)).all()
            
            for chunk in chunks:
                embedding = await self.generate_embedding(chunk.content)
                
                # Store embedding
                embedding_record = EmbeddingStorage(
                    chunk_id=chunk.id,
                    vector=embedding,
                    model_name="openai-embedding-ada-002",  # Update with your model name
                    dimension=len(embedding)
                )
                
                self.db.add(embedding_record)
                
                # Update chunk with embedding ID
                chunk.embedding_id = embedding_record.id
            
            self.db.commit()
            
            # Avoid rate limits if using external API
            if i + self.batch_size < len(chunk_ids):
                await asyncio.sleep(0.5)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            # Implementation depends on the embedding model used
            # Example for OpenAI:
            if hasattr(self.embedding_model, 'embeddings'):
                response = self.embedding_model.embeddings.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                return response.data[0].embedding
            
            # Example for Sentence Transformers:
            elif hasattr(self.embedding_model, 'encode'):
                embedding = self.embedding_model.encode(text)
                return embedding.tolist()
            
            # Fallback:
            elif hasattr(self.embedding_model, 'embed'):
                return self.embedding_model.embed(text)
            
            else:
                # Last resort dummy embedding
                logger.warning("Using random embedding - model not properly configured")
                return np.random.randn(self.embedding_dimension).astype(np.float32).tolist()
                
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zeroed embedding in case of failure
            return [0.0] * self.embedding_dimension