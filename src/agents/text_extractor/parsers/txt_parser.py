"""
TXT Parser Module

Research Summary:
- Text file parsing requires sophisticated pattern recognition for structure detection
- Regular expressions are essential for identifying headers, lists, tables, and sections
- Natural language processing can improve content classification
- Statistical analysis helps detect tabular data and formatting patterns

Challenges Addressed:
1. Unstructured text with hidden structure - Pattern matching and heuristics
2. Mixed content types - Tables embedded in paragraphs, lists, etc.
3. Inconsistent formatting - Varying indentation, spacing, delimiters
4. Large text files - Memory-efficient processing
5. Various text encodings - Robust encoding detection
6. Table detection in plain text - Delimiter and alignment analysis

Libraries Used:
- re: Pattern matching for structure detection
- chardet: Encoding detection for robust file reading
- pandas: CSV-like table processing when patterns detected
- nltk/spacy: Optional NLP for advanced text analysis
- difflib: Similarity matching for structure detection

Edge Cases Handled:
- Files with mixed line endings (Windows/Unix)
- Tables with irregular spacing or delimiters
- Nested lists with varying indentation
- Code blocks and formatted sections
- Very long lines or paragraphs
- Empty lines and inconsistent spacing
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import chardet
import io

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False


class TXTParser:
    """
    Production-grade TXT parser that extracts structured content from plain text files.
    
    Handles complex scenarios including:
    - Tables in plain text (delimited and aligned)
    - Hierarchical lists and nested structures
    - Mixed content (paragraphs, tables, lists, code blocks)
    - Various text encodings and line endings
    - Large text files with efficient processing
    """
    
    def __init__(self, max_file_size: int = 50*1024*1024):
        """
        Initialize TXT parser with configuration.
        
        Args:
            max_file_size: Maximum file size in bytes for processing
        """
        self.max_file_size = max_file_size
        
        # Compile regex patterns for performance
        self.patterns = {
            'header': re.compile(r'^(#{1,6}\s+.*|={3,}|_{3,}|-{3,}|\*{3,}|[A-Z][A-Z\s]{10,}|\d+\.\s+[A-Z].*|\w+:?\s*\n[=-]{3,})$', re.MULTILINE),
            'list_item': re.compile(r'^(\s*)([-*+•]|\d+[\.\)]|\([a-zA-Z0-9]+\))\s+(.+)$', re.MULTILINE),
            'table_delimiter': re.compile(r'[|,;\t]'),
            'code_block': re.compile(r'```[\s\S]*?```|~~~[\s\S]*?~~~|^    .*$', re.MULTILINE),
            'bullet_points': re.compile(r'^(\s*)([-*+•·])\s+(.+)$', re.MULTILINE),
            'numbered_list': re.compile(r'^(\s*)(\d+[.\)]))\s+(.+)$', re.MULTILINE),
            'key_value': re.compile(r'^([^:\n]+):\s*(.+)$', re.MULTILINE),
            'section_separator': re.compile(r'^([=-]{3,}|\*{3,}|_{3,})$', re.MULTILINE),
            'whitespace_table': re.compile(r'^\s*\S+(\s{2,}\S+){2,}\s*$', re.MULTILINE)
        }
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse TXT file and extract structured content.
        
        Args:
            file_path (str): Path to the text file
            
        Returns:
            Dict[str, Any]: Standardized dictionary with metadata, content, and extraction info
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                raise ValueError(f"File too large: {file_size} bytes (max: {self.max_file_size})")
            
            # Read file with encoding detection
            content = self._read_file_with_encoding(file_path)
            
            # Preprocess content
            content = self._preprocess_content(content)
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, content, file_size)
            
            # Split content into lines for processing
            lines = content.split('\n')
            
            # Extract structured elements
            structured_elements = self._extract_structured_elements(lines, content)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(structured_elements, content)
            
            return {
                "metadata": metadata,
                "content": {
                    "raw_text": content,
                    "structured_elements": structured_elements
                },
                "extraction_info": {
                    "method": "txt_parser",
                    "confidence_score": confidence_score
                }
            }
            
        except Exception as e:
            return self._create_error_response(file_path, str(e))
    
    def _read_file_with_encoding(self, file_path: Path) -> str:
        """Read file with automatic encoding detection."""
        # First, try to detect encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
        
        detected_encoding = chardet.detect(raw_data)
        encoding = detected_encoding.get('encoding', 'utf-8')
        
        # Try detected encoding first, fallback to common encodings
        encodings = [encoding, 'utf-8', 'latin-1', 'cp1252', 'ascii']
        
        for enc in encodings:
            try:
                return raw_data.decode(enc)
            except (UnicodeDecodeError, TypeError):
                continue
        
        # Final fallback with error handling
        return raw_data.decode('utf-8', errors='replace')
    
    def _preprocess_content(self, content: str) -> str:
        """Preprocess content to normalize formatting."""
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive blank lines (more than 2 consecutive)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Normalize tabs to spaces
        content = content.expandtabs(4)
        
        return content.strip()
    
    def _extract_metadata(self, file_path: Path, content: str, file_size: int) -> Dict[str, Any]:
        """Extract metadata from text file and content."""
        lines = content.split('\n')
        
        metadata = {
            "source_file": file_path.name,
            "file_type": "txt",
            "extraction_timestamp": datetime.now().isoformat(),
            "file_size": file_size
        }
        
        # Content statistics
        metadata["statistics"] = {
            "line_count": len(lines),
            "word_count": len(content.split()),
            "character_count": len(content),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "average_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0
        }
        
        # Detect content patterns
        patterns_found = {}
        
        # Check for various structural patterns
        if self.patterns['table_delimiter'].search(content):
            patterns_found['delimited_tables'] = len(self.patterns['table_delimiter'].findall(content))
        
        if self.patterns['list_item'].search(content):
            patterns_found['lists'] = len(self.patterns['list_item'].findall(content))
        
        if self.patterns['header'].search(content):
            patterns_found['headers'] = len(self.patterns['header'].findall(content))
        
        if self.patterns['code_block'].search(content):
            patterns_found['code_blocks'] = len(self.patterns['code_block'].findall(content))
        
        if patterns_found:
            metadata["detected_patterns"] = patterns_found
        
        # Detect potential encoding issues
        if '�' in content or content.count('?') > len(content) * 0.01:
            metadata["encoding_issues"] = True
        
        return metadata
    
    def _extract_structured_elements(self, lines: List[str], content: str) -> List[Dict[str, Any]]:
        """Extract structured elements from text content."""
        elements = []
        position = 0
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Skip empty lines
            if not line.strip():
                i += 1
                continue
            
            # Try to identify element type and process
            element, lines_consumed = self._identify_and_process_element(lines, i, position)
            
            if element:
                elements.append(element)
                position += 1
            
            i += lines_consumed if lines_consumed > 0 else 1
        
        return elements
    
    def _identify_and_process_element(self, lines: List[str], start_idx: int, position: int) -> Tuple[Optional[Dict[str, Any]], int]:
        """Identify and process element starting at given line index."""
        if start_idx >= len(lines):
            return None, 0
        
        current_line = lines[start_idx]
        
        # Check for headers
        if self._is_header(current_line, lines, start_idx):
            return self._process_header(current_line, position), 1
        
        # Check for lists
        list_element, list_lines = self._try_process_list(lines, start_idx, position)
        if list_element:
            return list_element, list_lines
        
        # Check for tables
        table_element, table_lines = self._try_process_table(lines, start_idx, position)
        if table_element:
            return table_element, table_lines
        
        # Check for code blocks
        code_element, code_lines = self._try_process_code_block(lines, start_idx, position)
        if code_element:
            return code_element, code_lines
        
        # Check for key-value pairs
        if self.patterns['key_value'].match(current_line):
            return self._process_key_value_section(lines, start_idx, position)
        
        # Default to paragraph
        paragraph_element, paragraph_lines = self._process_paragraph(lines, start_idx, position)
        return paragraph_element, paragraph_lines
    
    def _is_header(self, line: str, lines: List[str], idx: int) -> bool:
        """Check if line is a header."""
        # Markdown-style headers
        if re.match(r'^#{1,6}\s+', line):
            return True
        
        # Underlined headers
        if idx + 1 < len(lines):
            next_line = lines[idx + 1]
            if re.match(r'^[=-]{3,}$', next_line.strip()):
                return True
        
        # All caps headers (short lines)
        if len(line.strip()) <= 50 and line.strip().isupper() and len(line.strip().split()) <= 8:
            return True
        
        # Numbered section headers
        if re.match(r'^\d+(\.\d+)*\.?\s+[A-Z]', line):
            return True
        
        return False
    
    def _process_header(self, line: str, position: int) -> Dict[str, Any]:
        """Process header line."""
        # Determine header level
        level = 1
        
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
        elif line.strip().isupper():
            level = 1
        elif re.match(r'^\d+\.\s+', line):
            level = 2
        
        text = re.sub(r'^#{1,6}\s*', '', line).strip()
        
        return {
            "type": "heading",
            "content": text,
            "position": position,
            "metadata": {
                "level": level,
                "original_line": line,
                "formatting": "markdown" if line.startswith('#') else "plain"
            }
        }
    
    def _try_process_list(self, lines: List[str], start_idx: int, position: int) -> Tuple[Optional[Dict[str, Any]], int]:
        """Try to process list starting at given index."""
        if start_idx >= len(lines):
            return None, 0
        
        first_line = lines[start_idx]
        
        # Check if first line is a list item
        if not (self.patterns['bullet_points'].match(first_line) or 
                self.patterns['numbered_list'].match(first_line)):
            return None, 0
        
        # Collect consecutive list items
        list_items = []
        i = start_idx
        list_type = "bulleted" if self.patterns['bullet_points'].match(first_line) else "numbered"
        
        while i < len(lines):
            line = lines[i]
            
            if not line.strip():
                i += 1
                continue
            
            # Check for list item
            bullet_match = self.patterns['bullet_points'].match(line)
            number_match = self.patterns['numbered_list'].match(line)
            
            if bullet_match:
                indent, marker, text = bullet_match.groups()
                list_items.append({
                    "text": text.strip(),
                    "indent_level": len(indent) // 2,
                    "marker": marker
                })
                i += 1
            elif number_match:
                indent, marker, text = number_match.groups()
                list_items.append({
                    "text": text.strip(),
                    "indent_level": len(indent) // 2,
                    "marker": marker
                })
                i += 1
            else:
                break
        
        if not list_items:
            return None, 0
        
        # Process nested structure
        nested_items = self._build_nested_list(list_items)
        
        return {
            "type": "list",
            "content": {
                "list_type": list_type,
                "items": nested_items
            },
            "position": position,
            "metadata": {
                "item_count": len(list_items),
                "has_nesting": any(item["indent_level"] > 0 for item in list_items),
                "max_indent_level": max(item["indent_level"] for item in list_items) if list_items else 0
            }
        }, i - start_idx
    
    def _build_nested_list(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build nested list structure from flat list items."""
        if not items:
            return []
        
        result = []
        i = 0
        
        while i < len(items):
            item = items[i]
            
            # Handle root level items
            if item["indent_level"] == 0:
                # Check if this item has children
                children = []
                j = i + 1
                while j < len(items) and items[j]["indent_level"] > 0:
                    if items[j]["indent_level"] == 1:
                        # Direct child
                        child_item = {
                            "text": items[j]["text"],
                            "marker": items[j]["marker"]
                        }
                        
                        # Check for grandchildren
                        grandchildren = []
                        k = j + 1
                        while k < len(items) and items[k]["indent_level"] > 1:
                            if items[k]["indent_level"] == 2:
                                grandchildren.append({
                                    "text": items[k]["text"],
                                    "marker": items[k]["marker"]
                                })
                            k += 1
                        
                        if grandchildren:
                            child_item["children"] = grandchildren
                        
                        children.append(child_item)
                        j = k
                    else:
                        j += 1
                
                root_item = {
                    "text": item["text"],
                    "marker": item["marker"]
                }
                
                if children:
                    root_item["children"] = children
                
                result.append(root_item)
                i = j if j > i + 1 else i + 1
            else:
                i += 1
        
        return result

    def _try_process_table(self, lines: List[str], start_idx: int, position: int) -> Tuple[Optional[Dict[str, Any]], int]:
        """Try to process table starting at given index."""
        if start_idx >= len(lines):
            return None, 0
        
        # Look ahead to detect table patterns
        table_lines = []
        i = start_idx
        
        # Check for delimited table (CSV-like, pipe-separated, etc.)
        delimiter_counts = {}
        
        while i < len(lines) and i < start_idx + 20:  # Look ahead max 20 lines
            line = lines[i].strip()
            
            if not line:
                if table_lines:  # Empty line after table content
                    break
                i += 1
                continue
            
            # Count delimiters
            for delimiter in [',', '|', '\t', ';']:
                count = line.count(delimiter)
                if count > 0:
                    if delimiter not in delimiter_counts:
                        delimiter_counts[delimiter] = []
                    delimiter_counts[delimiter].append(count)
            
            # Check for whitespace-aligned table
            if self.patterns['whitespace_table'].match(line):
                table_lines.append(line)
            
            # Check for consistent delimiter pattern
            consistent_delimiter = None
            for delim, counts in delimiter_counts.items():
                if len(counts) >= 2 and len(set(counts)) == 1 and counts[0] >= 2:
                    consistent_delimiter = delim
                    break
            
            if consistent_delimiter or self.patterns['whitespace_table'].match(line):
                table_lines.append(line)
            else:
                if table_lines:
                    break
            
            i += 1
        
        if len(table_lines) < 2:  # Need at least 2 rows to be a table
            return None, 0
        
        # Determine table type and parse
        if consistent_delimiter:
            return self._process_delimited_table(table_lines, consistent_delimiter, position), len(table_lines)
        else:
            return self._process_whitespace_table(table_lines, position), len(table_lines)

    def _process_delimited_table(self, lines: List[str], delimiter: str, position: int) -> Dict[str, Any]:
        """Process delimited table (CSV-like)."""
        if not pd:
            # Fallback without pandas
            rows = []
            for line in lines:
                rows.append([cell.strip() for cell in line.split(delimiter)])
            
            # Assume first row is header
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            
            return {
                "type": "table",
                "content": {
                    "headers": headers,
                    "rows": data_rows,
                    "format": "delimited"
                },
                "position": position,
                "metadata": {
                    "delimiter": delimiter,
                    "row_count": len(data_rows),
                    "column_count": len(headers),
                    "has_headers": True
                }
            }
        
        # Using pandas for robust parsing
        try:
            # Create StringIO from lines
            table_text = '\n'.join(lines)
            df = pd.read_csv(io.StringIO(table_text), sep=delimiter, skipinitialspace=True)
            
            headers = df.columns.tolist()
            rows = df.values.tolist()
            
            return {
                "type": "table",
                "content": {
                    "headers": headers,
                    "rows": rows,
                    "format": "delimited"
                },
                "position": position,
                "metadata": {
                    "delimiter": delimiter,
                    "row_count": len(rows),
                    "column_count": len(headers),
                    "has_headers": True,
                    "data_types": df.dtypes.to_dict()
                }
            }
        except Exception:
            # Fallback to manual parsing
            return self._manual_table_parse(lines, delimiter, position)

    def _process_whitespace_table(self, lines: List[str], position: int) -> Dict[str, Any]:
        """Process whitespace-aligned table."""
        # Analyze column positions
        column_starts = set()
        
        for line in lines:
            words = []
            current_pos = 0
            for char in line:
                if char != ' ' and (current_pos == 0 or line[current_pos-1] == ' '):
                    column_starts.add(current_pos)
                current_pos += 1
        
        column_starts = sorted(list(column_starts))
        
        # Extract columns
        rows = []
        for line in lines:
            row = []
            for i, start in enumerate(column_starts):
                end = column_starts[i+1] if i+1 < len(column_starts) else len(line)
                cell = line[start:end].strip()
                row.append(cell)
            rows.append(row)
        
        # Assume first row is header
        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []
        
        return {
            "type": "table",
            "content": {
                "headers": headers,
                "rows": data_rows,
                "format": "whitespace_aligned"
            },
            "position": position,
            "metadata": {
                "row_count": len(data_rows),
                "column_count": len(headers),
                "has_headers": True,
                "column_positions": column_starts
            }
        }

    def _manual_table_parse(self, lines: List[str], delimiter: str, position: int) -> Dict[str, Any]:
        """Manual table parsing fallback."""
        rows = []
        for line in lines:
            # Split by delimiter and clean
            cells = [cell.strip().strip('"\'') for cell in line.split(delimiter)]
            rows.append(cells)
        
        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []
        
        return {
            "type": "table",
            "content": {
                "headers": headers,
                "rows": data_rows,
                "format": "delimited"
            },
            "position": position,
            "metadata": {
                "delimiter": delimiter,
                "row_count": len(data_rows),
                "column_count": len(headers),
                "has_headers": True,
                "parsing_method": "manual_fallback"
            }
        }

    def _try_process_code_block(self, lines: List[str], start_idx: int, position: int) -> Tuple[Optional[Dict[str, Any]], int]:
        """Try to process code block starting at given index."""
        if start_idx >= len(lines):
            return None, 0
        
        first_line = lines[start_idx]
        
        # Markdown-style code blocks
        if first_line.strip().startswith('```') or first_line.strip().startswith('~~~'):
            delimiter = '```' if '```' in first_line else '~~~'
            language = first_line.strip()[3:].strip() if first_line.strip().startswith('```') else first_line.strip()[3:].strip()
            
            code_lines = []
            i = start_idx + 1
            
            while i < len(lines):
                if lines[i].strip() == delimiter:
                    break
                code_lines.append(lines[i])
                i += 1
            
            return {
                "type": "code_block",
                "content": {
                    "code": '\n'.join(code_lines),
                    "language": language or "text",
                    "format": "fenced"
                },
                "position": position,
                "metadata": {
                    "line_count": len(code_lines),
                    "delimiter": delimiter
                }
            }, i - start_idx + 1
        
        # Indented code blocks (4 spaces or 1 tab)
        if first_line.startswith('    ') or first_line.startswith('\t'):
            code_lines = []
            i = start_idx
            
            while i < len(lines):
                line = lines[i]
                if line.startswith('    ') or line.startswith('\t') or not line.strip():
                    code_lines.append(line[4:] if line.startswith('    ') else line[1:] if line.startswith('\t') else line)
                    i += 1
                else:
                    break
            
            # Remove trailing empty lines
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            
            if code_lines:
                return {
                    "type": "code_block",
                    "content": {
                        "code": '\n'.join(code_lines),
                        "language": "text",
                        "format": "indented"
                    },
                    "position": position,
                    "metadata": {
                        "line_count": len(code_lines)
                    }
                }, i - start_idx
        
        return None, 0

    def _process_key_value_section(self, lines: List[str], start_idx: int, position: int) -> Tuple[Dict[str, Any], int]:
        """Process key-value pairs section."""
        pairs = {}
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            
            if not line.strip():
                i += 1
                continue
            
            match = self.patterns['key_value'].match(line)
            if match:
                key, value = match.groups()
                pairs[key.strip()] = value.strip()
                i += 1
            else:
                break
        
        return {
            "type": "key_value_pairs",
            "content": pairs,
            "position": position,
            "metadata": {
                "pair_count": len(pairs),
                "keys": list(pairs.keys())
            }
        }, i - start_idx

    def _process_paragraph(self, lines: List[str], start_idx: int, position: int) -> Tuple[Dict[str, Any], int]:
        """Process paragraph (consecutive non-empty lines)."""
        paragraph_lines = []
        i = start_idx
        
        while i < len(lines):
            line = lines[i]
            
            if not line.strip():
                break
            
            # Stop if we hit a special element
            if (self._is_header(line, lines, i) or 
                self.patterns['list_item'].match(line) or
                self.patterns['code_block'].match(line) or
                line.strip().startswith('```')):
                break
            
            paragraph_lines.append(line)
            i += 1
        
        if not paragraph_lines:
            return None, 0
        
        text = ' '.join(line.strip() for line in paragraph_lines)
        
        # Basic text analysis
        word_count = len(text.split())
        sentence_count = len([s for s in text.split('.') if s.strip()])
        
        return {
            "type": "paragraph",
            "content": text,
            "position": position,
            "metadata": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "line_count": len(paragraph_lines)
            }
        }, i - start_idx

    def _calculate_confidence_score(self, elements: List[Dict[str, Any]], content: str) -> float:
        """Calculate confidence score for extraction quality."""
        if not elements:
            return 0.0
        
        scores = []
        
        # Structure diversity score
        element_types = set(elem["type"] for elem in elements)
        diversity_score = min(len(element_types) / 5.0, 1.0)  # Normalize to max 5 types
        scores.append(diversity_score * 0.3)
        
        # Content coverage score
        total_extracted_chars = sum(len(str(elem.get("content", ""))) for elem in elements)
        coverage_score = min(total_extracted_chars / len(content), 1.0)
        scores.append(coverage_score * 0.4)
        
        # Structure quality score
        structured_elements = [e for e in elements if e["type"] in ["table", "list", "heading"]]
        structure_score = min(len(structured_elements) / max(len(elements), 1), 1.0)
        scores.append(structure_score * 0.3)
        
        return sum(scores)

    def _create_error_response(self, file_path: Union[str, Path], error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "metadata": {
                "source_file": str(file_path),
                "file_type": "txt",
                "extraction_timestamp": datetime.now().isoformat(),
                "error": error_message
            },
            "content": {
                "raw_text": "",
                "structured_elements": []
            },
            "extraction_info": {
                "method": "txt_parser",
                "confidence_score": 0.0,
                "error": error_message
            }
        }