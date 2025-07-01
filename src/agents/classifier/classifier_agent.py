# src/agents/classifier/classifier_agent.py
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

from ...core.base_agent import BaseAgent
from ...core.data_models import (
    FileMetadata, FileType, PipelineType, ClassificationResult,
    ClassificationError
)
from .file_detector import FileDetector
from .content_analyzer import ContentAnalyzer
from .pipeline_router import PipelineRouter

class ClassifierAgent(BaseAgent):
    """
    Main classifier agent that coordinates file detection, 
    content analysis, and pipeline routing
    """
    
    def __init__(self):
        super().__init__("ClassifierAgent")
        self.file_detector = FileDetector()
        self.content_analyzer = ContentAnalyzer()
        self.pipeline_router = PipelineRouter()
    
    async def process(self, file_path: str, **kwargs) -> ClassificationResult:
        """
        Classify a file and determine the appropriate processing pipeline
        
        Args:
            file_path: Path to the file to classify
            **kwargs: Additional parameters
            
        Returns:
            ClassificationResult with pipeline recommendation
        """
        start_time = time.time()
        
        try:
            self._log_processing_start(f"file: {file_path}")
            
            # Validate file exists
            if not os.path.exists(file_path):
                raise ClassificationError(f"File not found: {file_path}")
            
            # Step 1: Detect file type and extract basic metadata
            file_metadata = await self.file_detector.detect_file_type(file_path)
            self.logger.info(f"Detected file type: {file_metadata.file_type}")
            
            # Step 2: Analyze content complexity if possible
            complexity_result = await self.content_analyzer.analyze_complexity(
                file_path, file_metadata
            )
            self.logger.info(f"Content complexity score: {complexity_result['complexity_score']}")
            
            # Step 3: Determine optimal pipeline
            pipeline_recommendation = await self.pipeline_router.route_to_pipeline(
                file_metadata, complexity_result
            )
            
            # Create classification result
            classification_result = ClassificationResult(
                file_type=file_metadata.file_type,
                recommended_pipeline=pipeline_recommendation['pipeline'],
                confidence=pipeline_recommendation['confidence'],
                complexity_score=complexity_result['complexity_score'],
                metadata={
                    'file_metadata': file_metadata.__dict__,
                    'content_analysis': complexity_result,
                    'pipeline_reasoning': pipeline_recommendation['reasoning']
                },
                requires_hybrid=pipeline_recommendation.get('requires_hybrid', False)
            )
            
            processing_time = time.time() - start_time
            self._log_processing_end(
                f"Pipeline: {pipeline_recommendation['pipeline']}, "
                f"Confidence: {pipeline_recommendation['confidence']:.2f}",
                processing_time
            )
            
            return classification_result
            
        except Exception as e:
            self._log_error(e, "classification")
            raise ClassificationError(f"Classification failed: {str(e)}") from e
    
    async def batch_classify(self, file_paths: list) -> Dict[str, ClassificationResult]:
        """
        Classify multiple files in batch
        
        Args:
            file_paths: List of file paths to classify
            
        Returns:
            Dictionary mapping file paths to classification results
        """
        results = {}
        
        for file_path in file_paths:
            try:
                result = await self.process(file_path)
                results[file_path] = result
            except Exception as e:
                self.logger.error(f"Failed to classify {file_path}: {str(e)}")
                results[file_path] = None
        
        return results
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get list of supported file formats by pipeline"""
        return {
            'text_pipeline': ['html', 'txt', 'json', 'log'],
            'ocr_pipeline': ['pdf', 'png', 'jpg', 'jpeg'],
            'hybrid_pipeline': ['docx', 'complex_pdf']
        }