# src/agents/text_extractor/parsers/txt_parser.py
import re
from typing import List, Dict, Any
from ....core.data_models import StructuredElement, FileMetadata

class TXTParser:
    """Parser for plain text files"""
    
    def __init__(self):
        self.supported_elements = ['paragraph', 'list', 'heading', 'table', 'section']
        self.features = ['structure_detection', 'pattern_recognition', 'content_classification']
    
    async def parse(self, content: str, file_metadata: FileMetadata) -> List[StructuredElement]:
        """Parse text content into structured elements"""
        elements = []
        lines = content.splitlines()
        position = 0
        
        current_paragraph = []
        
        for line_num, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Skip empty lines
            if not stripped_line:
                if current_paragraph:
                    elements.append(self._create_paragraph_element(current_paragraph, position))
                    current_paragraph = []
                    position += 1
                continue
            
            # Check for different content types
            element = None
            
            # Check for headings (lines in ALL CAPS or with specific patterns)
            if self._is_heading(stripped_line):
                if current_paragraph:
                    elements.append(self._create_paragraph_element(current_paragraph, position))
                    current_paragraph = []
                    position += 1
                
                element = StructuredElement(
                    element_type='heading',
                    content=stripped_line,
                    position=position,
                    metadata={'detection_method': 'pattern_based', 'line_number': line_num + 1},
                    confidence=0.8
                )
            
            # Check for list items
            elif self._is_list_item(stripped_line):
                if current_paragraph:
                    elements.append(self._create_paragraph_element(current_paragraph, position))
                    current_paragraph = []
                    position += 1
                
                element = StructuredElement(
                    element_type='list_item',
                    content=self._extract_list_content(stripped_line),
                    position=position,
                    metadata={
                        'list_type': self._get_list_type(stripped_line),
                        'line_number': line_num + 1
                    },
                    confidence=0.9
                )
            
            # Check for table-like structures
            elif self._is_table_row(stripped_line):
                if current_paragraph:
                    elements.append(self._create_paragraph_element(current_paragraph, position))
                    current_paragraph = []
                    position += 1
                
                element = StructuredElement(
                    element_type='table_row',
                    content=self._parse_table_row(stripped_line),
                    position=position,
                    metadata={'separator': self._detect_separator(stripped_line), 'line_number': line_num + 1},
                    confidence=0.8
                )
            
            # Regular text line
            else:
                current_paragraph.append(stripped_line)
                continue
            
            if element:
                elements.append(element)
                position += 1
        
        # Handle remaining paragraph
        if current_paragraph:
            elements.append(self._create_paragraph_element(current_paragraph, position))
        
        return elements
    
    def _is_heading(self, line: str) -> bool:
        """Detect if line is a heading"""
        # Check for all caps (but not too short)
        if len(line) > 3 and line.isupper() and not line.isdigit():
            return True
        
        # Check for title case with specific patterns
        if self._is_title_case(line) and len(line.split()) <= 8:
            return True
        
        # Check for numbered headings (1. Title, 1.1 Title, etc.)
        if re.match(r'^\d+(\.\d+)*\.?\s+[A-Z]', line):
            return True
        
        # Check for markdown-style headings (# Title)
        if re.match(r'^#+\s+', line):
            return True
        
        # Check for underlined headings (next line contains dashes or equals)
        # This would need context from the next line, so we'll keep it simple
        
        return False
    
    def _is_title_case(self, line: str) -> bool:
        """Check if line is in title case"""
        words = line.split()
        if len(words) < 2:
            return False
        
        # Check if first word is capitalized
        if not words[0][0].isupper():
            return False
        
        # Check if most words are capitalized (allowing for articles, prepositions)
        capitalized_count = sum(1 for word in words if word[0].isupper())
        return capitalized_count / len(words) >= 0.6
    
    def _is_list_item(self, line: str) -> bool:
        """Detect if line is a list item"""
        # Bullet points (-, *, •, ◦, etc.)
        if re.match(r'^[-*•◦▪▫‣⁃]\s+', line):
            return True
        
        # Numbered lists (1., 1), (1), a., A., i., I., etc.)
        if re.match(r'^(\d+[.)]|\([0-9]+\)|[a-zA-Z][.)]|[ivxlcdm]+[.)])\s+', line, re.IGNORECASE):
            return True
        
        # Roman numerals
        if re.match(r'^[IVXLCDM]+[.)\s]+', line, re.IGNORECASE):
            return True
        
        return False
    
    def _extract_list_content(self, line: str) -> str:
        """Extract content from list item (remove bullet/number)"""
        # Remove bullet points
        line = re.sub(r'^[-*•◦▪▫‣⁃]\s*', '', line)
        
        # Remove numbered prefixes
        line = re.sub(r'^(\d+[.)]|\([0-9]+\)|[a-zA-Z][.)]|[ivxlcdm]+[.)])\s*', '', line, flags=re.IGNORECASE)
        line = re.sub(r'^[IVXLCDM]+[.)\s]*', '', line, flags=re.IGNORECASE)
        
        return line.strip()
    
    def _get_list_type(self, line: str) -> str:
        """Determine the type of list item"""
        if re.match(r'^[-*•◦▪▫‣⁃]\s+', line):
            return 'bullet'
        elif re.match(r'^\d+[.)]', line):
            return 'numbered'
        elif re.match(r'^\([0-9]+\)', line):
            return 'numbered_parentheses'
        elif re.match(r'^[a-z][.)]', line):
            return 'alphabetic_lower'
        elif re.match(r'^[A-Z][.)]', line):
            return 'alphabetic_upper'
        elif re.match(r'^[ivxlcdm]+[.)]', line, re.IGNORECASE):
            return 'roman_numeral'
        else:
            return 'unknown'
    
    def _is_table_row(self, line: str) -> bool:
        """Detect if line represents a table row"""
        # Check for common separators
        separators = ['|', '\t', '  ', ',', ';']
        
        for sep in separators:
            if sep in line:
                parts = line.split(sep)
                # Must have at least 2 parts and reasonable length
                if len(parts) >= 2 and all(len(part.strip()) > 0 for part in parts):
                    return True
        
        # Check for aligned columns (multiple spaces)
        if re.search(r'\s{3,}', line):
            return True
        
        return False
    
    def _detect_separator(self, line: str) -> str:
        """Detect the separator used in a table row"""
        separators = ['|', '\t', ',', ';']
        
        for sep in separators:
            if sep in line:
                return sep
        
        # Check for multiple spaces
        if re.search(r'\s{3,}', line):
            return 'spaces'
        
        return 'unknown'
    
    def _parse_table_row(self, line: str) -> List[str]:
        """Parse a table row into columns"""
        separator = self._detect_separator(line)
        
        if separator == 'spaces':
            # Split on multiple spaces
            columns = re.split(r'\s{3,}', line)
        elif separator in ['|', '\t', ',', ';']:
            columns = line.split(separator)
        else:
            # Fallback: split on any whitespace
            columns = line.split()
        
        # Clean up columns
        return [col.strip() for col in columns if col.strip()]
    
    def _create_paragraph_element(self, paragraph_lines: List[str], position: int) -> StructuredElement:
        """Create a paragraph element from multiple lines"""
        content = ' '.join(paragraph_lines)
        
        # Analyze paragraph characteristics
        metadata = {
            'line_count': len(paragraph_lines),
            'word_count': len(content.split()),
            'character_count': len(content)
        }
        
        # Detect if it might be a code block
        if self._is_code_block(paragraph_lines):
            metadata['suspected_code'] = True
            element_type = 'code_block'
            confidence = 0.7
        else:
            element_type = 'paragraph'
            confidence = 0.9
        
        return StructuredElement(
            element_type=element_type,
            content=content,
            position=position,
            metadata=metadata,
            confidence=confidence
        )
    
    def _is_code_block(self, lines: List[str]) -> bool:
        """Detect if paragraph lines represent a code block"""
        # Check for common code patterns
        code_indicators = [
            r'^\s*def\s+',  # Python function
            r'^\s*class\s+',  # Python class
            r'^\s*if\s+.*:',  # Python if statement
            r'^\s*for\s+.*:',  # Python for loop
            r'^\s*while\s+.*:',  # Python while loop
            r'^\s*import\s+',  # Python import
            r'^\s*from\s+.*import',  # Python from import
            r'^\s*function\s+',  # JavaScript function
            r'^\s*var\s+',  # JavaScript var
            r'^\s*const\s+',  # JavaScript const
            r'^\s*let\s+',  # JavaScript let
            r'^\s*#include\s*<',  # C/C++ include
            r'^\s*public\s+',  # Java/C# public
            r'^\s*private\s+',  # Java/C# private
            r'^\s*\{.*\}$',  # Brackets
            r'^\s*\[.*\]$',  # Square brackets
        ]
        
        code_score = 0
        total_lines = len(lines)
        
        for line in lines:
            # Check for code patterns
            for pattern in code_indicators:
                if re.search(pattern, line):
                    code_score += 1
                    break
            
            # Check for indentation patterns
            if line.startswith('    ') or line.startswith('\t'):
                code_score += 0.5
            
            # Check for special characters common in code
            if any(char in line for char in ['{}', '[]', '()', ';', '->', '=>', '==']):
                code_score += 0.3
        
        # If more than 40% of lines look like code, consider it a code block
        return (code_score / total_lines) > 0.4