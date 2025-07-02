import pytest
from src.agents.text_extractor.parsers.json_parser import JSONParser

def test_parse_simple_json(tmp_path):
    test_file = tmp_path / "test.json"
    test_content = '''
    {
        "title": "Test JSON",
        "items": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"}
        ]
    }
    '''
    test_file.write_text(test_content)

    parser = JSONParser()
    result = parser.parse(str(test_file))

    assert "metadata" in result
    assert "content" in result
    assert "structured_elements" in result["content"]
    assert any(elem["type"] == "table" for elem in result["content"]["structured_elements"]) or \
           any(elem["type"] == "object" for elem in result["content"]["structured_elements"])
