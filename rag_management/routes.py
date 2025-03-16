# app/rag_management/routes.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from database import get_db
from rag_management.schemas import (
    DocumentCreate, 
    DocumentResponse, 
    DocumentList, 
    QueryRequest, 
    QueryResult,
    ChunkResponse
)
from rag_management.services.document_service import DocumentService
from rag_management.services.llm_service import LLMService
from rag_management.utils.file_handlers import FileManager


router = APIRouter(prefix="/rag-mngmnt", tags=["Rag LLM"])
file_manager = FileManager()


@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a document for RAG processing
    """
    # Validate file type
    if not file_manager.is_valid_file_type(file.filename):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Supported formats: PDF, DOCX, TXT, MD"
        )
    
    document_service = DocumentService(db)
    document = await document_service.create_document(
        file=file,
        title=title,
        description=description,
        background_tasks=background_tasks
    )
    return document


@router.get("/documents", response_model=DocumentList)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all uploaded documents
    """
    document_service = DocumentService(db)
    documents, total = document_service.get_documents(skip=skip, limit=limit)
    
    return {
        "total": total,
        "documents": documents
    }

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get document details by ID
    """
    document_service = DocumentService(db)
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document

@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document and all associated data
    """
    document_service = DocumentService(db)
    result = document_service.delete_document(document_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return None

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Download the original document file
    """
    document_service = DocumentService(db)
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")
    
    content_type = file_manager.get_file_content_type(document.file_path)
    
    file_stream = file_manager.get_file_stream(document.file_path)
    
    return StreamingResponse(
        file_stream,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment; filename={document.file_name}"
        }
    )

@router.get("/documents/{document_id}/chunks", response_model=List[ChunkResponse])
async def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all text chunks for a document
    """
    document_service = DocumentService(db)
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Format chunks for response
    chunks = []
    for chunk in document.chunks:
        chunk_metadata = chunk.chunk_metadata if chunk.chunk_metadata else {}
        chunks.append({
            "id": chunk.id,
            "text": chunk.content,
            "document_id": document_id,
            "metadata": {
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                **chunk_metadata
            }
        })
    return chunks


@router.post("/query", response_model=QueryResult)
async def query_documents(
    query_request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query documents using RAG
    """
    llm_service = LLMService(db)
    result = await llm_service.answer_query(
        query=query_request.query,
        document_ids=query_request.document_ids,
        top_k=10
    )
    return result


@router.post("/reindex/{document_id}", response_model=DocumentResponse)
async def reindex_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Force reprocessing and reindexing of a document
    """
    document_service = DocumentService(db)
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Start reindexing in the background
    background_tasks.add_task(document_service.process_document, document_id)
    
    return document
