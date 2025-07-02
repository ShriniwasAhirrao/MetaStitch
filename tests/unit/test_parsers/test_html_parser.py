import pytest
from src.agents.text_extractor.parsers.html_parser import HTMLParser

def test_parse_simple_html(tmp_path):
    test_file = tmp_path / "test.html"
    test_content = """
    <html>
        <head><title>Test</title></head>
        <body>
            <h1>Header</h1>
            <p>Paragraph text.</p>
            <ul><li>Item 1</li><li>Item 2</li></ul>
        </body>
    </html>
    """
    test_file.write_text(test_content)

    parser = HTMLParser()
    result = parser.parse(str(test_file))

    assert "metadata" in result
    assert "content" in result
    assert "structured_elements" in result["content"]
    assert any(elem["type"] == "heading" for elem in result["content"]["structured_elements"])
    assert any(elem["type"] == "paragraph" for elem in result["content"]["structured_elements"])
    assert any(elem["type"] == "list" for elem in result["content"]["structured_elements"])
