import pytest
from src.agents.text_extractor.parsers.txt_parser import TXTParser

def test_parse_simple_text(tmp_path):
    test_file = tmp_path / "test.txt"
    test_content = "Header\n======\n\nThis is a paragraph.\n\n- List item 1\n- List item 2"
    test_file.write_text(test_content)

    parser = TXTParser()
    result = parser.parse(str(test_file))

    assert "metadata" in result
    assert "content" in result
    assert "structured_elements" in result["content"]
    assert any(elem["type"] == "heading" for elem in result["content"]["structured_elements"])
    assert any(elem["type"] == "list" for elem in result["content"]["structured_elements"])
    assert any(elem["type"] == "paragraph" for elem in result["content"]["structured_elements"])
