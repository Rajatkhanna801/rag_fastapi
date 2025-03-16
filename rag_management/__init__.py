# app/rag_management/__init__.py
"""
RAG Management Module

This module provides functionality for implementing a Retrieval-Augmented Generation
(RAG) pipeline in a FastAPI application. It allows users to upload documents,
process them into searchable chunks, and query them using natural language.

Key components:
- Document management (upload, download, deletion)
- Text extraction and chunking
- Embedding generation
- Vector similarity search
- LLM-based question answering
"""

__version__ = "0.1.0"