"""
Utilities Module

This module contains common utility functions used throughout the Unstructured Data
Integration system. It provides helper functions for file operations, data validation,
formatting, configuration management, and other common tasks.

Categories:
- File Operations
- Data Validation and Conversion
- Configuration Management
- Time and Date Utilities
- Text Processing
- Hashing and Security
- Performance Monitoring

Author: Unstructured Data Integration Team
Version: 1.0.0
"""

import os
import re
import json
import hashlib
import mimetypes
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import time
from functools import wraps
import jsonschema
from jsonschema import validate, ValidationError as JsonValidationError

from .constants import (
    SUPPORTED_FILE_TYPES,
    FILE_SIZE_LIMITS,
    MIME_TYPE_MAPPING,
    REGEX_PATTERNS,
    DEFAULT_ENV_VALUES
)

logger = logging.getLogger(__name__)

# =============================================================================
# FILE OPERATIONS
# =============================================================================

def validate_file_path(file_path: str) -> bool:
    """
    Validate if a file path exists and is accessible.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        True if file path is valid and accessible
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file() and os.access(file_path, os.R_OK)
    except Exception as e:
        logger.warning(f"File path validation failed for {file_path}: {e}")
        return False


def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary containing file metadata
    """
    try:
        path = Path(file_path)
        stat = path.stat()
        
        # Get file extension and MIME type
        file_ext = path.suffix.lower().lstrip('.')
        mime_type = get_mime_type(file_path)
        
        metadata = {
            'file_path': str(path.absolute()),
            'file_name': path.name,
            'file_type': file_ext,
            'file_size': stat.st_size,
            'mime_type': mime_type,
            'created_at': datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            'accessed_at': datetime.fromtimestamp(stat.st_atime, tz=timezone.utc).isoformat(),
            'checksum': calculate_file_hash(file_path),
            'is_supported': file_ext in SUPPORTED_FILE_TYPES,
            'size_mb': convert_bytes_to_mb(stat.st_size)
        }
        
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to extract metadata from {file_path}: {e}")
        raise


def get_mime_type(file_path: str) -> str:
    """
    Get MIME type for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string
    """
    file_ext = Path(file_path).suffix.lower().lstrip('.')
    
    # Use custom mapping first
    if file_ext in MIME_TYPE_MAPPING:
        return MIME_TYPE_MAPPING[file_ext]
    
    # Fallback to mimetypes module
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'


def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate hash for a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)
        
    Returns:
        Hexadecimal hash string
    """
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        raise


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove/replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = 'unnamed_file'
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized


def create_directory_structure(path: str) -> bool:
    """
    Create directory structure if it doesn't exist.
    
    Args:
        path: Directory path to create
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False


def get_file_size_category(file_size: int) -> str:
    """
    Categorize file size.
    
    Args:
        file_size: File size in bytes
        
    Returns:
        Size category string
    """
    size_mb = convert_bytes_to_mb(file_size)
    
    if size_mb < 1:
        return 'small'
    elif size_mb < 10:
        return 'medium'
    elif size_mb < 100:
        return 'large'
    else:
        return 'very_large'


# =============================================================================
# DATA VALIDATION AND CONVERSION
# =============================================================================

def convert_bytes_to_mb(bytes_value: int) -> float:
    """
    Convert bytes to megabytes.
    
    Args:
        bytes_value: Size in bytes
        
    Returns:
        Size in megabytes (rounded to 2 decimal places)
    """
    return round(bytes_value / (1024 * 1024), 2)


def convert_mb_to_bytes(mb_value: float) -> int:
    """
    Convert megabytes to bytes.
    
    Args:
        mb_value: Size in megabytes
        
    Returns:
        Size in bytes
    """
    return int(mb_value * 1024 * 1024)


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against JSON schema.
    
    Args:
        data: Data to validate
        schema: JSON schema
        
    Returns:
        True if validation passes
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        validate(instance=data, schema=schema)
        return True
    except JsonValidationError as e:
        logger.error(f"JSON schema validation failed: {e.message}")
        raise ValidationError(f"Schema validation failed: {e.message}")
    except Exception as e:
        logger.error(f"JSON schema validation error: {e}")
        raise ValidationError(f"Schema validation error: {e}")


def is_valid_json(json_string: str) -> bool:
    """
    Check if string is valid JSON.
    
    Args:
        json_string: String to validate
        
    Returns:
        True if string is valid JSON
    """
    try:
        json.loads(json_string)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """
    Safely load JSON with fallback.
    
    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"JSON parsing failed: {e}")
        return default


def normalize_text(text: str) -> str:
    """
    Normalize text by removing extra whitespace and standardizing format.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', text.strip())
    
    # Remove control characters
    normalized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', normalized)
    
    return normalized


def extract_entities_with_regex(text: str, entity_type: str) -> List[str]:
    """
    Extract entities from text using regex patterns.
    
    Args:
        text: Text to search
        entity_type: Type of entity to extract (email, phone, url, etc.)
        
    Returns:
        List of extracted entities
    """
    if entity_type not in REGEX_PATTERNS:
        logger.warning(f"Unknown entity type: {entity_type}")
        return []
    
    pattern = REGEX_PATTERNS[entity_type]
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(matches))


# =============================================================================
# CONFIGURATION MANAGEMENT
# =============================================================================

def merge_configurations(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries with deep merging.
    
    Args:
        configs: Configuration dictionaries to merge
        
    Returns:
        Merged configuration dictionary
    """
    result = {}
    
    for config in configs:
        if not isinstance(config, dict):
            continue
            
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_configurations(result[key], value)
            else:
                result[key] = value
    
    return result


def load_config_from_env(prefix: str = 'UDI_') -> Dict[str, str]:
    """
    Load configuration from environment variables.
    
    Args:
        prefix: Prefix for environment variables
        
    Returns:
        Dictionary of configuration values
    """
    config = {}
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()
            config[config_key] = value
    
    # Apply defaults for missing values
    for env_var, default_value in DEFAULT_ENV_VALUES.items():
        if env_var.startswith(prefix):
            config_key = env_var[len(prefix):].lower()
            if config_key not in config:
                config[config_key] = default_value
    
    return config


def validate_config_types(config: Dict[str, Any], type_mapping: Dict[str, type]) -> Dict[str, Any]:
    """
    Validate and convert configuration value types.
    
    Args:
        config: Configuration dictionary
        type_mapping: Mapping of keys to expected types
        
    Returns:
        Configuration with converted types
    """
    validated_config = config.copy()
    
    for key, expected_type in type_mapping.items():
        if key in validated_config:
            value = validated_config[key]
            
            try:
                if expected_type == bool:
                    if isinstance(value, str):
                        validated_config[key] = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        validated_config[key] = bool(value)
                elif expected_type in (int, float):
                    validated_config[key] = expected_type(value)
                elif expected_type == list and isinstance(value, str):
                    validated_config[key] = [item.strip() for item in value.split(',')]
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to convert config key '{key}' to {expected_type}: {e}")
    
    return validated_config


# =============================================================================
# TIME AND DATE UTILITIES
# =============================================================================

def format_timestamp(timestamp: Optional[datetime] = None, format_string: str = '%Y-%m-%d %H:%M:%S UTC') -> str:
    """
    Format timestamp to string.
    
    Args:
        timestamp: Datetime object (uses current time if None)
        format_string: Format string for timestamp
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    return timestamp.strftime(format_string)


def retry_on_exception(max_retries: int = 3, delay_seconds: float = 1.0, exceptions: Tuple = (Exception,)):
    """
    Decorator to retry a function on specified exceptions.
    
    Args:
        max_retries: Maximum number of retries
        delay_seconds: Delay between retries in seconds
        exceptions: Tuple of exception classes to catch
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    logger.warning(f"Exception caught in {func.__name__}: {e}. Retrying {attempts}/{max_retries}...")
                    time.sleep(delay_seconds)
            # Final attempt
            return func(*args, **kwargs)
        return wrapper
    return decorator
