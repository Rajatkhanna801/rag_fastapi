# app/rag_management/utils/file_handlers.py
import os
import shutil
import logging
import mimetypes
import uuid
from typing import List, Dict, Any, Optional, BinaryIO
from fastapi import UploadFile, HTTPException
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)

# Configure allowed file types
ALLOWED_EXTENSIONS = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.csv': 'text/csv',
    '.json': 'application/json',
}

class FileManager:
    def __init__(self):
        self.upload_dir = Path(settings.MEDIA_ROOT) / "documents"
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_upload_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Save an uploaded file to disk
        
        Args:
            file: The uploaded file
            
        Returns:
            Dict containing file path and metadata
            
        Raises:
            HTTPException: If file type is not allowed or file saving fails
        """
        # Validate file type
        extension = os.path.splitext(file.filename)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS.keys())}"
            )
        
        # Generate a unique filename to avoid collisions
        unique_filename = f"{uuid.uuid4()}{extension}"
        file_path = self.upload_dir / unique_filename
        
        try:
            # Save file
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Get content type
        content_type = file.content_type or ALLOWED_EXTENSIONS.get(extension, 'application/octet-stream')
        
        return {
            "original_filename": file.filename,
            "stored_filename": unique_filename,
            "file_path": str(file_path),
            "file_size": file_size,
            "content_type": content_type,
            "extension": extension
        }
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from disk
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_stream(self, file_path: str) -> BinaryIO:
        """
        Get a file stream for downloading
        
        Args:
            file_path: Path to the file
            
        Returns:
            File object
            
        Raises:
            HTTPException: If file doesn't exist or can't be read
        """
        try:
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                raise HTTPException(status_code=404, detail="File not found")
                
            return path.open("rb")
        except Exception as e:
            logger.error(f"Error opening file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
    
    def get_file_content_type(self, file_path: str) -> str:
        """
        Get the content type of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Content type string
        """
        # Get file extension
        extension = os.path.splitext(file_path)[1].lower()
        
        # Try to get from our allowed extensions first
        if extension in ALLOWED_EXTENSIONS:
            return ALLOWED_EXTENSIONS[extension]
        
        # Fall back to mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type:
            return content_type
        
        # Default
        return 'application/octet-stream'
    
    def is_valid_file_type(self, filename: str) -> bool:
        """
        Check if a file has an allowed extension
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if allowed, False otherwise
        """
        extension = os.path.splitext(filename)[1].lower()
        return extension in ALLOWED_EXTENSIONS