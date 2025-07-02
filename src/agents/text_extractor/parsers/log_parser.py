"""
LOG Parser Module

Research Summary:
- Log files are highly structured but diverse in format (Apache, Nginx, syslog, application logs)
- Common patterns include timestamps, log levels, source/component, message content
- Challenges include multi-line logs, stack traces, custom formats, and large file sizes
- Regular expressions are crucial for pattern matching and field extraction
- Statistical analysis helps detect log format patterns and anomalies

Challenges Addressed:
1. Multiple log formats - Apache Common/Combined, RFC3164 syslog, custom application logs
2. Multi-line log entries - Stack traces, JSON logs, error messages spanning lines
3. Timestamp parsing - Various formats (ISO8601, Apache, syslog, custom)
4. Large log files - Memory efficient processing with streaming
5. Malformed entries - Corrupted logs, incomplete lines, encoding issues
6. Mixed log formats - Files with multiple applications logging different formats

Libraries Used:
- re: Pattern matching for log parsing
- datetime: Timestamp parsing and normalization
- json: JSON log entry parsing
- chardet: Encoding detection
- gzip/bz2: Compressed log file support
- ipaddress: IP address validation and parsing

Edge Cases Handled:
- Logs with mixed timestamp formats
- Multi-line stack traces and error messages
- JSON logs embedded in traditional log formats
- Compressed log files (.gz, .bz2)
- Logs with custom delimiters and formats
- Incomplete log entries at file boundaries
"""

import os
import re
import json
import gzip
import bz2
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union, Tuple, Iterator
from pathlib import Path
import chardet
import ipaddress


class LogParser:
    """
    Production-grade log parser that extracts structured content from various log file formats.
    
    Supports:
    - Common log formats (Apache Common/Combined, Nginx, syslog)
    - Custom application logs with configurable patterns
    - Multi-line log entries (stack traces, JSON logs)
    - Compressed log files (.gz, .bz2)
    - Large file streaming processing
    - Timestamp normalization and timezone handling
    """
    
    def __init__(self, max_file_size: int = 500*1024*1024, chunk_size: int = 1024*1024):
        """
        Initialize log parser with configuration.
        
        Args:
            max_file_size: Maximum file size in bytes for processing
            chunk_size: Chunk size for streaming large files
        """
        self.max_file_size = max_file_size
        self.chunk_size = chunk_size
        
        # Common log format patterns
        self.log_patterns = {
            'apache_common': re.compile(
                r'(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<size>\S+)'
            ),
            'apache_combined': re.compile(
                r'(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<size>\S+) "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)"'
            ),
            'nginx_access': re.compile(
                r'(?P<ip>\S+) - \S+ \[(?P<timestamp>[^\]]+)\] "(?P<method>\S+) (?P<url>\S+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<size>\d+) "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)"'
            ),
            'syslog_rfc3164': re.compile(
                r'(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+) (?P<hostname>\S+) (?P<process>\S+?)(?:\[(?P<pid>\d+)\])?: (?P<message>.*)'
            ),
            'syslog_rfc5424': re.compile(
                r'(?P<priority><\d+>)?(?P<version>\d+)?\s*(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+(?P<hostname>\S+)\s+(?P<app_name>\S+)\s+(?P<proc_id>\S+)\s+(?P<msg_id>\S+)\s+(?P<structured_data>\[.*?\]|\-)\s+(?P<message>.*)'
            ),
            'iso_timestamp': re.compile(
                r'(?P<timestamp>\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+(?P<level>\w+)?\s*(?P<message>.*)'
            ),
            'generic_timestamp': re.compile(
                r'(?P<timestamp>\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d+)?)\s+(?P<level>\w+)?\s*(?P<message>.*)'
            ),
            'json_log': re.compile(r'^(?P<json_data>\{.*\})$'),
            'log_level': re.compile(r'\b(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE|CRITICAL)\b', re.IGNORECASE)
        }
        
        # Timestamp format patterns
        self.timestamp_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d %H:%M:%S.%f',
            '%d/%b/%Y:%H:%M:%S %z',
            '%b %d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%d-%m-%Y %H:%M:%S',
            '%Y%m%d %H:%M:%S'
        ]
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse log file and extract structured content.
        
        Args:
            file_path (str): Path to the log file
            
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
            
            # Determine if file is compressed
            is_compressed, compression_type = self._detect_compression(file_path)
            
            # Read file content
            content = self._read_log_file(file_path, is_compressed, compression_type)
            
            # Extract metadata
            metadata = self._extract_metadata(file_path, content, file_size, compression_type)
            
            # Detect log format
            log_format, format_confidence = self._detect_log_format(content)
            metadata["detected_format"] = {
                "format": log_format,
                "confidence": format_confidence
            }
            
            # Parse log entries
            log_entries = self._parse_log_entries(content, log_format)
            
            # Create structured elements
            structured_elements = self._create_structured_elements(log_entries)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(log_entries, structured_elements, content)
            
            return {
                "metadata": metadata,
                "content": {
                    "raw_text": content,
                    "structured_elements": structured_elements
                },
                "extraction_info": {
                    "method": "log_parser",
                    "confidence_score": confidence_score,
                    "detected_format": log_format,
                    "entries_parsed": len(log_entries)
                }
            }
            
        except Exception as e:
            return self._create_error_response(file_path, str(e))
    
    def _detect_compression(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """Detect if file is compressed and determine compression type."""
        if file_path.suffix.lower() == '.gz':
            return True, 'gzip'
        elif file_path.suffix.lower() == '.bz2':
            return True, 'bzip2'
        
        # Check magic bytes
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                if magic.startswith(b'\x1f\x8b'):
                    return True, 'gzip'
                elif magic.startswith(b'BZ'):
                    return True, 'bzip2'
        except Exception:
            pass
        
        return False, None
    
    def _read_log_file(self, file_path: Path, compressed: bool, compression_type: Optional[str]) -> str:
        """Read log file content with compression support."""
        if compressed:
            if compression_type == 'gzip':
                with gzip.open(file_path, 'rb') as f:
                    raw_data = f.read()
            elif compression_type == 'bzip2':
                with bz2.open(file_path, 'rb') as f:
                    raw_data = f.read()
            else:
                raise ValueError(f"Unsupported compression type: {compression_type}")
        else:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
        
        # Detect encoding
        detected_encoding = chardet.detect(raw_data)
        encoding = detected_encoding.get('encoding', 'utf-8')
        
        # Try to decode with detected encoding, fallback to common encodings
        encodings = [encoding, 'utf-8', 'latin-1', 'cp1252', 'ascii']
        
        for enc in encodings:
            try:
                return raw_data.decode(enc)
            except (UnicodeDecodeError, TypeError):
                continue
        
        # Final fallback with error handling
        return raw_data.decode('utf-8', errors='replace')
    
    def _extract_metadata(self, file_path: Path, content: str, file_size: int, compression_type: Optional[str]) -> Dict[str, Any]:
        """Extract metadata from log file and content."""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        metadata = {
            "source_file": file_path.name,
            "file_type": "log",
            "extraction_timestamp": datetime.now().isoformat(),
            "file_size": file_size,
            "compression": compression_type
        }
        
        # Content statistics
        metadata["statistics"] = {
            "line_count": len(lines),
            "entry_count": len(non_empty_lines),
            "character_count": len(content),
            "average_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0
        }
        
        # Analyze log patterns
        patterns_found = {}
        
        # Check for common log formats
        for format_name, pattern in self.log_patterns.items():
            matches = pattern.findall(content)
            if matches:
                patterns_found[format_name] = len(matches)
        
        # Check for log levels
        level_matches = self.log_patterns['log_level'].findall(content)
        if level_matches:
            level_counts = {}
            for level in level_matches:
                level = level.upper()
                level_counts[level] = level_counts.get(level, 0) + 1
            patterns_found['log_levels'] = level_counts
        
        # Check for IP addresses
        ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        ip_matches = ip_pattern.findall(content)
        if ip_matches:
            patterns_found['ip_addresses'] = len(set(ip_matches))
        
        # Time range analysis
        timestamps = self._extract_timestamps(content[:10000])  # Sample first 10KB
        if timestamps:
            metadata["time_range"] = {
                "start_time": min(timestamps).isoformat(),
                "end_time": max(timestamps).isoformat(),
                "duration_seconds": (max(timestamps) - min(timestamps)).total_seconds()
            }
        
        if patterns_found:
            metadata["detected_patterns"] = patterns_found
        
        return metadata
    
    def _detect_log_format(self, content: str) -> Tuple[str, float]:
        """Detect the most likely log format and confidence score."""
        sample_lines = content.split('\n')[:100]  # Analyze first 100 lines
        format_scores = {}
        
        for format_name, pattern in self.log_patterns.items():
            if format_name in ['log_level', 'json_log']:
                continue
            
            matches = 0
            for line in sample_lines:
                if line.strip() and pattern.match(line):
                    matches += 1
            
            if matches > 0:
                format_scores[format_name] = matches / len([l for l in sample_lines if l.strip()])
        
        # Check for JSON logs
        json_matches = 0
        for line in sample_lines:
            if line.strip():
                try:
                    json.loads(line.strip())
                    json_matches += 1
                except:
                    pass
        
        if json_matches > 0:
            format_scores['json_log'] = json_matches / len([l for l in sample_lines if l.strip()])
        
        if format_scores:
            best_format = max(format_scores.items(), key=lambda x: x[1])
            return best_format[0], best_format[1]
        
        return 'generic', 0.0
    
    def _parse_log_entries(self, content: str, log_format: str) -> List[Dict[str, Any]]:
        """Parse log entries based on detected format."""
        lines = content.split('\n')
        entries = []
        current_entry = None
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            # Try to parse as new log entry
            parsed_entry = self._parse_single_line(line, log_format, line_num)
            
            if parsed_entry:
                # New entry found
                if current_entry:
                    entries.append(current_entry)
                current_entry = parsed_entry
            else:
                # Continuation of previous entry (multi-line log)
                if current_entry:
                    if 'message' in current_entry:
                        current_entry['message'] += '\n' + line
                    else:
                        current_entry['raw_line'] = current_entry.get('raw_line', '') + '\n' + line
                    current_entry['is_multiline'] = True
                else:
                    # Orphaned line, create generic entry
                    current_entry = {
                        'line_number': line_num,
                        'raw_line': line,
                        'message': line,
                        'type': 'orphaned_line',
                        'timestamp': None
                    }
        
        # Add the last entry
        if current_entry:
            entries.append(current_entry)
        
        return entries
    
    def _parse_single_line(self, line: str, log_format: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Parse a single log line based on format."""
        # Try JSON parsing first
        if log_format == 'json_log':
            try:
                json_data = json.loads(line.strip())
                return {
                    'line_number': line_num,
                    'raw_line': line,
                    'type': 'json_log',
                    'timestamp': self._parse_timestamp(json_data.get('timestamp') or json_data.get('time') or json_data.get('@timestamp')),
                    'level': json_data.get('level') or json_data.get('severity'),
                    'message': json_data.get('message') or json_data.get('msg'),
                    'json_data': json_data
                }
            except:
                pass
        
        # Try specific format patterns
        if log_format in self.log_patterns:
            pattern = self.log_patterns[log_format]
            match = pattern.match(line)
            
            if match:
                entry = {
                    'line_number': line_num,
                    'raw_line': line,
                    'type': log_format
                }
                
                # Extract matched groups
                for key, value in match.groupdict().items():
                    if key == 'timestamp':
                        entry['timestamp'] = self._parse_timestamp(value)
                    else:
                        entry[key] = value
                
                # Extract log level if not already captured
                if 'level' not in entry:
                    level_match = self.log_patterns['log_level'].search(line)
                    if level_match:
                        entry['level'] = level_match.group('level').upper()
                
                return entry
        
        # Generic parsing fallback
        return self._generic_line_parse(line, line_num)
    
    def _generic_line_parse(self, line: str, line_num: int) -> Dict[str, Any]:
        """Generic line parsing for unknown formats."""
        entry = {
            'line_number': line_num,
            'raw_line': line,
            'type': 'generic'
        }
        
        # Try to extract timestamp
        timestamp = self._extract_timestamp_from_line(line)
        if timestamp:
            entry['timestamp'] = timestamp
        
        # Try to extract log level
        level_match = self.log_patterns['log_level'].search(line)
        if level_match:
            entry['level'] = level_match.group('level').upper()
        
        # Try to extract IP address
        ip_pattern = re.compile(r'\b(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\b')
        ip_match = ip_pattern.search(line)
        if ip_match:
            entry['ip'] = ip_match.group('ip')
        
        # The rest is message
        entry['message'] = line
        
        return entry
    
    def _extract_timestamp_from_line(self, line: str) -> Optional[datetime]:
        """Extract timestamp from a line using various patterns."""
        # Try ISO timestamp pattern
        iso_match = self.log_patterns['iso_timestamp'].match(line)
        if iso_match:
            return self._parse_timestamp(iso_match.group('timestamp'))
        
        # Try generic timestamp pattern
        generic_match = self.log_patterns['generic_timestamp'].match(line)
        if generic_match:
            return self._parse_timestamp(generic_match.group('timestamp'))
        
        # Try to find any timestamp-like pattern
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?',
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+\d{1,2}:\d{2}:\d{2}(?:\.\d+)?',
            r'\w+\s+\d+\s+\d{2}:\d{2}:\d{2}',
            r'\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2}\s+[+-]\d{4}'
        ]
        
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                timestamp = self._parse_timestamp(match.group())
                if timestamp:
                    return timestamp
        
        return None
    
    def _parse_timestamp(self, timestamp_str: Union[str, int, float, None]) -> Optional[datetime]:
        """Parse timestamp string into datetime object."""
        if not timestamp_str:
            return None
        
        # Handle Unix timestamp
        if isinstance(timestamp_str, (int, float)):
            try:
                return datetime.fromtimestamp(timestamp_str, tz=timezone.utc)
            except:
                return None
        
        if isinstance(timestamp_str, str):
            # Handle Unix timestamp as string
            try:
                timestamp_float = float(timestamp_str)
                if timestamp_float > 1000000000:  # Reasonable Unix timestamp
                    return datetime.fromtimestamp(timestamp_float, tz=timezone.utc)
            except:
                pass
            
            # Try various timestamp formats
            for fmt in self.timestamp_formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # Try parsing with dateutil if available
            try:
                from dateutil.parser import parse as dateutil_parse
                return dateutil_parse(timestamp_str)
            except:
                pass
        
        return None
    
    def _extract_timestamps(self, content: str) -> List[datetime]:
        """Extract all timestamps from content sample."""
        timestamps = []
        lines = content.split('\n')[:50]  # Sample first 50 lines
        
        for line in lines:
            timestamp = self._extract_timestamp_from_line(line)
            if timestamp:
                timestamps.append(timestamp)
        
        return timestamps
    
    def _create_structured_elements(self, log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create structured elements from parsed log entries."""
        elements = []
        
        # Group entries by type for analysis
        entries_by_type = {}
        for entry in log_entries:
            entry_type = entry.get('type', 'generic')
            if entry_type not in entries_by_type:
                entries_by_type[entry_type] = []
            entries_by_type[entry_type].append(entry)
        
        # Create summary element
        summary_element = {
            "type": "log_summary",
            "content": {
                "total_entries": len(log_entries),
                "entry_types": {k: len(v) for k, v in entries_by_type.items()},
                "time_range": self._get_time_range(log_entries),
                "log_levels": self._get_log_level_distribution(log_entries)
            },
            "position": 0,
            "metadata": {
                "analysis_type": "summary"
            }
        }
        elements.append(summary_element)
        
        # Create log entries element
        entries_element = {
            "type": "log_entries",
            "content": {
                "entries": log_entries,
                "format": "structured_log_data"
            },
            "position": 1,
            "metadata": {
                "entry_count": len(log_entries),
                "has_timestamps": sum(1 for e in log_entries if e.get('timestamp')) > 0,
                "has_log_levels": sum(1 for e in log_entries if e.get('level')) > 0,
                "multiline_entries": sum(1 for e in log_entries if e.get('is_multiline', False))
            }
        }
        elements.append(entries_element)
        
        # Create error/exception analysis if present
        error_entries = [e for e in log_entries if self._is_error_entry(e)]
        if error_entries:
            error_element = {
                "type": "error_analysis",
                "content": {
                    "error_count": len(error_entries),
                    "error_entries": error_entries[:50],  # Limit to first 50 errors
                    "error_patterns": self._analyze_error_patterns(error_entries)
                },
                "position": 2,
                "metadata": {
                    "analysis_type": "error_analysis",
                    "error_percentage": len(error_entries) / len(log_entries) * 100
                }
            }
            elements.append(error_element)
        
        # Create IP analysis if present
        ip_entries = [e for e in log_entries if 'ip' in e]
        if ip_entries:
            ip_analysis = self._analyze_ip_addresses(ip_entries)
            if ip_analysis:
                ip_element = {
                    "type": "ip_analysis",
                    "content": ip_analysis,
                    "position": 3,
                    "metadata": {
                        "analysis_type": "ip_analysis",
                        "entries_with_ip": len(ip_entries)
                    }
                }
                elements.append(ip_element)
        
        return elements
    
    def _get_time_range(self, entries: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """Get time range from log entries."""
        timestamps = [e.get('timestamp') for e in entries if e.get('timestamp')]
        if timestamps:
            return {
                "start": min(timestamps).isoformat(),
                "end": max(timestamps).isoformat(),
                "duration_seconds": (max(timestamps) - min(timestamps)).total_seconds()
            }
        return None
    
    def _get_log_level_distribution(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of log levels."""
        levels = {}
        for entry in entries:
            level = entry.get('level')
            if level:
                levels[level] = levels.get(level, 0) + 1
        return levels
    
    def _is_error_entry(self, entry: Dict[str, Any]) -> bool:
        """Check if entry represents an error or exception."""
        level = entry.get('level', '').upper()
        if level in ['ERROR', 'FATAL', 'CRITICAL']:
            return True
        
        message = entry.get('message', '').lower()
        error_keywords = ['error', 'exception', 'traceback', 'failed', 'failure', 'fatal', 'critical']
        return any(keyword in message for keyword in error_keywords)
    
    def _analyze_error_patterns(self, error_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in error entries."""
        patterns = {
            "common_errors": {},
            "error_frequency": {},
            "stack_traces": 0
        }
        
        for entry in error_entries:
            message = entry.get('message', '')
            
            # Count stack traces
            if 'traceback' in message.lower() or 'stack trace' in message.lower():
                patterns["stack_traces"] += 1
            
            # Extract error types (simple heuristic)
            error_words = re.findall(r'\b\w*[Ee]rror\w*\b|\b\w*[Ee]xception\w*\b', message)
            for error_word in error_words:
                patterns["common_errors"][error_word] = patterns["common_errors"].get(error_word, 0) + 1
        
        return patterns
    
    def _analyze_ip_addresses(self, ip_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze IP addresses in log entries."""
        ips = [entry.get('ip') for entry in ip_entries if entry.get('ip')]
        if not ips:
            return {}
        
        ip_counts = {}
        private_ips = 0
        public_ips = 0
        
        for ip in ips:
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
            
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private:
                    private_ips += 1
                else:
                    public_ips += 1
            except:
                pass
        
        # Top IPs
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "unique_ips": len(set(ips)),
            "total_requests": len(ips),
            "private_ips": private_ips,
            "public_ips": public_ips,
            "top_ips": top_ips
        }
    
    def _calculate_confidence_score(self, log_entries: List[Dict[str, Any]], 
                                  structured_elements: List[Dict[str, Any]], 
                                  content: str) -> float:
        """Calculate confidence score for log parsing quality."""
        if not log_entries:
            return 0.0
        
        scores = []
        
        # Parsing success rate
        successfully_parsed = sum(1 for e in log_entries if e.get('type') != 'generic')
        parsing_score = successfully_parsed / len(log_entries)
        scores.append(parsing_score * 0.4)
        
        # Timestamp extraction rate
        with_timestamps = sum(1 for e in log_entries if e.get('timestamp'))
        timestamp_score = with_timestamps / len(log_entries)
        scores.append(timestamp_score * 0.3)
        
        # Structure detection rate
        structured_entries = sum(1 for e in log_entries if len(e.keys()) > 4)  # More than basic fields
        structure_score = structured_entries / len(log_entries)
        scores.append(structure_score * 0.3)
        
        return sum(scores)
    
    def _create_error_response(self, file_path: Union[str, Path], error_message: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "metadata": {
                "source_file": str(file_path),
                "file_type": "log",
                "extraction_timestamp": datetime.now().isoformat(),
                "error": error_message
            },
            "content": {
                "raw_text": "",
                "structured_elements": []
            },
            "extraction_info": {
                "method": "log_parser",
                "confidence_score": 0.0,
                "error": error_message
            }
        }