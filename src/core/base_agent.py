# src/core/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import time

from .data_models import ExtractionResult, ExtractionMetadata, AgentException

class BaseAgent(ABC):
    """Base class for all processing agents"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging for the agent"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f'%(asctime)s - {self.name} - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    @abstractmethod
    async def process(self, input_data: Any, **kwargs) -> Any:
        """Main processing method - must be implemented by subclasses"""
        pass
    
    def _create_extraction_metadata(
        self, 
        method: str, 
        confidence: float, 
        start_time: float
    ) -> ExtractionMetadata:
        """Create standardized extraction metadata"""
        return ExtractionMetadata(
            extraction_method=method,
            confidence_score=confidence,
            processing_time=time.time() - start_time,
            agent_version=self.version
        )
    
    def _log_processing_start(self, input_info: str):
        """Log processing start"""
        self.logger.info(f"Starting processing: {input_info}")
    
    def _log_processing_end(self, result_info: str, processing_time: float):
        """Log processing completion"""
        self.logger.info(f"Processing completed: {result_info} (took {processing_time:.2f}s)")
    
    def _log_error(self, error: Exception, context: str = ""):
        """Log processing errors"""
        self.logger.error(f"Error in {context}: {str(error)}", exc_info=True)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the agent"""
        return {
            "agent": self.name,
            "version": self.version,
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }