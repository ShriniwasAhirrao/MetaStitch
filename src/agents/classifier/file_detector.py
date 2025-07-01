# src/agents/classifier/file_detector.py
import os
import mimetypes
import magic
from pathlib import Path
from typing import Optional
import hashlib
from datetime import datetime

from ...core.data_models import FileMetadata, FileType, FileProcessingError

class FileDetector:
    """Detects file types and extracts basic metadata"""
    
    def __init__(self):
        self.supported_extensions = {
            '.html': FileType.HTML,
            '.htm': FileType.HTML,
            '.txt': FileType.TXT,
            '.json': FileType.JSON,
            '.log': FileType.LOG,
            '.pdf': FileType.PDF,
            '.docx': FileType.DOCX,
            '.png': FileType.PNG,
            '.jpg': FileType.JPG,
            '.jpeg': FileType.JPEG,
        }
    
    async def detect_file_type(self, file_path: str) -> FileMetadata:
        """
        Detect file type and extract metadata
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileMetadata object with file information
        """
        try:
            path_obj = Path(file_path)
            
            # Basic file info
            file_size = os.path.getsize(file_path)
            filename = path_obj.name
            
            # Detect file type
            file_type = self._detect_file_type_by_extension(path_obj.suffix.lower())
            
            # Get MIME type
            mime_type = self._get_mime_type(file_path)
            
            # Calculate checksum
            checksum = self._calculate_checksum(file_path)
            
            # Detect encoding for text files
            encoding = None
            if file_type in [FileType.TXT, FileType.HTML, FileType.JSON, FileType.LOG]:
                encoding = self._detect_encoding(file_path)
            
            return FileMetadata(
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                mime_type=mime_type,
                checksum=checksum,
                encoding=encoding
            )
            
        except Exception as e:
            raise FileProcessingError(f"Failed to detect file type for {file_path}: {str(e)}")
    
    def _detect_file_type_by_extension(self, extension: str) -> FileType:
        """Detect file type by extension"""
        return self.supported_extensions.get(extension, FileType.UNKNOWN)
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type of the file"""
        try:
            # Try using python-magic for more accurate detection
            mime_type = magic.from_file(file_path, mime=True)
            return mime_type
        except:
            # Fallback to mimetypes module
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or 'application/octet-stream'
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of the file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _detect_encoding(self, file_path: str) -> Optional[str]:
        """Detect text encoding of the file"""
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                return result.get('encoding', 'utf-8')
        except ImportError:
            # Fallback if chardet is not available
            return 'utf-8'
        except Exception:
            return 'utf-8'
    
    def is_supported_file(self, file_path: str) -> bool:
        """Check if file type is supported"""
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_extensions
    
    def get_file_info_summary(self, file_metadata: FileMetadata) -> dict:
        """Get a summary of file information"""
        return {
            'filename': file_metadata.filename,
            'size_mb': round(file_metadata.file_size / (1024 * 1024), 2),
            'type': file_metadata.file_type.value,
            'mime_type': file_metadata.mime_type,
            'encoding': file_metadata.encoding
        }