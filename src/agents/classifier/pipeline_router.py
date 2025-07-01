# src/agents/classifier/pipeline_router.py
from typing import Dict, Any
from ...core.data_models import FileMetadata, FileType, PipelineType

class PipelineRouter:
    """Routes files to appropriate processing pipelines based on analysis"""
    
    def __init__(self):
        # Define pipeline mapping rules
        self.pipeline_rules = {
            # Text-based files -> Text Pipeline
            FileType.TXT: PipelineType.TEXT,
            FileType.HTML: PipelineType.TEXT,
            FileType.JSON: PipelineType.TEXT,
            FileType.LOG: PipelineType.TEXT,
            
            # Image files -> OCR Pipeline
            FileType.PNG: PipelineType.OCR,
            FileType.JPG: PipelineType.OCR,
            FileType.JPEG: PipelineType.OCR,
            
            # Complex files -> Hybrid Pipeline (default)
            FileType.PDF: PipelineType.HYBRID,
            FileType.DOCX: PipelineType.HYBRID,
        }
        
        # Complexity thresholds for pipeline switching
        self.complexity_thresholds = {
            'hybrid_required': 0.7,
            'ocr_over_text': 0.8
        }
    
    async def route_to_pipeline(
        self, 
        file_metadata: FileMetadata, 
        complexity_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine the optimal pipeline for processing the file
        
        Args:
            file_metadata: File metadata from detection
            complexity_result: Content complexity analysis results
            
        Returns:
            Dictionary with pipeline recommendation and reasoning
        """
        file_type = file_metadata.file_type
        complexity_score = complexity_result.get('complexity_score', 0.5)
        complexity_level = complexity_result
        