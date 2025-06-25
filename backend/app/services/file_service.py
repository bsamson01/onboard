import os
import uuid
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import magic
import aiofiles

from fastapi import UploadFile, HTTPException
from app.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """Service for handling secure file uploads and document management."""
    
    def __init__(self):
        """Initialize file service with upload configuration."""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS
        
        # Create upload directories
        self._ensure_upload_directories()
        
        # Supported MIME types
        self.allowed_mime_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg', 
            'png': 'image/png',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
    
    def _ensure_upload_directories(self):
        """Create necessary upload directories if they don't exist."""
        # Main upload directory
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories for different document types
        subdirs = ['documents', 'temp', 'processed', 'archived']
        for subdir in subdirs:
            (self.upload_dir / subdir).mkdir(exist_ok=True)
    
    async def upload_document(
        self, 
        file: UploadFile, 
        customer_id: str, 
        document_type: str,
        application_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload and validate a document file.
        
        Args:
            file: FastAPI UploadFile object
            customer_id: UUID of the customer
            document_type: Type of document being uploaded
            application_id: Optional application ID for linking
            
        Returns:
            Dictionary with file information and metadata
        """
        try:
            # Validate file before processing
            validation_result = await self._validate_upload_file(file)
            if not validation_result['valid']:
                raise HTTPException(status_code=400, detail=validation_result['error'])
            
            # Generate unique filename
            file_extension = self._get_file_extension(file.filename)
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Determine storage path
            file_path = self._get_storage_path(customer_id, document_type, unique_filename)
            
            # Save file to disk
            await self._save_file(file, file_path)
            
            # Calculate file hash for integrity
            file_hash = await self._calculate_file_hash(file_path)
            
            # Get file metadata
            file_stats = file_path.stat()
            mime_type = magic.from_file(str(file_path), mime=True)
            
            # Create file record
            file_record = {
                'id': str(uuid.uuid4()),
                'customer_id': customer_id,
                'application_id': application_id,
                'document_type': document_type,
                'original_filename': file.filename,
                'stored_filename': unique_filename,
                'file_path': str(file_path.relative_to(self.upload_dir)),
                'full_path': str(file_path),
                'file_size': file_stats.st_size,
                'mime_type': mime_type,
                'file_hash': file_hash,
                'upload_timestamp': datetime.utcnow(),
                'status': 'uploaded'
            }
            
            logger.info(f"Document uploaded successfully: {unique_filename} for customer {customer_id}")
            return file_record
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document upload failed: {str(e)}")
            raise HTTPException(status_code=500, detail="File upload failed")
    
    async def _validate_upload_file(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file before processing."""
        
        # Check file size
        if file.size and file.size > self.max_file_size:
            return {
                'valid': False,
                'error': f'File size ({file.size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)'
            }
        
        # Check filename
        if not file.filename:
            return {
                'valid': False,
                'error': 'No filename provided'
            }
        
        # Check file extension
        file_extension = self._get_file_extension(file.filename)
        if file_extension not in self.allowed_extensions:
            return {
                'valid': False,
                'error': f'File type "{file_extension}" not allowed. Allowed types: {", ".join(self.allowed_extensions)}'
            }
        
        # Read a small portion of the file to check MIME type
        try:
            file_content = await file.read(1024)  # Read first 1KB
            await file.seek(0)  # Reset file pointer
            
            # Check MIME type
            detected_mime = magic.from_buffer(file_content, mime=True)
            expected_mime = self.allowed_mime_types.get(file_extension)
            
            if expected_mime and detected_mime != expected_mime:
                # Allow some flexibility for MIME type detection
                if not self._is_compatible_mime_type(detected_mime, expected_mime):
                    return {
                        'valid': False,
                        'error': f'File content does not match extension. Expected: {expected_mime}, Got: {detected_mime}'
                    }
        
        except Exception as e:
            logger.warning(f"MIME type validation failed: {str(e)}")
            # Don't fail upload for MIME type issues, just log warning
        
        return {'valid': True}
    
    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        return Path(filename).suffix.lower().lstrip('.')
    
    def _get_storage_path(self, customer_id: str, document_type: str, filename: str) -> Path:
        """Generate storage path for uploaded file."""
        # Create customer-specific directory
        customer_dir = self.upload_dir / 'documents' / customer_id
        customer_dir.mkdir(parents=True, exist_ok=True)
        
        # Create document type subdirectory
        doc_type_dir = customer_dir / document_type
        doc_type_dir.mkdir(exist_ok=True)
        
        return doc_type_dir / filename
    
    async def _save_file(self, file: UploadFile, file_path: Path):
        """Save uploaded file to disk."""
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                # Read and write file in chunks to handle large files
                chunk_size = 8192  # 8KB chunks
                while chunk := await file.read(chunk_size):
                    await f.write(chunk)
                    
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {str(e)}")
            # Clean up partial file if it exists
            if file_path.exists():
                file_path.unlink()
            raise
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for integrity verification."""
        hash_sha256 = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            chunk_size = 8192
            while chunk := await f.read(chunk_size):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def _is_compatible_mime_type(self, detected: str, expected: str) -> bool:
        """Check if detected MIME type is compatible with expected type."""
        # Define compatible MIME type mappings
        compatible_types = {
            'application/pdf': ['application/pdf'],
            'image/jpeg': ['image/jpeg', 'image/pjpeg'],
            'image/png': ['image/png'],
            'application/msword': ['application/msword', 'application/vnd.ms-office'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/zip'  # DOCX files are ZIP archives
            ]
        }
        
        return detected in compatible_types.get(expected, [expected])
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a stored file."""
        try:
            full_path = self.upload_dir / file_path
            if not full_path.exists():
                return None
            
            file_stats = full_path.stat()
            mime_type = magic.from_file(str(full_path), mime=True)
            
            return {
                'file_path': file_path,
                'full_path': str(full_path),
                'file_size': file_stats.st_size,
                'mime_type': mime_type,
                'created_at': datetime.fromtimestamp(file_stats.st_ctime),
                'modified_at': datetime.fromtimestamp(file_stats.st_mtime),
                'exists': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {str(e)}")
            return None
    
    async def delete_file(self, file_path: str, archive: bool = True) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Relative path to the file
            archive: Whether to archive the file instead of deleting
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self.upload_dir / file_path
            if not full_path.exists():
                return False
            
            if archive:
                # Move to archived directory
                archive_dir = self.upload_dir / 'archived'
                archive_dir.mkdir(exist_ok=True)
                
                # Create unique archive filename
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                archive_filename = f"{timestamp}_{full_path.name}"
                archive_path = archive_dir / archive_filename
                
                shutil.move(str(full_path), str(archive_path))
                logger.info(f"File archived: {file_path} -> {archive_path}")
            else:
                # Permanently delete
                full_path.unlink()
                logger.info(f"File deleted: {file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    async def move_to_processed(self, file_path: str) -> Optional[str]:
        """Move file to processed directory after successful processing."""
        try:
            full_path = self.upload_dir / file_path
            if not full_path.exists():
                return None
            
            # Create processed directory structure
            processed_dir = self.upload_dir / 'processed'
            relative_dir = full_path.parent.relative_to(self.upload_dir)
            target_dir = processed_dir / relative_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file
            target_path = target_dir / full_path.name
            shutil.move(str(full_path), str(target_path))
            
            # Return new relative path
            new_relative_path = target_path.relative_to(self.upload_dir)
            logger.info(f"File moved to processed: {file_path} -> {new_relative_path}")
            
            return str(new_relative_path)
            
        except Exception as e:
            logger.error(f"Failed to move file to processed: {file_path}: {str(e)}")
            return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.upload_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'upload_directory': str(self.upload_dir),
                'max_file_size_mb': round(self.max_file_size / (1024 * 1024), 2),
                'allowed_extensions': self.allowed_extensions
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {
                'error': str(e),
                'upload_directory': str(self.upload_dir)
            }