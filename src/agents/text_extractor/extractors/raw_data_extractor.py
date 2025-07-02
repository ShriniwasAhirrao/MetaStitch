import asyncio
from pathlib import Path
import chardet

class RawDataExtractor:
    """
    Extracts raw text content from files with encoding detection and async support.
    """
    async def extract(self, file_path: str, file_metadata=None) -> str:
        """
        Extract raw text content from the given file path.
        
        Args:
            file_path: Path to the file to read
            file_metadata: Optional metadata (not used here)
        
        Returns:
            Raw text content as string
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._read_file, file_path)
    
    def _read_file(self, file_path: str) -> str:
        """
        Synchronous file reading with encoding detection.
        """
        path = Path(file_path)
        raw_data = path.read_bytes()
        
        detected = chardet.detect(raw_data)
        encoding = detected.get('encoding', 'utf-8')
        
        try:
            return raw_data.decode(encoding)
        except (UnicodeDecodeError, TypeError):
            # Fallback encodings
            for enc in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
                try:
                    return raw_data.decode(enc)
                except Exception:
                    continue
            # Final fallback with replacement
            return raw_data.decode('utf-8', errors='replace')
