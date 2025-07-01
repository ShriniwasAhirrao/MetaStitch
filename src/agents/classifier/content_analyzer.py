# src/agents/classifier/content_analyzer.py
import os
import re
from typing import Dict, Any
from pathlib import Path

from ...core.data_models import FileMetadata, FileType, FileProcessingError

class ContentAnalyzer:
    """Analyzes content complexity to determine processing requirements"""
    
    def __init__(self):
        self.complexity_thresholds = {
            'simple': 0.3,
            'moderate': 0.6,
            'complex': 0.8
        }
    
    async def analyze_complexity(self, file_path: str, file_metadata: FileMetadata) -> Dict[str, Any]:
        """
        Analyze content complexity of the file
        
        Args:
            file_path: Path to the file
            file_metadata: File metadata from detection
            
        Returns:
            Dictionary with complexity analysis results
        """
        try:
            complexity_score = 0.0
            analysis_details = {}
            
            if file_metadata.file_type in [FileType.TXT, FileType.HTML, FileType.JSON, FileType.LOG]:
                complexity_score, analysis_details = await self._analyze_text_complexity(
                    file_path, file_metadata
                )
            elif file_metadata.file_type in [FileType.PNG, FileType.JPG, FileType.JPEG]:
                complexity_score, analysis_details = await self._analyze_image_complexity(
                    file_path, file_metadata
                )
            elif file_metadata.file_type == FileType.PDF:
                complexity_score, analysis_details = await self._analyze_pdf_complexity(
                    file_path, file_metadata
                )
            elif file_metadata.file_type == FileType.DOCX:
                complexity_score, analysis_details = await self._analyze_docx_complexity(
                    file_path, file_metadata
                )
            else:
                complexity_score = 0.5  # Default moderate complexity
                analysis_details = {'method': 'default_estimation'}
            
            return {
                'complexity_score': complexity_score,
                'complexity_level': self._get_complexity_level(complexity_score),
                'analysis_details': analysis_details,
                'file_characteristics': self._extract_file_characteristics(file_metadata)
            }
            
        except Exception as e:
            raise FileProcessingError(f"Content analysis failed for {file_path}: {str(e)}")
    
    async def _analyze_text_complexity(self, file_path: str, file_metadata: FileMetadata) -> tuple:
        """Analyze complexity of text-based files"""
        try:
            with open(file_path, 'r', encoding=file_metadata.encoding or 'utf-8') as f:
                content = f.read()
            
            analysis = {
                'character_count': len(content),
                'line_count': len(content.splitlines()),
                'word_count': len(content.split())
            }
            
            complexity_score = 0.0
            
            # Size-based complexity
            if analysis['character_count'] > 100000:  # >100KB text
                complexity_score += 0.3
            elif analysis['character_count'] > 50000:  # >50KB text
                complexity_score += 0.2
            else:
                complexity_score += 0.1
            
            # Structure-based complexity
            if file_metadata.file_type == FileType.HTML:
                complexity_score += self._analyze_html_complexity(content)
            elif file_metadata.file_type == FileType.JSON:
                complexity_score += self._analyze_json_complexity(content)
            elif file_metadata.file_type == FileType.LOG:
                complexity_score += self._analyze_log_complexity(content)
            else:  # TXT
                complexity_score += self._analyze_text_structure_complexity(content)
            
            analysis['complexity_factors'] = self._get_text_complexity_factors(content)
            
            return min(complexity_score, 1.0), analysis
            
        except Exception as e:
            return 0.5, {'error': str(e), 'method': 'fallback_estimation'}
    
    def _analyze_html_complexity(self, content: str) -> float:
        """Analyze HTML-specific complexity"""
        score = 0.0
        
        # Count HTML tags
        tag_count = len(re.findall(r'<[^>]+>', content))
        if tag_count > 500:
            score += 0.3
        elif tag_count > 100:
            score += 0.2
        else:
            score += 0.1
        
        # Check for complex elements
        if re.search(r'<table[^>]*>', content, re.IGNORECASE):
            score += 0.1
        if re.search(r'<script[^>]*>', content, re.IGNORECASE):
            score += 0.1
        if re.search(r'<style[^>]*>', content, re.IGNORECASE):
            score += 0.1
        
        return score
    
    def _analyze_json_complexity(self, content: str) -> float:
        """Analyze JSON-specific complexity"""
        score = 0.0
        
        try:
            import json
            data = json.loads(content)
            
            # Nesting depth
            depth = self._get_json_depth(data)
            if depth > 5:
                score += 0.3
            elif depth > 3:
                score += 0.2
            else:
                score += 0.1
            
            # Number of keys
            key_count = self._count_json_keys(data)
            if key_count > 100:
                score += 0.2
            elif key_count > 50:
                score += 0.1
            
        except json.JSONDecodeError:
            score = 0.4  # Invalid JSON is complex to handle
        
        return score
    
    def _analyze_log_complexity(self, content: str) -> float:
        """Analyze log file complexity"""
        score = 0.0
        lines = content.splitlines()
        
        # Number of lines
        if len(lines) > 10000:
            score += 0.3
        elif len(lines) > 1000:
            score += 0.2
        else:
            score += 0.1
        
        # Log format variety (check for different timestamp formats)
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\[\d{2}:\d{2}:\d{2}\]',  # [HH:MM:SS]
        ]
        
        pattern_matches = sum(1 for pattern in timestamp_patterns 
                            if re.search(pattern, content))
        score += pattern_matches * 0.05
        
        return score
    
    def _analyze_text_structure_complexity(self, content: str) -> float:
        """Analyze plain text structure complexity"""
        score = 0.0
        
        # Check for structured elements
        lines = content.splitlines()
        
        # Look for list patterns
        list_patterns = [r'^\s*[-*+]\s', r'^\s*\d+\.\s', r'^\s*[a-zA-Z]\.\s']
        list_lines = sum(1 for line in lines 
                        for pattern in list_patterns 
                        if re.match(pattern, line))
        
        if list_lines > len(lines) * 0.3:  # >30% list items
            score += 0.2
        
        # Check for table-like structures
        tab_separated_lines = sum(1 for line in lines if '\t' in line)
        if tab_separated_lines > len(lines) * 0.1:  # >10% tab-separated
            score += 0.1
        
        return score
    
    async def _analyze_image_complexity(self, file_path: str, file_metadata: FileMetadata) -> tuple:
        """Analyze image complexity (basic implementation)"""
        # For now, use file size as a proxy for complexity
        size_mb = file_metadata.file_size / (1024 * 1024)
        
        if size_mb > 5:
            complexity_score = 0.7
        elif size_mb > 2:
            complexity_score = 0.5
        else:
            complexity_score = 0.3
        
        analysis = {
            'size_mb': size_mb,
            'estimated_complexity': 'size_based'
        }
        
        return complexity_score, analysis
    
    async def _analyze_pdf_complexity(self, file_path: str, file_metadata: FileMetadata) -> tuple:
        """Analyze PDF complexity"""
        # PDF complexity is often high due to mixed content
        size_mb = file_metadata.file_size / (1024 * 1024)
        
        complexity_score = 0.6  # Base complexity for PDFs
        
        if size_mb > 10:
            complexity_score = 0.8
        elif size_mb > 5:
            complexity_score = 0.7
        
        analysis = {
            'size_mb': size_mb,
            'assumed_mixed_content': True
        }
        
        return complexity_score, analysis
    
    async def _analyze_docx_complexity(self, file_path: str, file_metadata: FileMetadata) -> tuple:
        """Analyze DOCX complexity"""
        # DOCX files typically require hybrid processing
        complexity_score = 0.7
        
        analysis = {
            'requires_hybrid_processing': True,
            'contains_mixed_content': True
        }
        
        return complexity_score, analysis
    
    def _get_json_depth(self, obj, depth=0):
        """Calculate maximum nesting depth of JSON object"""
        if isinstance(obj, dict):
            return max([self._get_json_depth(v, depth + 1) for v in obj.values()] + [depth])
        elif isinstance(obj, list):
            return max([self._get_json_depth(item, depth + 1) for item in obj] + [depth])
        else:
            return depth
    
    def _count_json_keys(self, obj):
        """Count total number of keys in nested JSON"""
        if isinstance(obj, dict):
            return len(obj) + sum(self._count_json_keys(v) for v in obj.values())
        elif isinstance(obj, list):
            return sum(self._count_json_keys(item) for item in obj)
        else:
            return 0
    
    def _get_text_complexity_factors(self, content: str) -> Dict[str, Any]:
        """Extract factors that contribute to text complexity"""
        return {
            'has_tables': bool(re.search(r'\t.*\t', content)),
            'has_lists': bool(re.search(r'^\s*[-*+]\s', content, re.MULTILINE)),
            'has_numbered_lists': bool(re.search(r'^\s*\d+\.\s', content, re.MULTILINE)),
            'has_urls': bool(re.search(r'https?://', content)),
            'has_emails': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content))
        }
    
    def _get_complexity_level(self, score: float) -> str:
        """Convert complexity score to level"""
        if score >= self.complexity_thresholds['complex']:
            return 'complex'
        elif score >= self.complexity_thresholds['moderate']:
            return 'moderate'
        else:
            return 'simple'
    
    def _extract_file_characteristics(self, file_metadata: FileMetadata) -> Dict[str, Any]:
        """Extract general file characteristics"""
        return {
            'size_category': self._categorize_file_size(file_metadata.file_size),
            'file_type': file_metadata.file_type.value,
            'has_encoding': file_metadata.encoding is not None
        }
    
    def _categorize_file_size(self, size_bytes: int) -> str:
        """Categorize file size"""
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > 10:
            return 'large'
        elif size_mb > 1:
            return 'medium'
        else:
            return 'small'