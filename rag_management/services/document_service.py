# app/rag_management/services/document_service.py
import os
import shutil
from typing import List, Optional, Dict, Any, Tuple
from fastapi import UploadFile, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import uuid
import logging
from datetime import datetime

from models.rag_models import Document, TextChunk
from rag_management.schemas import DocumentStatus
from rag_management.services.embedding_service import EmbeddingService
from rag_management.utils.text_processing import process_document, split_text_into_chunks
from config import settings

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService(db)
        self.upload_dir = os.path.join(settings.MEDIA_ROOT, "documents")
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def create_document(self, 
                             file: UploadFile, 
                             title: str, 
                             description: Optional[str] = None,
                             background_tasks: Optional[BackgroundTasks] = None) -> Document:
        """Upload and create a new document"""
        
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        file_path = os.path.join(self.upload_dir, f"{file_id}{file_extension}")
        
        # Save file to disk
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save file")
        
        # Create document record
        document = Document(
            id=file_id,
            title=title,
            description=description,
            file_name=file.filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            mime_type=file.content_type,
            status=DocumentStatus.PENDING,
            doc_metadata={
                "original_filename": file.filename,
                "content_type": file.content_type,
            }
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Process document in background
        if background_tasks:
            background_tasks.add_task(self.process_document, document.id)
        
        return document
    
    async def process_document(self, document_id: str) -> None:
        """Process a document by extracting text, chunking, and creating embeddings"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error(f"Document {document_id} not found")
            return
        
        try:
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            self.db.commit()
            
            # Extract text from document
            text, metadata = process_document(document.file_path)
            
            # Update document metadata
            document.doc_metadata = {**document.doc_metadata, **metadata}
            self.db.commit()
            
            # Split text into chunks
            chunks = split_text_into_chunks(text, metadata)
            
            # Store chunks
            for idx, chunk_data in enumerate(chunks):
                chunk = TextChunk(
                    document_id=document.id,
                    content=chunk_data['content'],
                    chunk_index=idx,
                    page_number=chunk_data.get('page_number'),
                    chunk_metadata=chunk_data.get('metadata', {})
                )
                self.db.add(chunk)
            
            self.db.commit()
            
            # Generate embeddings for chunks
            chunk_ids = [chunk.id for chunk in document.chunks]
            await self.embedding_service.generate_embeddings_for_chunks(chunk_ids)
            
            # Update status to indexed
            document.status = DocumentStatus.INDEXED
            document.updated_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            document.status = DocumentStatus.FAILED
            document.doc_metadata = {
                **document.doc_metadata, 
                "error": str(e),
                "error_time": datetime.utcnow().isoformat()
            }
            self.db.commit()
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID"""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_documents(self, skip: int = 0, limit: int = 100) -> Tuple[List[Document], int]:
        """Get a list of documents with pagination"""
        total = self.db.query(Document).count()
        documents = self.db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
        return documents, total
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document by ID"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            return False
        
        # Delete file if it exists
        if os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
            except Exception as e:
                logger.error(f"Failed to delete file {document.file_path}: {e}")
        
        # Delete document from database (chunks will be deleted due to cascade)
        self.db.delete(document)
        self.db.commit()
        
        return True