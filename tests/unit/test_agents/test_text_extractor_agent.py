import pytest
from src.agents.text_extractor.text_extractor_agent import TextExtractorAgent
from src.core.data_models import FileMetadata, FileType

@pytest.mark.asyncio
async def test_process_txt_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_content = "Header\n======\n\nThis is a test paragraph."
    test_file.write_text(test_content)

    agent = TextExtractorAgent()
    file_metadata = FileMetadata(
        filename=str(test_file),
        file_type=FileType.TXT,
        file_size=len(test_content),
        encoding="utf-8"
    )

    result = await agent.process(str(test_file), file_metadata)
    assert result is not None
    assert "structured_elements" in result
    assert len(result.structured_elements) > 0
