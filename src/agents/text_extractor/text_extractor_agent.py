# src/agents/text_extractor/text_extractor_agent.py
import time
from typing import Dict, Any, List
from pathlib import Path

from ...core.base_agent import BaseAgent
from ...core.data_models import (
    FileMetadata, ExtractionResult, StructuredElement, 
    ExtractionMetadata, ExtractionError, FileType
)
from .parsers.html_parser import HTMLParser
from .parsers.json_parser import JSONParser
from .parsers.txt_parser import TXTParser
from .parsers.log_parser import LogParser
from .extractors.raw_data_extractor import RawDataExtractor
from .extractors.metadata_extractor import MetadataExtractor

class TextExtractorAgent(BaseAgent):
    """
    Agent responsible for extracting content from text-based files
    (HTML, TXT, JSON, LOG)
    """
    
    def __init__(self):
        super().__init__("TextExtractorAgent")
        
        # Initialize parsers
        self.parsers = {
            FileType.HTML: HTMLParser(),
            FileType.TXT: TXTParser(),
            FileType.JSON: JSONParser(),
            FileType.LOG: LogParser()
        }
        
        # Initialize extractors
        self.raw_data_extractor = RawDataExtractor()
        self.metadata_extractor = MetadataExtractor()
    
    async def process(self, file_path: str, file_metadata: FileMetadata = None, **kwargs) -> ExtractionResult:
        """
        Extract content from text-based file
        
        Args:
            file_path: Path to the file to process
            file_metadata: Optional pre-computed file metadata
            **kwargs: Additional processing parameters
            
        Returns:
            ExtractionResult with extracted content and metadata
        """
        start_time = time.time()
        
        try:
            self._log_processing_start(f"text file: {file_path}")
            
            # Get file metadata if not provided
            if file_metadata is None:
                from ..classifier.file_detector import FileDetector
                detector = FileDetector()
                file_metadata = await detector.detect_file_type(file_path)
            
            # Validate file type is supported
            if file_metadata.file_type not in self.parsers:
                raise ExtractionError(
                    f"Unsupported file type for text extraction: {file_metadata.file_type}"
                )
            
            # Step 1: Extract raw data
            raw_content = await self.raw_data_extractor.extract(file_path, file_metadata)
            self.logger.info(f"Raw content extracted: {len(raw_content)} characters")
            
            # Step 2: Parse structured content using appropriate parser
            parser = self.parsers[file_metadata.file_type]
            # Adjusted to call parse with file_path as per parser interface
            parse_result = parser.parse(file_path)
            # Extract structured elements from parse_result
            structured_elements = parse_result.get('content', {}).get('structured_elements', [])
            self.logger.info(f"Parsed {len(structured_elements)} structured elements")
            
            # Step 3: Extract additional metadata
            content_metadata = await self.metadata_extractor.extract_metadata(
                raw_content, structured_elements, file_metadata
            )
            
            # Step 4: Create extraction result
            extraction_metadata = self._create_extraction_metadata(
                method=f"{file_metadata.file_type.value}_parser",
                confidence=self._calculate_confidence_score(structured_elements),
                start_time=start_time
            )
            
            # Build the result
            result = ExtractionResult(
                metadata={
                    'source_file': file_metadata.filename,
                    'file_type': file_metadata.file_type.value,
                    'file_size': file_metadata.file_size,
                    'encoding': file_metadata.encoding,
                    'extraction_timestamp': extraction_metadata.timestamp.isoformat(),
                    'content_metadata': content_metadata
                },
                content={
                    'raw_text': raw_content,
                    'structured_elements_count': len(structured_elements),
                    'processing_method': extraction_metadata.extraction_method
                },
                extraction_info=extraction_metadata,
                structured_elements=structured_elements
            )
            
            processing_time = time.time() - start_time
            self._log_processing_end(
                f"Extracted {len(structured_elements)} elements",
                processing_time
            )
            
            return result
            
        except Exception as e:
            self._log_error(e, "text extraction")
            raise ExtractionError(f"Text extraction failed for {file_path}: {str(e)}") from e
    
    async def process_batch(self, file_paths: List[str]) -> Dict[str, ExtractionResult]:
        """
        Process multiple text files in batch
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dictionary mapping file paths to extraction results
        """
        results = {}
        
        for file_path in file_paths:
            try:
                result = await self.process(file_path)
                results[file_path] = result
                self.logger.info(f"Successfully processed: {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {str(e)}")
                results[file_path] = None
        
        return results
    
    def _calculate_confidence_score(self, structured_elements: List[StructuredElement]) -> float:
        """Calculate confidence score based on extraction results"""
        if not structured_elements:
            return 0.5  # Medium confidence for empty results
        
        # Base confidence
        confidence = 0.8
        
        # Adjust based on element confidence scores
        element_confidences = [elem.confidence for elem in structured_elements if elem.confidence is not None]
        if element_confidences:
            avg_element_confidence = sum(element_confidences) / len(element_confidences)
            confidence = (confidence + avg_element_confidence) / 2
        
        # Adjust based on number of elements (more elements = higher confidence)
        if len(structured_elements) > 10:
            confidence = min(confidence + 0.1, 1.0)
        elif len(structured_elements) < 3:
            confidence = max(confidence - 0.1, 0.1)
        
        return round(confidence, 2)
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return [file_type.value for file_type in self.parsers.keys()]
    
    def get_parser_info(self, file_type: FileType) -> Dict[str, Any]:
        """Get information about a specific parser"""
        if file_type not in self.parsers:
            return {'error': f'No parser available for {file_type.value}'}
        
        parser = self.parsers[file_type]
        return {
            'parser_name': parser.__class__.__name__,
            'supported_elements': getattr(parser, 'supported_elements', []),
            'features': getattr(parser, 'features', [])
        }
    
    async def validate_extraction(self, file_path: str, extraction_result: ExtractionResult) -> Dict[str, Any]:
        """
        Validate extraction results
        
        Args:
            file_path: Original file path
            extraction_result: Extraction result to validate
            
        Returns:
            Validation report
        """
        validation_report = {
            'is_valid': True,
            'issues': [],
            'quality_score': 0.0,
            'recommendations': []
        }
        
        try:
            # Check if extraction has content
            if not extraction_result.structured_elements:
                validation_report['issues'].append("No structured elements extracted")
                validation_report['is_valid'] = False
            
            # Check content length vs file size
            raw_text_length = len(extraction_result.content.get('raw_text', ''))
            file_size = extraction_result.metadata.get('file_size', 0)
            
            if raw_text_length == 0 and file_size > 0:
                validation_report['issues'].append("No text content extracted from non-empty file")
                validation_report['is_valid'] = False
            
            # Check extraction confidence
            extraction_confidence = extraction_result.extraction_info.confidence_score
            if extraction_confidence < 0.5:
                validation_report['issues'].append(f"Low extraction confidence: {extraction_confidence}")
                validation_report['recommendations'].append("Consider using alternative extraction method")
            
            # Calculate quality score
            quality_factors = []
            
            # Content completeness
            if raw_text_length > 0:
                quality_factors.append(0.3)
            
            # Structured elements presence
            if extraction_result.structured_elements:
                quality_factors.append(0.3)
            
            # Extraction confidence
            quality_factors.append(extraction_confidence * 0.4)
            
            validation_report['quality_score'] = sum(quality_factors)
            
            # Overall validation
            if validation_report['quality_score'] < 0.6:
                validation_report['is_valid'] = False
                validation_report['recommendations'].append("Consider re-processing with different parameters")
            
        except Exception as e:
            validation_report['issues'].append(f"Validation error: {str(e)}")
            validation_report['is_valid'] = False
        
        return validation_report