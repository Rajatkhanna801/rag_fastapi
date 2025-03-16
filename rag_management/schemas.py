# app/rag_management/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"

class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    file_name: str
    file_size: int
    doc_metadata: Optional[Dict[str, Any]] = None  # Changed from 'metadata' to 'doc_metadata'
    
    class Config:
        orm_mode = True

class DocumentList(BaseModel):
    total: int
    documents: List[DocumentResponse]

class QueryRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    top_k: int = Field(5, ge=1, le=20)
    
class QueryResult(BaseModel):
    answer: str
    context: List[Dict[str, Any]]

class ChunkResponse(BaseModel):
    id: str
    text: str
    document_id: str
    metadata: Optional[Dict[str, Any]] = None  # This is not a DB column, so keep as is