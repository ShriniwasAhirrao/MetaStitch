"""
Core Package

This package contains the foundational components for the Unstructured Data Integration system.
It provides base classes, data models, utilities, constants, and exception handling that are
used throughout the entire application.

Core Components:
- BaseAgent: Abstract base class for all agents
- DataModels: Pydantic models for data validation and serialization
- Constants: System-wide constants and configuration values
- Utils: Common utility functions and helpers
- Exceptions: Custom exception classes for error handling

Key Features:
- Type-safe data models with validation
- Standardized agent interface
- Centralized configuration management
- Comprehensive error handling
- Utility functions for common operations

Author: Unstructured Data Integration Team
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional, Union, Type
import logging
from pathlib import Path

# Import core components
from .base_agent import BaseAgent
from .data_models import (
    FileMetadata,
    ExtractionResult,
    ClassificationResult,
    ProcessingStatus,
    AgentConfig,
    PipelineConfig,
    ValidationResult,
    StructuredData,
    ContentElement,
    EntityData,
    QualityMetrics
)
from .constants import (
    SUPPORTED_FILE_TYPES,
    PIPELINE_TYPES,
    AGENT_TYPES,
    STATUS_CODES,
    ERROR_CODES,
    QUALITY_THRESHOLDS,
    DEFAULT_CONFIG,
    FILE_SIZE_LIMITS,
    PROCESSING_TIMEOUTS
)
from .utils import (
    validate_file_path,
    get_file_metadata,
    calculate_file_hash,
    format_timestamp,
    sanitize_filename,
    create_directory_structure,
    merge_configurations,
    validate_json_schema,
    convert_bytes_to_mb,
    estimate_processing_time
)
from .exceptions import (
    UDIBaseException,
    FileProcessingError,
    ValidationError,
    ConfigurationError,
    PipelineError,
    AgentError,
    DataExtractionError,
    OCRError,
    StructuringError,
    QualityError
)

# Version and metadata
__version__ = "1.0.0"
__author__ = "Unstructured Data Integration Team"
__description__ = "Core components for unstructured data integration"

# Core logger
logger = logging.getLogger(__name__)

# System configuration
CORE_CONFIG = {
    'version': __version__,
    'max_concurrent_processes': 10,
    'default_timeout': 300,
    'enable_caching': True,
    'cache_ttl': 3600,
    'log_level': 'INFO',
    'metrics_enabled': True
}


class CoreManager:
    """
    Central manager for core system operations and configuration.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the core manager.
        
        Args:
            config: Optional configuration override
        """
        self.config = merge_configurations(CORE_CONFIG, config or {})
        self._setup_logging()
        self._validate_environment()
        
        logger.info(f"Core system initialized (v{__version__})")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _validate_environment(self):
        """Validate system environment and requirements."""
        try:
            # Check required directories exist
            required_dirs = ['data/input', 'data/output', 'data/cache', 'logs']
            for dir_path in required_dirs:
                create_directory_structure(dir_path)
            
            logger.debug("Environment validation completed")
            
        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            raise ConfigurationError(f"Environment setup failed: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information and status.
        
        Returns:
            Dictionary containing system information
        """
        return {
            'version': __version__,
            'config': self.config,
            'supported_file_types': SUPPORTED_FILE_TYPES,
            'available_pipelines': PIPELINE_TYPES,
            'agent_types': AGENT_TYPES
        }
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """
        Validate a file for processing.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            ValidationResult with validation status
        """
        try:
            # Basic file validation
            if not validate_file_path(file_path):
                return ValidationResult(
                    is_valid=False,
                    error_message="Invalid file path"
                )
            
            # Get file metadata
            metadata = get_file_metadata(file_path)
            
            # Check file size limits
            file_size_mb = convert_bytes_to_mb(metadata.file_size)
            max_size = FILE_SIZE_LIMITS.get(metadata.file_type, 100)
            
            if file_size_mb > max_size:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"File size ({file_size_mb}MB) exceeds limit ({max_size}MB)"
                )
            
            # Check file type support
            if metadata.file_type not in SUPPORTED_FILE_TYPES:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Unsupported file type: {metadata.file_type}"
                )
            
            return ValidationResult(
                is_valid=True,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=str(e)
            )


def initialize_core_system(config: Optional[Dict[str, Any]] = None) -> CoreManager:
    """
    Initialize the core system with optional configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Initialized CoreManager instance
    """
    return CoreManager(config)


def get_agent_class(agent_type: str) -> Type[BaseAgent]:
    """
    Get agent class by type name.
    
    Args:
        agent_type: Type of agent to retrieve
        
    Returns:
        Agent class
        
    Raises:
        ValueError: If agent type is not supported
    """
    if agent_type not in AGENT_TYPES:
        raise ValueError(f"Unsupported agent type: {agent_type}")
    
    # Dynamic import based on agent type
    if agent_type == 'classifier':
        from ..agents.classifier import ClassifierAgent
        return ClassifierAgent
    elif agent_type == 'text_extractor':
        from ..agents.text_extractor import TextExtractorAgent
        return TextExtractorAgent
    # Add other agent types as implemented
    else:
        raise ValueError(f"Agent type not yet implemented: {agent_type}")


def create_extraction_result(
    file_path: str,
    content: Dict[str, Any],
    metadata: Optional[FileMetadata] = None,
    quality_metrics: Optional[QualityMetrics] = None
) -> ExtractionResult:
    """
    Create a standardized extraction result.
    
    Args:
        file_path: Path to the processed file
        content: Extracted content
        metadata: Optional file metadata
        quality_metrics: Optional quality metrics
        
    Returns:
        ExtractionResult instance
    """
    if metadata is None:
        metadata = get_file_metadata(file_path)
    
    return ExtractionResult(
        file_path=file_path,
        content=content,
        metadata=metadata,
        quality_metrics=quality_metrics,
        processing_status=ProcessingStatus.COMPLETED
    )


def validate_configuration(config: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate configuration against a schema.
    
    Args:
        config: Configuration to validate
        schema: JSON schema for validation
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValidationError: If configuration is invalid
    """
    try:
        return validate_json_schema(config, schema)
    except Exception as e:
        raise ValidationError(f"Configuration validation failed: {e}")


# Global core manager instance
_core_manager: Optional[CoreManager] = None


def get_core_manager() -> CoreManager:
    """
    Get the global core manager instance.
    
    Returns:
        CoreManager instance
    """
    global _core_manager
    if _core_manager is None:
        _core_manager = initialize_core_system()
    return _core_manager


# Export all public components
__all__ = [
    # Core classes
    'BaseAgent',
    'CoreManager',
    
    # Data models
    'FileMetadata',
    'ExtractionResult', 
    'ClassificationResult',
    'ProcessingStatus',
    'AgentConfig',
    'PipelineConfig',
    'ValidationResult',
    'StructuredData',
    'ContentElement',
    'EntityData',
    'QualityMetrics',
    
    # Constants
    'SUPPORTED_FILE_TYPES',
    'PIPELINE_TYPES',
    'AGENT_TYPES',
    'STATUS_CODES',
    'ERROR_CODES',
    'QUALITY_THRESHOLDS',
    'DEFAULT_CONFIG',
    'FILE_SIZE_LIMITS',
    'PROCESSING_TIMEOUTS',
    
    # Utilities
    'validate_file_path',
    'get_file_metadata',
    'calculate_file_hash',
    'format_timestamp',
    'sanitize_filename',
    'create_directory_structure',
    'merge_configurations',
    'validate_json_schema',
    'convert_bytes_to_mb',
    'estimate_processing_time',
    
    # Exceptions
    'UDIBaseException',
    'FileProcessingError',
    'ValidationError',
    'ConfigurationError',
    'PipelineError',
    'AgentError',
    'DataExtractionError',
    'OCRError',
    'StructuringError',
    'QualityError',
    
    # Factory functions
    'initialize_core_system',
    'get_agent_class',
    'create_extraction_result',
    'validate_configuration',
    'get_core_manager',
    
    # Package metadata
    '__version__',
    '__author__',
    '__description__'
]

# Initialize logging for the package
logging.getLogger(__name__).info(f"Core package loaded (v{__version__})")