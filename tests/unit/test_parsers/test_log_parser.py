import pytest
from src.agents.text_extractor.parsers.log_parser import LogParser

def test_parse_simple_log(tmp_path):
    test_file = tmp_path / "test.log"
    test_content = '127.0.0.1 - - [10/Oct/2020:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 2326'
    test_file.write_text(test_content)

    parser = LogParser()
    result = parser.parse(str(test_file))

    assert "metadata" in result
    assert "content" in result
    assert "structured_elements" in result["content"]
    assert len(result["content"]["structured_elements"]) > 0
