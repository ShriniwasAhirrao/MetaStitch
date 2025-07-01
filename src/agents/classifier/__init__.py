"""
Classifier Agent Package

This package contains all components related to file classification and pipeline routing.
The classifier agent is responsible for analyzing input files and determining the most
appropriate processing pipeline for optimal data extraction.

Components:
- ClassifierAgent: Main orchestrator for file classification
- FileDetector: Identifies file types and characteristics
- ContentAnalyzer: Analyzes file content structure and complexity
- PipelineRouter: Routes files to appropriate processing pipelines

Key Features:
- Intelligent file type detection
- Content complexity analysis
- Multi-format support
- Hybrid content detection
- Pipeline recommendation engine

Author: Unstructured Data Integration Team
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

# Import all classifier components
from .classifier_agent import ClassifierAgent
from .file_detector import FileDetector
from .content_analyzer import ContentAnalyzer
from .pipeline_router import PipelineRouter

# Classification constants
SUPPORTED_FILE_TYPES = [
    'txt', 'html', 'json', 'log', 
    'pdf', 'docx', 'doc',
    'png', 'jpg', 'jpeg', 'bmp', 'tiff'
]

PIPELINE_TYPES = [
    'text_pipeline',
    'ocr_pipeline', 
    'hybrid_pipeline'
]

# Content complexity levels
COMPLEXITY_LEVELS = {
    'SIMPLE': 1,      # Plain text, simple structure
    'MODERATE': 2,    # Some formatting, basic tables
    'COMPLEX': 3,     # Rich formatting, multiple elements
    'HYBRID': 4       # Mixed content types (text + images)
}

# Classification confidence thresholds
CONFIDENCE_THRESHOLDS = {
    'HIGH': 0.9,
    'MEDIUM': 0.7,
    'LOW': 0.5
}

# Default classification configuration
DEFAULT_CLASSIFIER_CONFIG = {
    'confidence_threshold': CONFIDENCE_THRESHOLDS['MEDIUM'],
    'enable_hybrid_detection': True,
    'max_file_size_mb': 100,
    'content_analysis_depth': 'MODERATE',
    'enable_caching': True,
    'cache_ttl_seconds': 3600
}

logger = logging.getLogger(__name__)


class ClassificationResult:
    """
    Represents the result of file classification.
    """
    
    def __init__(
        self,
        file_path: str,
        file_type: str,
        pipeline_type: str,
        confidence: float,
        complexity_level: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.file_path = file_path
        self.file_type = file_type
        self.pipeline_type = pipeline_type
        self.confidence = confidence
        self.complexity_level = complexity_level
        self.metadata = metadata or {}
        self.timestamp = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'file_path': self.file_path,
            'file_type': self.file_type,
            'pipeline_type': self.pipeline_type,
            'confidence': self.confidence,
            'complexity_level': self.complexity_level,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }
    
    def is_high_confidence(self) -> bool:
        """Check if classification has high confidence."""
        return self.confidence >= CONFIDENCE_THRESHOLDS['HIGH']
    
    def requires_hybrid_processing(self) -> bool:
        """Check if file requires hybrid processing."""
        return self.complexity_level == COMPLEXITY_LEVELS['HYBRID']


def create_classifier_pipeline(config: Optional[Dict[str, Any]] = None) -> Tuple[FileDetector, ContentAnalyzer, PipelineRouter]:
    """
    Create a complete classifier pipeline with all components.
    
    Args:
        config: Optional configuration for the pipeline components
        
    Returns:
        Tuple of (FileDetector, ContentAnalyzer, PipelineRouter)
    """
    config = config or DEFAULT_CLASSIFIER_CONFIG
    
    try:
        file_detector = FileDetector(config=config)
        content_analyzer = ContentAnalyzer(config=config)
        pipeline_router = PipelineRouter(config=config)
        
        logger.info("Classifier pipeline created successfully")
        return file_detector, content_analyzer, pipeline_router
        
    except Exception as e:
        logger.error(f"Failed to create classifier pipeline: {e}")
        raise


def validate_file_for_classification(file_path: str) -> bool:
    """
    Validate if a file can be processed by the classifier.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        True if file is valid for classification
    """
    import os
    from pathlib import Path
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return False
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        if file_ext not in SUPPORTED_FILE_TYPES:
            logger.warning(f"Unsupported file type: {file_ext}")
            return False
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > DEFAULT_CLASSIFIER_CONFIG['max_file_size_mb']:
            logger.warning(f"File too large: {file_size_mb}MB")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating file {file_path}: {e}")
        return False


def get_supported_formats() -> Dict[str, List[str]]:
    """
    Get dictionary of supported file formats by category.
    
    Returns:
        Dictionary mapping categories to supported file extensions
    """
    return {
        'text': ['txt', 'html', 'json', 'log'],
        'document': ['pdf', 'docx', 'doc'],
        'image': ['png', 'jpg', 'jpeg', 'bmp', 'tiff']
    }


def estimate_processing_time(file_path: str, file_type: str, complexity: int) -> float:
    """
    Estimate processing time for a file based on its characteristics.
    
    Args:
        file_path: Path to the file
        file_type: Type of the file
        complexity: Complexity level (1-4)
        
    Returns:
        Estimated processing time in seconds
    """
    import os
    
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        # Base processing time per MB by file type
        base_times = {
            'txt': 0.5, 'html': 1.0, 'json': 0.8, 'log': 0.7,
            'pdf': 3.0, 'docx': 2.0,
            'png': 5.0, 'jpg': 4.0, 'jpeg': 4.0
        }
        
        base_time = base_times.get(file_type, 2.0)
        complexity_multiplier = 1 + (complexity * 0.5)
        
        estimated_time = file_size_mb * base_time * complexity_multiplier
        
        # Minimum 1 second, maximum 300 seconds
        return max(1.0, min(300.0, estimated_time))
        
    except Exception as e:
        logger.warning(f"Could not estimate processing time: {e}")
        return 30.0  # Default estimate


# Package metadata
__version__ = "1.0.0"
__author__ = "Unstructured Data Integration Team"

# Export main classes and utilities
__all__ = [
    'ClassifierAgent',
    'FileDetector', 
    'ContentAnalyzer',
    'PipelineRouter',
    'ClassificationResult',
    'create_classifier_pipeline',
    'validate_file_for_classification',
    'get_supported_formats',
    'estimate_processing_time',
    'SUPPORTED_FILE_TYPES',
    'PIPELINE_TYPES',
    'COMPLEXITY_LEVELS',
    'CONFIDENCE_THRESHOLDS',
    'DEFAULT_CLASSIFIER_CONFIG'
]