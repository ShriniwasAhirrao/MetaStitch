"""
Constants Module

This module contains all system-wide constants, configuration values, and enumerations
used throughout the Unstructured Data Integration system.

Categories:
- File Types and Formats
- Pipeline and Agent Types
- Status and Error Codes
- Quality Thresholds and Metrics
- Processing Limits and Timeouts
- Default Configurations

Author: Unstructured Data Integration Team
Version: 1.0.0
"""

from enum import Enum
from typing import Dict, Any, List, Set
import os

# =============================================================================
# FILE TYPES AND FORMATS
# =============================================================================

# Supported input file extensions
SUPPORTED_FILE_TYPES: Set[str] = {
    'txt', 'html', 'json', 'log',           # Text files
    'pdf', 'docx', 'doc',                   # Document files
    'png', 'jpg', 'jpeg', 'bmp', 'tiff',   # Image files
    'csv', 'xlsx', 'xls'                    # Data files (future support)
}

# File type categories
FILE_CATEGORIES: Dict[str, List[str]] = {
    'text': ['txt', 'html', 'json', 'log'],
    'document': ['pdf', 'docx', 'doc'],
    'image': ['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
    'data': ['csv', 'xlsx', 'xls']
}

# MIME type mappings
MIME_TYPE_MAPPING: Dict[str, str] = {
    'txt': 'text/plain',
    'html': 'text/html',
    'json': 'application/json',
    'log': 'text/plain',
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'doc': 'application/msword',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'bmp': 'image/bmp',
    'tiff': 'image/tiff',
    'csv': 'text/csv',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'xls': 'application/vnd.ms-excel'
}

# =============================================================================
# PIPELINE AND AGENT TYPES
# =============================================================================

# Available processing pipelines
PIPELINE_TYPES: List[str] = [
    'text_pipeline',
    'ocr_pipeline',
    'hybrid_pipeline'
]

# Agent types in the system
AGENT_TYPES: List[str] = [
    'classifier',
    'text_extractor',
    'ocr_extractor',
    'hybrid_extractor',
    'context_analysis',
    'structured_agent'
]

# Pipeline to agent mapping
PIPELINE_AGENT_MAPPING: Dict[str, List[str]] = {
    'text_pipeline': ['classifier', 'text_extractor', 'context_analysis', 'structured_agent'],
    'ocr_pipeline': ['classifier', 'ocr_extractor', 'context_analysis', 'structured_agent'],
    'hybrid_pipeline': ['classifier', 'hybrid_extractor', 'context_analysis', 'structured_agent']
}

# =============================================================================
# STATUS AND ERROR CODES
# =============================================================================

class ProcessingStatus(Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class QualityLevel(Enum):
    """Data quality level enumeration."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNUSABLE = "unusable"

# Status codes for API responses
STATUS_CODES: Dict[str, int] = {
    'SUCCESS': 200,
    'CREATED': 201,
    'ACCEPTED': 202,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'CONFLICT': 409,
    'UNPROCESSABLE_ENTITY': 422,
    'INTERNAL_SERVER_ERROR': 500,
    'SERVICE_UNAVAILABLE': 503
}

# Error codes for different error types
ERROR_CODES: Dict[str, str] = {
    'FILE_NOT_FOUND': 'E001',
    'UNSUPPORTED_FORMAT': 'E002',
    'FILE_TOO_LARGE': 'E003',
    'INVALID_CONTENT': 'E004',
    'PROCESSING_TIMEOUT': 'E005',
    'EXTRACTION_FAILED': 'E006',
    'VALIDATION_FAILED': 'E007',
    'CLASSIFICATION_FAILED': 'E008',
    'OCR_FAILED': 'E009',
    'CONTEXT_ANALYSIS_FAILED': 'E010',
    'STRUCTURING_FAILED': 'E011',
    'CONFIGURATION_ERROR': 'E012',
    'AGENT_ERROR': 'E013',
    'PIPELINE_ERROR': 'E014',
    'QUALITY_CHECK_FAILED': 'E015'
}

# =============================================================================
# QUALITY THRESHOLDS AND METRICS
# =============================================================================

# Quality score thresholds (0.0 - 1.0)
QUALITY_THRESHOLDS: Dict[str, float] = {
    'EXCELLENT': 0.95,
    'GOOD': 0.80,
    'FAIR': 0.60,
    'POOR': 0.40,
    'UNUSABLE': 0.20
}

# Confidence thresholds for different operations
CONFIDENCE_THRESHOLDS: Dict[str, float] = {
    'CLASSIFICATION_HIGH': 0.90,
    'CLASSIFICATION_MEDIUM': 0.70,
    'CLASSIFICATION_LOW': 0.50,
    'OCR_HIGH': 0.85,
    'OCR_MEDIUM': 0.65,
    'OCR_LOW': 0.45,
    'EXTRACTION_HIGH': 0.88,
    'EXTRACTION_MEDIUM': 0.68,
    'EXTRACTION_LOW': 0.48
}

# Completeness thresholds
COMPLETENESS_THRESHOLDS: Dict[str, float] = {
    'COMPLETE': 0.95,
    'MOSTLY_COMPLETE': 0.80,
    'PARTIALLY_COMPLETE': 0.60,
    'INCOMPLETE': 0.40
}

# =============================================================================
# PROCESSING LIMITS AND TIMEOUTS
# =============================================================================

# File size limits in MB by file type
FILE_SIZE_LIMITS: Dict[str, float] = {
    'txt': 10.0,
    'html': 20.0,
    'json': 50.0,
    'log': 100.0,
    'pdf': 200.0,
    'docx': 100.0,
    'doc': 100.0,
    'png': 50.0,
    'jpg': 50.0,
    'jpeg': 50.0,
    'bmp': 100.0,
    'tiff': 100.0,
    'csv': 500.0,
    'xlsx': 200.0,
    'xls': 200.0
}

# Processing timeouts in seconds by operation
PROCESSING_TIMEOUTS: Dict[str, int] = {
    'classification': 30,
    'text_extraction': 120,
    'ocr_extraction': 300,
    'hybrid_extraction': 600,
    'context_analysis': 180,
    'structuring': 120,
    'validation': 60,
    'total_pipeline': 1200
}

# Memory limits in MB
MEMORY_LIMITS: Dict[str, int] = {
    'max_file_cache': 1000,
    'max_result_cache': 500,
    'max_model_memory': 2000,
    'agent_memory_limit': 512
}

# Concurrency limits
CONCURRENCY_LIMITS: Dict[str, int] = {
    'max_concurrent_files': 10,
    'max_concurrent_agents': 5,
    'max_queue_size': 100,
    'max_retry_attempts': 3
}

# =============================================================================
# DEFAULT CONFIGURATIONS
# =============================================================================

# Default system configuration
DEFAULT_CONFIG: Dict[str, Any] = {
    'version': '1.0.0',
    'environment': 'development',
    'debug': False,
    'log_level': 'INFO',
    'enable_caching': True,
    'cache_ttl': 3600,
    'enable_metrics': True,
    'enable_validation': True,
    'max_retries': 3,
    'retry_delay': 1.0,
    'cleanup_temp_files': True
}

# Default agent configurations
DEFAULT_AGENT_CONFIG: Dict[str, Dict[str, Any]] = {
    'classifier': {
        'confidence_threshold': 0.7,
        'enable_hybrid_detection': True,
        'max_analysis_depth': 3,
        'cache_results': True
    },
    'text_extractor': {
        'preserve_formatting': True,
        'extract_metadata': True,
        'timeout': 120,
        'encoding': 'utf-8'
    },
    'ocr_extractor': {
        'engine': 'tesseract',
        'languages': ['eng'],
        'dpi': 300,
        'preprocessing': True,
        'confidence_threshold': 0.6
    },
    'hybrid_extractor': {
        'text_priority': True,
        'merge_overlapping': True,
        'validate_consistency': True
    },
    'context_analysis': {
        'enable_entity_extraction': True,
        'enable_relationship_mapping': True,
        'min_confidence': 0.5,
        'max_entities': 1000
    },
    'structured_agent': {
        'validation_level': 'strict',
        'normalize_data': True,
        'quality_check': True,
        'output_format': 'json'
    }
}

# Default pipeline configurations
DEFAULT_PIPELINE_CONFIG: Dict[str, Dict[str, Any]] = {
    'text_pipeline': {
        'parallel_processing': False,
        'validate_intermediate': True,
        'save_intermediate': False
    },
    'ocr_pipeline': {
        'parallel_processing': True,
        'validate_intermediate': True,
        'save_intermediate': True,
        'fallback_engines': ['easyocr', 'paddleocr']
    },
    'hybrid_pipeline': {
        'parallel_processing': True,
        'validate_intermediate': True,
        'save_intermediate': True,
        'merge_strategy': 'weighted'
    }
}

# =============================================================================
# PATHS AND DIRECTORIES
# =============================================================================

# Base directories
BASE_DIRS: Dict[str, str] = {
    'data': 'data',
    'input': 'data/input',
    'output': 'data/output',
    'cache': 'data/cache',
    'temp': 'data/temp',
    'models': 'data/models',
    'logs': 'logs',
    'config': 'config'
}

# Log file names
LOG_FILES: Dict[str, str] = {
    'app': 'app.log',
    'error': 'error.log',
    'performance': 'performance.log',
    'access': 'access.log',
    'debug': 'debug.log'
}

# =============================================================================
# REGEX PATTERNS
# =============================================================================

# Common regex patterns for content analysis
REGEX_PATTERNS: Dict[str, str] = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'(\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
    'url': r'https?://(?:[-\w.])+(?::[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
    'date_iso': r'\d{4}-\d{2}-\d{2}',
    'date_us': r'\d{1,2}/\d{1,2}/\d{4}',
    'number': r'-?\d+(?:\.\d+)?',
    'currency': r'\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
    'ssn': r'\d{3}-\d{2}-\d{4}',
    'zip_code': r'\d{5}(?:-\d{4})?'
}

# =============================================================================
# MODEL CONFIGURATIONS
# =============================================================================

# NLP model configurations
NLP_MODEL_CONFIG: Dict[str, Any] = {
    'spacy_model': 'en_core_web_sm',
    'transformers_model': 'bert-base-uncased',
    'max_sequence_length': 512,
    'batch_size': 32,
    'device': 'auto'  # 'cpu', 'cuda', or 'auto'
}

# OCR engine configurations
OCR_ENGINE_CONFIG: Dict[str, Dict[str, Any]] = {
    'tesseract': {
        'config': '--oem 3 --psm 6',
        'languages': ['eng'],
        'timeout': 30
    },
    'easyocr': {
        'languages': ['en'],
        'gpu': False,
        'confidence_threshold': 0.5
    },
    'paddleocr': {
        'use_angle_cls': True,
        'lang': 'en',
        'use_gpu': False
    }
}

# =============================================================================
# API CONFIGURATIONS
# =============================================================================

# API endpoint configurations
API_CONFIG: Dict[str, Any] = {
    'version': 'v1',
    'title': 'Unstructured Data Integration API',
    'description': 'API for processing unstructured data files',
    'max_request_size': 100 * 1024 * 1024,  # 100MB
    'request_timeout': 300,
    'rate_limit': '100/minute',
    'cors_origins': ['*'],
    'docs_url': '/docs',
    'redoc_url': '/redoc'
}

# Response format templates
RESPONSE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    'success': {
        'status': 'success',
        'message': '',
        'data': {},
        'timestamp': None
    },
    'error': {
        'status': 'error',
        'error_code': '',
        'message': '',
        'details': {},
        'timestamp': None
    }
}

# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

# Environment variable names
ENV_VARS: Dict[str, str] = {
    'LOG_LEVEL': 'UDI_LOG_LEVEL',
    'DEBUG': 'UDI_DEBUG',
    'CACHE_TTL': 'UDI_CACHE_TTL',
    'MAX_FILE_SIZE': 'UDI_MAX_FILE_SIZE',
    'DATABASE_URL': 'UDI_DATABASE_URL',
    'REDIS_URL': 'UDI_REDIS_URL',
    'SECRET_KEY': 'UDI_SECRET_KEY',
    'ENVIRONMENT': 'UDI_ENVIRONMENT'
}

# Default environment values
DEFAULT_ENV_VALUES: Dict[str, str] = {
    'UDI_LOG_LEVEL': 'INFO',
    'UDI_DEBUG': 'False',
    'UDI_CACHE_TTL': '3600',
    'UDI_MAX_FILE_SIZE': '100',
    'UDI_ENVIRONMENT': 'development'
}

# =============================================================================
# VALIDATION SCHEMAS
# =============================================================================

# JSON schema for file metadata validation
FILE_METADATA_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "file_path": {"type": "string"},
        "file_name": {"type": "string"},
        "file_type": {"type": "string", "enum": list(SUPPORTED_FILE_TYPES)},
        "file_size": {"type": "integer", "minimum": 0},
        "created_at": {"type": "string", "format": "date-time"},
        "modified_at": {"type": "string", "format": "date-time"},
        "checksum": {"type": "string"}
    },
    "required": ["file_path", "file_name", "file_type", "file_size"]
}

# JSON schema for extraction result validation
EXTRACTION_RESULT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "file_path": {"type": "string"},
        "content": {"type": "object"},
        "metadata": {"type": "object"},
        "processing_status": {"type": "string", "enum": [status.value for status in ProcessingStatus]},
        "quality_metrics": {"type": "object"},
        "extraction_timestamp": {"type": "string", "format": "date-time"}
    },
    "required": ["file_path", "content", "processing_status"]
}