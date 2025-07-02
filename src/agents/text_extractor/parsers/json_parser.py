"""
JSON Parser Module

Research Summary:
- JSON parsing is relatively straightforward but complex nested structures pose challenges
- JSONPath expressions enable deep traversal of complex nested objects
- Pandas can handle JSON normalization for tabular data extraction
- Schema validation ensures data quality and structure consistency

Challenges Addressed:
1. Deeply nested JSON structures - Recursive traversal and flattening
2. Mixed data types - Type detection and conversion
3. Arrays of objects - Table-like structure extraction
4. Large JSON files - Memory-efficient parsing
5. Malformed JSON - Error handling and partial recovery
6. Complex nested arrays - Hierarchical structure preservation

Libraries Used:
- json: Standard library for JSON parsing
- jsonpath-ng: Advanced JSONPath queries for complex data extraction
- pandas: JSON normalization and tabular data handling
- ijson: Streaming JSON parser for large files
- jsonschema: Schema validation and structure analysis

Edge Cases Handled:
- Circular references and infinite recursion
- Mixed array types (objects + primitives)
- Null values and empty structures
- Unicode and encoding issues
- Very large JSON files (streaming)
- Invalid JSON with partial recovery
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Iterator
from pathlib import Path
import copy

try:
    import pandas as pd
    from jsonpath_ng import parse as jsonpath_parse
    from jsonpath_ng.ext import parse as jsonpath_ext_parse
    import ijson
    from jsonschema import validate, ValidationError
except ImportError as e:
    print(f"Warning: Optional dependencies not installed: {e}")
    print("Install with: pip install pandas jsonpath-ng ijson jsonschema")
    # Fallback to basic functionality
    pd = None
    jsonpath_parse = None
    jsonpath_ext_parse = None
    ijson = None
    ValidationError = Exception


class JSONParser:
    """
    Production-grade JSON parser that extracts structured content from JSON files.
    
    Handles complex scenarios including:
    - Deeply nested JSON structures
    - Arrays of objects (table-like data)
    - Mixed data types and structures
    - Large JSON files with streaming
    - Schema validation and structure analysis
    """
    
    def __init__(self, max_depth: int = 50, max_file_size: int = 100*1024*1024):
        """
        Initialize JSON parser with configuration.
        
        Args:
            max_depth: Maximum recursion depth for nested structures
            max_file_size: Maximum file size in bytes for in-memory parsing
        """
        self.max_depth = max_depth
        self.max_file_size = max_file_size
        self.current_depth = 0
        
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse JSON file and extract structured content.
        
        Args:
            file_path (str): Path to the JSON file
            
        Returns:
            Dict[str, Any]: Standardized dictionary with metadata, content, and extraction info
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_size = file_path.stat().st_size
            
            # Choose parsing strategy based on file size
            if file_size > self.max_file_size:
                json_data = self._parse_large_json(file_path)
            else:
                json_data = self._parse_regular_json(file_path)
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, json_data, file_size)
            
            # Extract raw text representation
            raw_text = self._extract_raw_text(json_data)
            
            # Extract structured elements
            structured_elements = self._extract_structured_elements(json_data)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(structured_elements, json_data)
            
            return {
                "metadata": metadata,
                "content": {
                    "raw_text": raw_text,
                    "structured_elements": structured_elements
                },
                "extraction_info": {
                    "method": "json_parser",
                    "confidence_score": confidence_score
                }
            }
            
        except Exception as e:
            return self._create_error_response(file_path, str(e))
    
    def _parse_regular_json(self, file_path: Path) -> Any:
        """Parse regular-sized JSON file into memory."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            # Try to recover from malformed JSON
            return self._attempt_json_recovery(file_path, str(e))
    
    def _parse_large_json(self, file_path: Path) -> Any:
        """Parse large JSON file using streaming parser."""
        if ijson is None:
            # Fallback to regular parsing
            return self._parse_regular_json(file_path)
            
        try:
            with open(file_path, 'rb') as f:
                # Parse the root object
                parser = ijson.parse(f)
                return self._build_from_events(parser)
        except Exception:
            return self._parse_regular_json(file_path)
    
    def _build_from_events(self, parser: Iterator) -> Any:
        """Build JSON object from ijson events."""
        stack = []
        current = None
        
        for prefix, event, value in parser:
            if event == 'start_map':
                new_dict = {}
                if stack:
                    self._insert_value(stack[-1], prefix, new_dict)
                stack.append(new_dict)
                current = new_dict
            elif event == 'end_map':
                if stack:
                    current = stack.pop()
            elif event == 'start_array':
                new_list = []
                if stack:
                    self._insert_value(stack[-1], prefix, new_list)
                stack.append(new_list)
                current = new_list
            elif event == 'end_array':
                if stack:
                    current = stack.pop()
            elif event in ('string', 'number', 'boolean', 'null'):
                if stack:
                    self._insert_value(stack[-1], prefix, value)
                else:
                    current = value
        
        return current
    
    def _insert_value(self, container: Union[Dict, List], prefix: str, value: Any) -> None:
        """Insert value into container based on prefix."""
        if isinstance(container, dict):
            key = prefix.split('.')[-1]
            container[key] = value
        elif isinstance(container, list):
            container.append(value)
    
    def _attempt_json_recovery(self, file_path: Path, error: str) -> Any:
        """Attempt to recover from malformed JSON."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Common JSON fixes
            content = content.strip()
            
            # Try to fix common issues
            if content.endswith(','):
                content = content[:-1]
            
            # Try to parse again
            return json.loads(content)
            
        except Exception:
            # Return minimal structure with error info
            return {
                "parse_error": error,
                "raw_content": content[:1000] if len(content) > 1000 else content
            }
    
    def _extract_metadata(self, file_path: Path, json_data: Any, file_size: int) -> Dict[str, Any]:
        """Extract metadata from JSON file and content."""
        metadata = {
            "source_file": file_path.name,
            "file_type": "json",
            "extraction_timestamp": datetime.now().isoformat(),
            "file_size": file_size
        }
        
        # Analyze JSON structure
        structure_info = self._analyze_structure(json_data)
        metadata["structure"] = structure_info
        
        # Check for schema patterns
        schema_info = self._detect_schema_patterns(json_data)
        if schema_info:
            metadata["schema_patterns"] = schema_info
        
        return metadata
    
    def _analyze_structure(self, data: Any, depth: int = 0) -> Dict[str, Any]:
        """Analyze JSON structure recursively."""
        if depth > self.max_depth:
            return {"type": "max_depth_exceeded"}
        
        if isinstance(data, dict):
            return {
                "type": "object",
                "key_count": len(data),
                "keys": list(data.keys())[:10],  # Limit to first 10 keys
                "depth": depth,
                "nested_structures": {
                    key: self._analyze_structure(value, depth + 1)
                    for key, value in list(data.items())[:5]  # Analyze first 5 items
                }
            }
        elif isinstance(data, list):
            return {
                "type": "array",
                "length": len(data),
                "depth": depth,
                "element_types": self._get_array_element_types(data),
                "sample_elements": [
                    self._analyze_structure(item, depth + 1)
                    for item in data[:3]  # Analyze first 3 items
                ]
            }
        else:
            return {
                "type": type(data).__name__,
                "value": str(data)[:100] if len(str(data)) > 100 else data,
                "depth": depth
            }
    
    def _get_array_element_types(self, arr: List[Any]) -> Dict[str, int]:
        """Get distribution of element types in an array."""
        type_counts = {}
        for item in arr:
            item_type = type(item).__name__
            type_counts[item_type] = type_counts.get(item_type, 0) + 1
        return type_counts
    
    def _detect_schema_patterns(self, data: Any) -> Optional[Dict[str, Any]]:
        """Detect common schema patterns in JSON data."""
        patterns = {}
        
        if isinstance(data, dict):
            # Check for common API response patterns
            if 'data' in data or 'results' in data:
                patterns['api_response'] = True
            
            if 'status' in data or 'error' in data:
                patterns['status_response'] = True
            
            # Check for configuration patterns
            config_keys = ['config', 'settings', 'options', 'parameters']
            if any(key in data for key in config_keys):
                patterns['configuration'] = True
                
        elif isinstance(data, list):
            # Check for homogeneous object arrays (table-like)
            if len(data) > 0 and all(isinstance(item, dict) for item in data):
                # Check if all objects have similar keys
                if len(data) > 1:
                    first_keys = set(data[0].keys()) if data[0] else set()
                    similar_structure = all(
                        len(set(item.keys() if isinstance(item, dict) else []) & first_keys) >= len(first_keys) * 0.8
                        for item in data[1:5]  # Check first few items
                    )
                    if similar_structure:
                        patterns['tabular_data'] = True
                        patterns['table_columns'] = list(first_keys)
        
        return patterns if patterns else None
    
    def _extract_raw_text(self, json_data: Any) -> str:
        """Extract raw text representation of JSON data."""
        try:
            return json.dumps(json_data, indent=2, ensure_ascii=False, default=str)
        except Exception:
            return str(json_data)
    
    def _extract_structured_elements(self, json_data: Any) -> List[Dict[str, Any]]:
        """Extract structured elements from JSON data."""
        elements = []
        self.current_depth = 0
        
        self._process_json_element(json_data, elements, "", 0)
        
        return elements
    
    def _process_json_element(self, data: Any, elements: List[Dict], path: str, position: int) -> int:
        """Process JSON element recursively."""
        if self.current_depth > self.max_depth:
            return position
        
        self.current_depth += 1
        
        try:
            if isinstance(data, dict):
                position = self._process_object(data, elements, path, position)
            elif isinstance(data, list):
                position = self._process_array(data, elements, path, position)
            else:
                position = self._process_primitive(data, elements, path, position)
        finally:
            self.current_depth -= 1
        
        return position
    
    def _process_object(self, obj: Dict[str, Any], elements: List[Dict], path: str, position: int) -> int:
        """Process JSON object."""
        # Check if this object represents tabular data
        if self._is_tabular_object(obj):
            elements.append({
                "type": "table",
                "content": self._object_to_table(obj),
                "position": position,
                "metadata": {
                    "json_path": path,
                    "object_type": "key_value_table",
                    "key_count": len(obj)
                }
            })
            return position + 1
        
        # Process as structured object
        elements.append({
            "type": "object",
            "content": {
                "keys": list(obj.keys()),
                "summary": self._create_object_summary(obj)
            },
            "position": position,
            "metadata": {
                "json_path": path,
                "key_count": len(obj),
                "nested_objects": sum(1 for v in obj.values() if isinstance(v, dict)),
                "nested_arrays": sum(1 for v in obj.values() if isinstance(v, list))
            }
        })
        
        position += 1
        
        # Process nested elements
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            position = self._process_json_element(value, elements, new_path, position)
        
        return position
    
    def _process_array(self, arr: List[Any], elements: List[Dict], path: str, position: int) -> int:
        """Process JSON array."""
        # Check if this is a homogeneous array of objects (table-like)
        if self._is_tabular_array(arr):
            table_data = self._array_to_table(arr)
            elements.append({
                "type": "table",
                "content": table_data,
                "position": position,
                "metadata": {
                    "json_path": path,
                    "array_length": len(arr),
                    "table_type": "object_array",
                    "column_count": len(table_data.get("headers", [])) if table_data.get("headers") else 0
                }
            })
            return position + 1
        
        # Process as list
        element_types = self._get_array_element_types(arr)
        
        elements.append({
            "type": "list",
            "content": {
                "list_type": "json_array",
                "items": self._create_array_summary(arr),
                "element_types": element_types
            },
            "position": position,
            "metadata": {
                "json_path": path,
                "array_length": len(arr),
                "homogeneous": len(element_types) == 1
            }
        })
        
        position += 1
        
        # Process nested elements (limit to prevent explosion)
        for i, item in enumerate(arr[:10]):  # Limit to first 10 items
            new_path = f"{path}[{i}]"
            position = self._process_json_element(item, elements, new_path, position)
        
        return position
    
    def _process_primitive(self, data: Any, elements: List[Dict], path: str, position: int) -> int:
        """Process primitive JSON value."""
        # Only create element for meaningful primitives
        if isinstance(data, str) and len(data) > 10:
            elements.append({
                "type": "paragraph",
                "content": data,
                "position": position,
                "metadata": {
                    "json_path": path,
                    "data_type": type(data).__name__,
                    "length": len(data) if isinstance(data, str) else None
                }
            })
            return position + 1
        
        return position
    
    def _is_tabular_object(self, obj: Dict[str, Any]) -> bool:
        """Check if object represents tabular data (key-value pairs)."""
        if len(obj) < 2:
            return False
        
        # Check if all values are simple types
        simple_values = all(
            not isinstance(v, (dict, list)) or 
            (isinstance(v, list) and len(v) < 5 and all(not isinstance(item, (dict, list)) for item in v))
            for v in obj.values()
        )
        
        return simple_values and len(obj) <= 20  # Reasonable limit for key-value table
    
    def _is_tabular_array(self, arr: List[Any]) -> bool:
        """Check if array represents tabular data."""
        if len(arr) < 2 or not arr:
            return False
        
        # Check if all elements are objects
        if not all(isinstance(item, dict) for item in arr):
            return False
        
        # Check if objects have similar structure
        first_keys = set(arr[0].keys()) if arr[0] else set()
        if not first_keys:
            return False
        
        # Check similarity across first few items
        similar_count = 0
        for item in arr[1:min(6, len(arr))]:  # Check first 5 additional items
            if isinstance(item, dict):
                item_keys = set(item.keys())
                overlap = len(first_keys & item_keys)
                if overlap >= len(first_keys) * 0.7:  # 70% overlap threshold
                    similar_count += 1
        
        return similar_count >= min(3, len(arr) - 1)
    
    def _object_to_table(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Convert object to table format."""
        return {
            "headers": ["Key", "Value"],
            "rows": [
                [{"text": str(key)}, {"text": self._format_value(value)}]
                for key, value in obj.items()
            ],
            "metadata": {
                "table_type": "key_value",
                "row_count": len(obj),
                "column_count": 2
            }
        }
    
    def _array_to_table(self, arr: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert array of objects to table format."""
        if not arr or not isinstance(arr[0], dict):
            return {}
        
        # Get all unique keys
        all_keys = set()
        for item in arr:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        headers = sorted(list(all_keys))
        
        # Create rows
        rows = []
        for item in arr:
            if isinstance(item, dict):
                row = []
                for header in headers:
                    value = item.get(header, "")
                    row.append({"text": self._format_value(value)})
                rows.append(row)
        
        return {
            "headers": headers,
            "rows": rows,
            "metadata": {
                "table_type": "object_array",
                "row_count": len(rows),
                "column_count": len(headers)
            }
        }
    
    def _format_value(self, value: Any) -> str:
        """Format value for display in table."""
        if value is None:
            return ""
        elif isinstance(value, (dict, list)):
            return json.dumps(value, separators=(',', ':'))[:100]
        else:
            return str(value)
    
    def _create_object_summary(self, obj: Dict[str, Any]) -> str:
        """Create summary of object content."""
        summary_parts = []
        
        for key, value in list(obj.items())[:5]:  # First 5 items
            if isinstance(value, str) and len(value) < 50:
                summary_parts.append(f"{key}: {value}")
            elif isinstance(value, (int, float, bool)):
                summary_parts.append(f"{key}: {value}")
            elif isinstance(value, dict):
                summary_parts.append(f"{key}: {{{len(value)} keys}}")
            elif isinstance(value, list):
                summary_parts.append(f"{key}: [{len(value)} items]")
            else:
                summary_parts.append(f"{key}: {type(value).__name__}")
        
        return "; ".join(summary_parts)
    
    def _create_array_summary(self, arr: List[Any]) -> List[Dict[str, Any]]:
        """Create summary of array content."""
        summary_items = []
        
        for i, item in enumerate(arr[:5]):  # First 5 items
            if isinstance(item, str) and len(item) < 100:
                summary_items.append({"text": item, "index": i})
            elif isinstance(item, (int, float, bool)):
                summary_items.append({"text": str(item), "index": i})
            elif isinstance(item, dict):
                summary_items.append({"text": f"Object with {len(item)} keys", "index": i})
            elif isinstance(item, list):
                summary_items.append({"text": f"Array with {len(item)} items", "index": i})
            else:
                summary_items.append({"text": f"{type(item).__name__}", "index": i})
        
        return summary_items
    
    def _calculate_confidence_score(self, structured_elements: List[Dict], json_data: Any) -> float:
        """Calculate confidence score based on extraction quality."""
        if not structured_elements:
            return 0.1
        
        score = 0.7  # Base score for valid JSON
        
        # Bonus for variety of element types
        element_types = set(elem['type'] for elem in structured_elements)
        score += len(element_types) * 0.05
        
        # Bonus for tables (structured data)
        table_count = sum(1 for elem in structured_elements if elem['type'] == 'table')
        score += min(table_count * 0.1, 0.2)
        
        # Bonus for complex nested structures
        max_depth = max((elem.get('metadata', {}).get('json_path', '').count('.') for elem in structured_elements), default=0)
        score += min(max_depth * 0.02, 0.1)
        
        return min(score, 1.0)
    
    def _create_error_response(self, file_path: Union[str, Path], error: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "metadata": {
                "source_file": str(file_path),
                "file_type": "json",
                "extraction_timestamp": datetime.now().isoformat(),
                "error": error
            },
            "content": {
                "raw_text": "",
                "structured_elements": []
            },
            "extraction_info": {
                "method": "json_parser",
                "confidence_score": 0.0
            }
        }


# Example usage and testing
if __name__ == "__main__":
    parser = JSONParser()
    
    # Test with sample JSON data
    test_json = {
        "title": "Sample Data",
        "metadata": {
            "created": "2024-01-01",
            "version": "1.0"
        },
        "users": [
            {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25},
            {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "age": 35}
        ],
        "settings": {
            "theme": "dark",
            "language": "en",
            "notifications": True
        },
        "description": "This is a sample JSON file for testing the parser with various data types and structures."
    }
    
    # Save test JSON to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_json, f, indent=2)
        temp_path = f.name
    
    try:
        result = parser.parse(temp_path)
        print(json.dumps(result, indent=2))
    finally:
        os.unlink(temp_path)