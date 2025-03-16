# models/rag_models.py
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Enum, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from database import Base
from rag_management.schemas import DocumentStatus

def generate_uuid():
    return str(uuid.uuid4())

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    doc_metadata = Column(JSON, nullable=True)  # Changed from 'metadata' to 'doc_metadata'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    chunks = relationship("TextChunk", back_populates="document", cascade="all, delete-orphan")
    
class TextChunk(Base):
    __tablename__ = "text_chunks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)
    chunk_metadata = Column(JSON, nullable=True)  # Changed from 'metadata' to 'chunk_metadata'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Vector embeddings (if stored in the same database)
    embedding_id = Column(String(36), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")

class EmbeddingStorage(Base):
    __tablename__ = "embeddings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    chunk_id = Column(String(36), ForeignKey("text_chunks.id", ondelete="CASCADE"), nullable=False)
    vector = Column(JSON, nullable=False)  # Can also use specific vector column if your DB supports it
    model_name = Column(String(100), nullable=False)
    dimension = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())