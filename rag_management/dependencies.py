# app/rag_management/dependencies.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Generator, Optional

from app.database import get_db
from app.auth import get_current_user, User  # Assuming you have authentication
from app.rag_management.services.document_service import DocumentService

# Function to check document ownership/access
async def verify_document_access(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """
    Verify that the current user has access to the document
    
    For a multi-user system, you would check ownership or permissions here.
    This is a simple implementation that just verifies the document exists.
    """
    document_service = DocumentService(db)
    document = document_service.get_document(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # If you have a multi-user system, check access rights here
    # For example:
    # if document.owner_id != current_user.id and not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You don't have permission to access this document"
    #     )
    
    return True

# For rate limiting document uploads
class RateLimiter:
    def __init__(self, max_uploads_per_day: int = 20):
        self.max_uploads = max_uploads_per_day
        self.user_uploads = {}  # In a real system, use Redis or another persistent store
    
    async def check_rate_limit(
        self, 
        current_user: User = Depends(get_current_user)
    ) -> bool:
        """
        Check if user has exceeded rate limits
        """
        # Simple in-memory implementation
        # In production, use a persistent store with time windowing
        user_id = current_user.id
        
        if user_id not in self.user_uploads:
            self.user_uploads[user_id] = 0
        
        if self.user_uploads[user_id] >= self.max_uploads:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"You've exceeded the limit of {self.max_uploads} document uploads per day"
            )
        
        self.user_uploads[user_id] += 1
        return True

rate_limiter = RateLimiter()