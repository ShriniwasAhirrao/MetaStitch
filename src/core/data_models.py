# src/core/data_models.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime
import json

class FileType(Enum):
    """Supported file types"""
    HTML = "html"
    TXT = "txt"
    JSON = "json"
    LOG = "log"
    PDF = "pdf"
    DOCX = "docx"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    UNKNOWN = "unknown"

class PipelineType(Enum):
    """Available processing pipelines"""
    TEXT = "text"
    OCR = "ocr"
    HYBRID = "hybrid"

class ProcessingStatus(Enum):
    """Processing status indicators"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class FileMetadata:
    """File metadata structure"""
    filename: str
    file_path: str
    file_size: int
    file_type: FileType
    mime_type: str
    created_at: datetime = field(default_factory=datetime.now)
    checksum: Optional[str] = None
    encoding: Optional[str] = None

@dataclass
class ExtractionMetadata:
    """Metadata about the extraction process"""
    extraction_method: str
    confidence_score: float
    processing_time: float
    agent_version: str = "1.0.0"
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class StructuredElement:
    """Individual structured content element"""
    element_type: str  # paragraph, table, list, heading, etc.
    content: Union[str, Dict, List]
    position: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

@dataclass
class ExtractionResult:
    """Unified extraction result format"""
    metadata: Dict[str, Any]
    content: Dict[str, Any]
    extraction_info: ExtractionMetadata
    structured_elements: List[StructuredElement] = field(default_factory=list)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object {obj} is not JSON serializable")
        
        return json.dumps(self.__dict__, default=serialize_datetime, indent=2)

@dataclass
class ClassificationResult:
    """Result from file classification"""
    file_type: FileType
    recommended_pipeline: PipelineType
    confidence: float
    complexity_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_hybrid: bool = False

# Base exceptions
class AgentException(Exception):
    """Base exception for all agent errors"""
    pass

class FileProcessingError(AgentException):
    """Error during file processing"""
    pass

class ClassificationError(AgentException):
    """Error during file classification"""
    pass

class ExtractionError(AgentException):
    """Error during content extraction"""
    pass