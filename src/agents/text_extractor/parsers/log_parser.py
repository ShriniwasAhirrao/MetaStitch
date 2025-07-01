import re
import json
import os
import gzip
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

class LogToJsonConverter:
    """
    Converts unstructured/semi-structured log files (.log, .txt, .out) to JSON format
    """
    
    def __init__(self, config: Optional[Dict] = None):
        # Set default config first, then update with user config
        self.config = self._default_config()
        if config:
            self.config.update(config)
        
        self.setup_logging()
        
        # Compile regex patterns for better performance
        self.patterns = self._compile_patterns()
        
        # Context buffer for multi-line entries
        self.context_buffer = []
        self.current_entry = {}
        
        # Statistics
        self.stats = {
            'total_lines': 0,
            'processed_lines': 0,
            'skipped_lines': 0,
            'errors': 0
        }
    
    def _default_config(self) -> Dict:
        """Default configuration for the converter"""
        return {
            'buffer_size': 1000,
            'compress_output': False,
            'validate_json': True,
            'preserve_raw_line': True,
            'timestamp_formats': [
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z?',  # ISO 8601
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?',     # Standard format
                r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',                 # US format
                r'\w{3} \d{2} \d{2}:\d{2}:\d{2}',                       # Syslog format
                r'\d{10}(?:\.\d{3})?'                                    # Unix timestamp
            ],
            'log_levels': ['TRACE', 'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL'],
            'multiline_indicators': ['Exception', 'Traceback', 'Stack trace', 'Caused by', '\tat '],
            'max_context_lines': 50
        }
    
    def setup_logging(self):
        """Setup logging for the converter"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _compile_patterns(self) -> Dict:
        """Compile regex patterns for performance"""
        patterns = {}
        
        # Timestamp patterns
        patterns['timestamps'] = [
            re.compile(pattern) for pattern in self.config['timestamp_formats']
        ]
        
        # Log level pattern
        log_levels = '|'.join(self.config['log_levels'])
        patterns['log_level'] = re.compile(rf'\b({log_levels})\b', re.IGNORECASE)
        
        # IP address pattern
        patterns['ip_address'] = re.compile(
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        )
        
        # Key-value patterns
        patterns['key_value'] = re.compile(r'(\w+)[:=]\s*([^\s,;]+)')
        
        # JSON fragment pattern
        patterns['json_fragment'] = re.compile(r'\{[^}]*\}|\[[^\]]*\]')
        
        # Stack trace patterns
        patterns['stack_trace'] = re.compile(
            r'(Exception|Error|Traceback|Stack trace|Caused by|\tat )',
            re.IGNORECASE
        )
        
        # HTTP request pattern
        patterns['http_request'] = re.compile(
            r'(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\s+([^\s]+)\s+HTTP/[\d.]+',
            re.IGNORECASE
        )
        
        # Process ID pattern
        patterns['process_id'] = re.compile(r'\[(\d+)\]')
        
        return patterns
    
    def detect_file_type(self, file_path: str) -> str:
        """Detect file type based on extension"""
        extension = Path(file_path).suffix.lower()
        
        type_mapping = {
            '.log': 'application_log',
            '.txt': 'text_log',
            '.out': 'output_log'
        }
        
        return type_mapping.get(extension, 'generic_log')
    
    def extract_timestamp(self, line: str) -> Optional[Dict]:
        """Extract timestamp from line"""
        for pattern in self.patterns['timestamps']:
            match = pattern.search(line)
            if match:
                timestamp_str = match.group(0)
                try:
                    # Try to parse different timestamp formats
                    parsed_time = self._parse_timestamp(timestamp_str)
                    return {
                        'timestamp': parsed_time.isoformat(),
                        'timestamp_raw': timestamp_str,
                        'timestamp_position': match.span()
                    }
                except Exception as e:
                    self.logger.debug(f"Failed to parse timestamp {timestamp_str}: {e}")
        
        return None
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object"""
        # Try different parsing strategies
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%b %d %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        # Try Unix timestamp
        try:
            return datetime.fromtimestamp(float(timestamp_str), tz=timezone.utc)
        except (ValueError, OSError):
            pass
        
        # Fallback to current time
        return datetime.now(timezone.utc)
    
    def extract_log_level(self, line: str) -> Optional[str]:
        """Extract log level from line"""
        match = self.patterns['log_level'].search(line)
        if match:
            level = match.group(1).upper()
            # Normalize log levels
            if level in ['WARN', 'WARNING']:
                return 'WARN'
            elif level in ['FATAL', 'CRITICAL']:
                return 'ERROR'
            return level
        return None
    
    def extract_ip_addresses(self, line: str) -> List[str]:
        """Extract IP addresses from line"""
        return self.patterns['ip_address'].findall(line)
    
    def extract_key_value_pairs(self, line: str) -> Dict[str, str]:
        """Extract key-value pairs from line"""
        pairs = {}
        matches = self.patterns['key_value'].findall(line)
        for key, value in matches:
            pairs[key.lower()] = value.strip('"\'')
        return pairs
    
    def extract_json_fragments(self, line: str) -> List[Dict]:
        """Extract JSON fragments from line"""
        fragments = []
        matches = self.patterns['json_fragment'].findall(line)
        for match in matches:
            try:
                parsed = json.loads(match)
                fragments.append(parsed)
            except json.JSONDecodeError:
                pass
        return fragments
    
    def extract_http_request(self, line: str) -> Optional[Dict]:
        """Extract HTTP request information"""
        match = self.patterns['http_request'].search(line)
        if match:
            return {
                'method': match.group(1).upper(),
                'path': match.group(2),
                'protocol': 'HTTP'
            }
        return None
    
    def extract_process_id(self, line: str) -> Optional[int]:
        """Extract process ID from line"""
        match = self.patterns['process_id'].search(line)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None
    
    def is_multiline_start(self, line: str) -> bool:
        """Check if line starts a multi-line entry"""
        return any(indicator in line for indicator in self.config['multiline_indicators'])
    
    def process_line(self, line: str, line_number: int) -> Dict[str, Any]:
        """Process a single line and extract structured data"""
        self.stats['total_lines'] += 1
        
        # Skip empty lines
        if not line.strip():
            self.stats['skipped_lines'] += 1
            return None
        
        entry = {
            'line_number': line_number,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': 'INFO',
            'message': line.strip(),
            'extracted_fields': {}
        }
        
        if self.config['preserve_raw_line']:
            entry['raw_line'] = line.rstrip('\n\r')
        
        try:
            # Extract timestamp
            timestamp_info = self.extract_timestamp(line)
            if timestamp_info:
                entry['timestamp'] = timestamp_info['timestamp']
                entry['extracted_fields']['timestamp_raw'] = timestamp_info['timestamp_raw']
            
            # Extract log level
            log_level = self.extract_log_level(line)
            if log_level:
                entry['level'] = log_level
            
            # Extract IP addresses
            ip_addresses = self.extract_ip_addresses(line)
            if ip_addresses:
                entry['extracted_fields']['ip_addresses'] = ip_addresses
            
            # Extract key-value pairs
            kv_pairs = self.extract_key_value_pairs(line)
            if kv_pairs:
                entry['extracted_fields']['key_value_pairs'] = kv_pairs
            
            # Extract JSON fragments
            json_fragments = self.extract_json_fragments(line)
            if json_fragments:
                entry['extracted_fields']['json_fragments'] = json_fragments
            
            # Extract HTTP request info
            http_info = self.extract_http_request(line)
            if http_info:
                entry['extracted_fields']['http_request'] = http_info
            
            # Extract process ID
            process_id = self.extract_process_id(line)
            if process_id:
                entry['extracted_fields']['process_id'] = process_id
            
            # Check for multi-line context
            if self.is_multiline_start(line):
                entry['multiline_start'] = True
            
            self.stats['processed_lines'] += 1
            return entry
            
        except Exception as e:
            self.logger.error(f"Error processing line {line_number}: {e}")
            self.stats['errors'] += 1
            return entry
    
    def handle_multiline_context(self, entries: List[Dict]) -> List[Dict]:
        """Handle multi-line log entries like stack traces"""
        if not entries:
            return entries
        
        processed_entries = []
        current_multiline = None
        
        for entry in entries:
            if entry.get('multiline_start'):
                if current_multiline:
                    processed_entries.append(current_multiline)
                current_multiline = entry.copy()
                current_multiline['multiline_content'] = [entry['message']]
            elif current_multiline and len(current_multiline['multiline_content']) < self.config['max_context_lines']:
                # Continue multi-line entry
                current_multiline['multiline_content'].append(entry['message'])
                current_multiline['message'] = '\n'.join(current_multiline['multiline_content'])
            else:
                if current_multiline:
                    processed_entries.append(current_multiline)
                    current_multiline = None
                processed_entries.append(entry)
        
        if current_multiline:
            processed_entries.append(current_multiline)
        
        return processed_entries
    
    def detect_log_format(self, entries: List[Dict]) -> str:
        """Detect log format (simple heuristic)"""
        # Example: check for Apache, Nginx, or custom
        for entry in entries:
            msg = entry.get("message", "")
            if "HTTP/" in msg and ("GET" in msg or "POST" in msg):
                return "apache"
            if "nginx" in msg.lower():
                return "nginx"
        if any('process_id' in e.get('structured_fields', {}) for e in entries):
            return "custom"
        return "unknown"

    def extract_patterns(self, entries: List[Dict]) -> list:
        """Extract patterns: IP addresses, error codes, URLs"""
        ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        error_code_pattern = re.compile(r'\b(?:ERR|ERROR|FAIL|CODE)[\w-]*\b', re.IGNORECASE)
        url_pattern = re.compile(r'https?://[^\s]+')
        ips, error_codes, urls = set(), set(), set()
        for entry in entries:
            msg = entry.get("message", "")
            ips.update(ip_pattern.findall(msg))
            error_codes.update(error_code_pattern.findall(msg))
            urls.update(url_pattern.findall(msg))
        patterns = []
        if ips:
            patterns.append("IP addresses")
        if error_codes:
            patterns.append("error codes")
        if urls:
            patterns.append("URLs")
        return patterns

    def convert_file(self, input_file: str, output_file: str) -> bool:
        """Convert log file to the new JSON format"""
        try:
            self.logger.info(f"Starting conversion: {input_file} -> {output_file}")
            self.stats = {key: 0 for key in self.stats}
            entries = []
            line_number = 0
    
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    line_number += 1
                    entry = self.process_line(line, line_number)
                    if entry:
                        log_entry = {
                        "timestamp": entry.get("timestamp"),
                        "level": entry.get("level"),
                        "message": entry.get("message"),
                        "structured_fields": entry.get("extracted_fields", {})
                    }
                        entries.append(log_entry)

            log_format = self.detect_log_format(entries)
            patterns = self.extract_patterns(entries)

            output_data = {
                "file_specific_data": {
                    "log_format": log_format,
                    "entries": entries,
                    "patterns": patterns
                }
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            if self.config['compress_output']:
                self._compress_output(output_file)

            self.logger.info(f"Conversion completed successfully. Processed {self.stats['processed_lines']} lines")
            return True

        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
            return False
    def _write_batch(self, entries: List[Dict], output_file: str, is_first_batch: bool):
        """Write batch of entries to output file"""
        mode = 'w' if is_first_batch else 'a'
        
        with open(output_file, mode, encoding='utf-8') as file:
            if is_first_batch:
                file.write('[\n')
            
            for i, entry in enumerate(entries):
                if not (is_first_batch and i == 0):
                    file.write(',\n')
                
                json.dump(entry, file, indent=2, ensure_ascii=False)
    
    def _append_metadata(self, output_file: str, metadata: Dict):
        """Append metadata to the JSON file"""
        with open(output_file, 'a', encoding='utf-8') as file:
            file.write(',\n')
            json.dump(metadata, file, indent=2, ensure_ascii=False)
            file.write('\n]')
    
    def _compress_output(self, output_file: str):
        """Compress the output JSON file"""
        compressed_file = output_file + '.gz'
        
        with open(output_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                f_out.writelines(f_in)
        
        os.remove(output_file)
        self.logger.info(f"Output compressed to {compressed_file}")

def main():
    """Example usage of the LogToJsonConverter"""
    
    # Configuration
    config = {
        'buffer_size': 500,
        'compress_output': False,
        'validate_json': True,
        'preserve_raw_line': True
    }
    
    # Create converter instance
    converter = LogToJsonConverter(config)
    
    # Example conversion
    input_files = [
        # 'application.log',
        # 'system.txt',
        # 'process.out',
        'custom_test.log'
    ]
    
    for input_file in input_files:
        if os.path.exists(input_file):
            output_file = f"{Path(input_file).stem}_converted.json"
            success = converter.convert_file(input_file, output_file)
            
            if success:
                print(f"✅ Successfully converted {input_file} to {output_file}")
            else:
                print(f"❌ Failed to convert {input_file}")
        else:
            print(f"⚠️  File not found: {input_file}")

if __name__ == "__main__":
    main()