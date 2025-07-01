"""
Agents Package

This package contains all the intelligent agents used in the Unstructured Data Integration system.
Each agent is responsible for specific aspects of data processing and analysis.

Agents Overview:
- ClassifierAgent: Routes files to appropriate processing pipelines
- TextExtractorAgent: Processes text-based files (HTML, TXT, JSON, LOG)
- OCRExtractorAgent: Handles image-based content extraction
- HybridExtractorAgent: Manages mixed content files
- ContextAnalysisAgent: Transforms raw data into structured information
- StructuredAgent: Final validation and quality assurance

Author: Unstructured Data Integration Team
Version: 1.0.0
"""

from typing import Dict, Any, Optional, List
import logging

# Import all agent classes for easy access
from .classifier.classifier_agent import ClassifierAgent
from .text_extractor.text_extractor_agent import TextExtractorAgent

# Import agent utilities
from .classifier.file_detector import FileDetector
from .classifier.content_analyzer import ContentAnalyzer
from .classifier.pipeline_router import PipelineRouter

# Agent registry for dynamic agent loading
AGENT_REGISTRY: Dict[str, Any] = {
    'classifier': ClassifierAgent,
    'text_extractor': TextExtractorAgent,
    'file_detector': FileDetector,
    'content_analyzer': ContentAnalyzer,
    'pipeline_router': PipelineRouter,
}

# Supported agent types
SUPPORTED_AGENTS = list(AGENT_REGISTRY.keys())

# Agent configuration defaults
DEFAULT_AGENT_CONFIG = {
    'classifier': {
        'confidence_threshold': 0.8,
        'enable_hybrid_detection': True,
        'max_file_size_mb': 100
    },
    'text_extractor': {
        'preserve_formatting': True,
        'extract_metadata': True,
        'timeout_seconds': 30
    }
}

logger = logging.getLogger(__name__)


def get_agent(agent_type: str, config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Factory function to create agent instances.
    
    Args:
        agent_type: Type of agent to create
        config: Optional configuration for the agent
        
    Returns:
        Agent instance
        
    Raises:
        ValueError: If agent type is not supported
    """
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(f"Unsupported agent type: {agent_type}. "
                        f"Supported types: {SUPPORTED_AGENTS}")
    
    agent_class = AGENT_REGISTRY[agent_type]
    agent_config = config or DEFAULT_AGENT_CONFIG.get(agent_type, {})
    
    logger.info(f"Creating {agent_type} agent with config: {agent_config}")
    
    try:
        return agent_class(config=agent_config)
    except Exception as e:
        logger.error(f"Failed to create {agent_type} agent: {e}")
        raise


def list_available_agents() -> List[str]:
    """
    Get list of all available agent types.
    
    Returns:
        List of supported agent type names
    """
    return SUPPORTED_AGENTS.copy()


def validate_agent_config(agent_type: str, config: Dict[str, Any]) -> bool:
    """
    Validate agent configuration.
    
    Args:
        agent_type: Type of agent
        config: Configuration to validate
        
    Returns:
        True if configuration is valid
        
    Raises:
        ValueError: If configuration is invalid
    """
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent type: {agent_type}")
    
    # Basic validation - can be extended per agent type
    required_fields = {
        'classifier': ['confidence_threshold'],
        'text_extractor': ['preserve_formatting']
    }
    
    if agent_type in required_fields:
        for field in required_fields[agent_type]:
            if field not in config:
                raise ValueError(f"Missing required field '{field}' for {agent_type} agent")
    
    logger.debug(f"Configuration validated for {agent_type} agent")
    return True


# Package metadata
__version__ = "1.0.0"
__author__ = "Unstructured Data Integration Team"
__email__ = "team@example.com"

# Export main classes and functions
__all__ = [
    'ClassifierAgent',
    'TextExtractorAgent',
    'FileDetector',
    'ContentAnalyzer',
    'PipelineRouter',
    'get_agent',
    'list_available_agents',
    'validate_agent_config',
    'AGENT_REGISTRY',
    'SUPPORTED_AGENTS',
    'DEFAULT_AGENT_CONFIG'
]