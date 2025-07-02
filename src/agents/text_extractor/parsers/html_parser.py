"""
HTML Parser Module

Research Summary:
- BeautifulSoup4 with lxml parser provides the best balance of performance and robustness
- Pandas read_html() is excellent for table extraction but limited to simple tables
- lxml is fastest but less forgiving with malformed HTML
- For complex nested tables, custom traversal with BeautifulSoup is most reliable

Challenges Addressed:
1. Nested/multiple tables - Custom recursive table extraction
2. Mixed content (tables + paragraphs + lists) - Element-by-element traversal
3. Malformed HTML - BeautifulSoup's error tolerance
4. Complex table structures - Cell spanning, nested elements
5. Semantic structure preservation - Maintains document hierarchy

Libraries Used:
- BeautifulSoup4 (bs4): Primary HTML parsing, handles malformed HTML gracefully
- lxml: Fast XML/HTML parser backend for BeautifulSoup
- pandas: Table structure validation and processing
- re: Text cleaning and pattern matching

Edge Cases Handled:
- Tables without headers, irregular cell structures
- Deeply nested elements and mixed content types
- Invalid HTML tags and missing closing tags
- Empty cells, merged cells (colspan/rowspan)
- Tables inside other elements (divs, sections)
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

try:
    from bs4 import BeautifulSoup, Tag, NavigableString
    import pandas as pd
    import lxml
except ImportError as e:
    raise ImportError(f"Required dependencies not installed: {e}. Install with: pip install beautifulsoup4 lxml pandas")


class HTMLParser:
    """
    Production-grade HTML parser that extracts structured content from HTML files.
    
    Handles complex scenarios including:
    - Multiple nested tables
    - Mixed content (paragraphs, lists, headings, tables)
    - Malformed HTML
    - Complex table structures with merged cells
    """
    
    def __init__(self):
        self.supported_elements = {
            'heading': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
            'paragraph': ['p', 'div'],
            'list': ['ul', 'ol', 'dl'],
            'table': ['table'],
            'text': ['span', 'strong', 'em', 'b', 'i', 'u']
        }
        
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse HTML file and extract structured content.
        
        Args:
            file_path (str): Path to the HTML file
            
        Returns:
            Dict[str, Any]: Standardized dictionary with metadata, content, and extraction info
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Parse with BeautifulSoup using lxml parser for speed and robustness
            soup = BeautifulSoup(content, 'lxml')
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, soup)
            
            # Extract raw text
            raw_text = self._extract_raw_text(soup)
            
            # Extract structured elements
            structured_elements = self._extract_structured_elements(soup)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(structured_elements, raw_text)
            
            return {
                "metadata": metadata,
                "content": {
                    "raw_text": raw_text,
                    "structured_elements": structured_elements
                },
                "extraction_info": {
                    "method": "html_parser",
                    "confidence_score": confidence_score
                }
            }
            
        except Exception as e:
            return self._create_error_response(file_path, str(e))
    
    def _extract_metadata(self, file_path: Path, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML file and content."""
        metadata = {
            "source_file": file_path.name,
            "file_type": "html",
            "extraction_timestamp": datetime.now().isoformat(),
            "file_size": file_path.stat().st_size if file_path.exists() else 0
        }
        
        # Extract HTML-specific metadata
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()
            
        # Meta tags
        meta_tags = soup.find_all('meta')
        meta_data = {}
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
            content = meta.get('content')
            if name and content:
                meta_data[name] = content
        
        if meta_data:
            metadata["meta_tags"] = meta_data
            
        # Document statistics
        metadata["statistics"] = {
            "total_elements": len(soup.find_all()),
            "tables": len(soup.find_all('table')),
            "paragraphs": len(soup.find_all('p')),
            "lists": len(soup.find_all(['ul', 'ol', 'dl'])),
            "headings": len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        }
        
        return metadata
    
    def _extract_raw_text(self, soup: BeautifulSoup) -> str:
        """Extract clean raw text from HTML."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _extract_structured_elements(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract structured elements maintaining document order."""
        elements = []
        position = 0
        
        # Find body or use entire document
        body = soup.find('body') or soup
        
        # Traverse all elements in document order
        for element in body.descendants:
            if isinstance(element, Tag):
                element_data = self._process_element(element, position)
                if element_data:
                    elements.append(element_data)
                    position += 1
                    
        return elements
    
    def _process_element(self, element: Tag, position: int) -> Optional[Dict[str, Any]]:
        """Process individual HTML element."""
        tag_name = element.name.lower()
        
        # Skip if element is empty or only whitespace
        text_content = self._get_clean_text(element)
        if not text_content.strip():
            return None
            
        # Process based on element type
        if tag_name in self.supported_elements['heading']:
            return self._process_heading(element, position)
        elif tag_name == 'table':
            return self._process_table(element, position)
        elif tag_name in ['ul', 'ol', 'dl']:
            return self._process_list(element, position)
        elif tag_name == 'p' or (tag_name == 'div' and self._is_paragraph_like(element)):
            return self._process_paragraph(element, position)
        
        return None
    
    def _process_heading(self, element: Tag, position: int) -> Dict[str, Any]:
        """Process heading elements."""
        level = int(element.name[1])  # h1 -> 1, h2 -> 2, etc.
        text = self._get_clean_text(element)
        
        return {
            "type": "heading",
            "content": text,
            "position": position,
            "metadata": {
                "level": level,
                "tag": element.name,
                "attributes": dict(element.attrs) if element.attrs else {}
            }
        }
    
    def _process_paragraph(self, element: Tag, position: int) -> Dict[str, Any]:
        """Process paragraph elements."""
        text = self._get_clean_text(element)
        
        # Check for inline formatting
        formatting = self._detect_inline_formatting(element)
        
        return {
            "type": "paragraph",
            "content": text,
            "position": position,
            "metadata": {
                "tag": element.name,
                "formatting": formatting,
                "attributes": dict(element.attrs) if element.attrs else {}
            }
        }
    
    def _process_list(self, element: Tag, position: int) -> Dict[str, Any]:
        """Process list elements (ul, ol, dl)."""
        list_type = element.name
        items = []
        
        if list_type in ['ul', 'ol']:
            for li in element.find_all('li', recursive=False):
                item_text = self._get_clean_text(li)
                if item_text.strip():
                    # Check for nested lists
                    nested_lists = li.find_all(['ul', 'ol'])
                    nested_data = []
                    for nested in nested_lists:
                        nested_items = [self._get_clean_text(nested_li) 
                                      for nested_li in nested.find_all('li', recursive=False)]
                        nested_data.append({
                            "type": nested.name,
                            "items": nested_items
                        })
                    
                    item_data = {"text": item_text}
                    if nested_data:
                        item_data["nested_lists"] = nested_data
                    items.append(item_data)
        
        elif list_type == 'dl':
            # Definition list
            terms = element.find_all('dt')
            definitions = element.find_all('dd')
            
            for i, term in enumerate(terms):
                term_text = self._get_clean_text(term)
                def_text = ""
                if i < len(definitions):
                    def_text = self._get_clean_text(definitions[i])
                
                items.append({
                    "term": term_text,
                    "definition": def_text
                })
        
        return {
            "type": "list",
            "content": {
                "list_type": list_type,
                "items": items
            },
            "position": position,
            "metadata": {
                "tag": element.name,
                "item_count": len(items),
                "attributes": dict(element.attrs) if element.attrs else {}
            }
        }
    
    def _process_table(self, element: Tag, position: int) -> Dict[str, Any]:
        """Process table elements with complex structure support."""
        table_data = {
            "headers": [],
            "rows": [],
            "metadata": {
                "has_header": False,
                "row_count": 0,
                "column_count": 0,
                "has_merged_cells": False
            }
        }
        
        # Extract table caption
        caption = element.find('caption')
        if caption:
            table_data["caption"] = self._get_clean_text(caption)
        
        # Find headers
        thead = element.find('thead')
        header_rows = []
        
        if thead:
            header_rows = thead.find_all('tr')
        else:
            # Check if first row contains th elements
            first_row = element.find('tr')
            if first_row and first_row.find('th'):
                header_rows = [first_row]
        
        # Process headers
        if header_rows:
            table_data["metadata"]["has_header"] = True
            for header_row in header_rows:
                header_cells = header_row.find_all(['th', 'td'])
                headers = []
                for cell in header_cells:
                    cell_text = self._get_clean_text(cell)
                    colspan = int(cell.get('colspan', 1))
                    rowspan = int(cell.get('rowspan', 1))
                    
                    cell_data = {"text": cell_text}
                    if colspan > 1 or rowspan > 1:
                        cell_data["colspan"] = colspan
                        cell_data["rowspan"] = rowspan
                        table_data["metadata"]["has_merged_cells"] = True
                    
                    headers.append(cell_data)
                
                table_data["headers"].append(headers)
        
        # Process data rows
        tbody = element.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            rows = element.find_all('tr')
            # Skip header rows if we found them
            if header_rows:
                rows = rows[len(header_rows):]
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = []
            
            for cell in cells:
                cell_text = self._get_clean_text(cell)
                colspan = int(cell.get('colspan', 1))
                rowspan = int(cell.get('rowspan', 1))
                
                cell_data = {"text": cell_text}
                if colspan > 1 or rowspan > 1:
                    cell_data["colspan"] = colspan
                    cell_data["rowspan"] = rowspan
                    table_data["metadata"]["has_merged_cells"] = True
                
                # Check for nested elements
                nested_tables = cell.find_all('table')
                if nested_tables:
                    cell_data["nested_tables"] = len(nested_tables)
                
                lists = cell.find_all(['ul', 'ol'])
                if lists:
                    cell_data["nested_lists"] = len(lists)
                
                row_data.append(cell_data)
            
            if row_data:
                table_data["rows"].append(row_data)
        
        # Update metadata
        table_data["metadata"]["row_count"] = len(table_data["rows"])
        if table_data["rows"]:
            table_data["metadata"]["column_count"] = max(len(row) for row in table_data["rows"])
        
        # Try to convert to pandas DataFrame for validation
        try:
            df_data = []
            for row in table_data["rows"]:
                df_row = [cell["text"] if isinstance(cell, dict) else str(cell) for cell in row]
                df_data.append(df_row)
            
            if df_data:
                df = pd.DataFrame(df_data)
                table_data["metadata"]["pandas_compatible"] = True
                table_data["metadata"]["shape"] = list(df.shape)
            else:
                table_data["metadata"]["pandas_compatible"] = False
        except Exception:
            table_data["metadata"]["pandas_compatible"] = False
        
        return {
            "type": "table",
            "content": table_data,
            "position": position,
            "metadata": {
                "tag": element.name,
                "attributes": dict(element.attrs) if element.attrs else {},
                **table_data["metadata"]
            }
        }
    
    def _get_clean_text(self, element: Tag) -> str:
        """Get clean text from element, preserving meaningful whitespace."""
        if isinstance(element, NavigableString):
            return str(element).strip()
        
        # Handle special elements
        if element.name in ['br']:
            return '\n'
        elif element.name in ['script', 'style']:
            return ''
        
        # Get text and clean it
        text = element.get_text(separator=' ', strip=True)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _is_paragraph_like(self, element: Tag) -> bool:
        """Determine if a div element should be treated as a paragraph."""
        # Check if div contains mainly text content
        text_length = len(self._get_clean_text(element))
        if text_length < 10:
            return False
        
        # Check if it contains block-level elements
        block_elements = element.find_all(['div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table', 'ul', 'ol'])
        if len(block_elements) > 2:  # Allow some nested elements
            return False
        
        return True
    
    def _detect_inline_formatting(self, element: Tag) -> Dict[str, bool]:
        """Detect inline formatting within an element."""
        formatting = {
            "bold": bool(element.find_all(['b', 'strong'])),
            "italic": bool(element.find_all(['i', 'em'])),
            "underline": bool(element.find_all(['u'])),
            "links": bool(element.find_all(['a'])),
            "code": bool(element.find_all(['code'])),
        }
        return formatting
    
    def _calculate_confidence_score(self, structured_elements: List[Dict], raw_text: str) -> float:
        """Calculate confidence score based on extraction quality."""
        if not structured_elements:
            return 0.1
        
        # Base score
        score = 0.5
        
        # Bonus for variety of element types
        element_types = set(elem['type'] for elem in structured_elements)
        score += len(element_types) * 0.1
        
        # Bonus for tables (complex structure)
        table_count = sum(1 for elem in structured_elements if elem['type'] == 'table')
        score += min(table_count * 0.1, 0.3)
        
        # Bonus for good text coverage
        total_element_text = sum(len(str(elem.get('content', ''))) for elem in structured_elements)
        if total_element_text > 0:
            coverage_ratio = min(total_element_text / max(len(raw_text), 1), 1.0)
            score += coverage_ratio * 0.2
        
        return min(score, 1.0)
    
    def _create_error_response(self, file_path: Union[str, Path], error: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "metadata": {
                "source_file": str(file_path),
                "file_type": "html",
                "extraction_timestamp": datetime.now().isoformat(),
                "error": error
            },
            "content": {
                "raw_text": "",
                "structured_elements": []
            },
            "extraction_info": {
                "method": "html_parser",
                "confidence_score": 0.0
            }
        }


# Example usage and testing
if __name__ == "__main__":
    parser = HTMLParser()
    
    # Test with a sample HTML string
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Document</title>
        <meta name="description" content="Test HTML document">
    </head>
    <body>
        <h1>Main Title</h1>
        <p>This is a <strong>test paragraph</strong> with <em>formatting</em>.</p>
        
        <h2>Data Table</h2>
        <table border="1">
            <tr>
                <th>Name</th>
                <th colspan="2">Details</th>
            </tr>
            <tr>
                <td>John</td>
                <td>Age: 30</td>
                <td>City: NYC</td>
            </tr>
            <tr>
                <td>Jane</td>
                <td>Age: 25</td>
                <td>City: LA</td>
            </tr>
        </table>
        
        <h3>Features</h3>
        <ul>
            <li>Feature 1</li>
            <li>Feature 2
                <ul>
                    <li>Sub-feature A</li>
                    <li>Sub-feature B</li>
                </ul>
            </li>
            <li>Feature 3</li>
        </ul>
    </body>
    </html>
    """
    
    # Save test HTML to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(test_html)
        temp_path = f.name
    
    try:
        result = parser.parse(temp_path)
        print(json.dumps(result, indent=2))
    finally:
        os.unlink(temp_path)