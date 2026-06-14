from pathlib import Path

import pytest
from docx import Document
from mcp_documents.tools.document_tools import extract_document, resolve_document
from mcp_shared.errors import ValidationError


def test_extract_docx(tmp_path: Path) -> None:
    document = Document()
    document.add_paragraph("Hello documents")
    document.save(tmp_path / "sample.docx")
    result = extract_document(tmp_path, "sample.docx", 10, 20)
    assert result["format"] == "docx"
    assert result["text"] == "Hello documents"


def test_rejects_outside_root(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        resolve_document(tmp_path, "../outside.pdf", 10)
