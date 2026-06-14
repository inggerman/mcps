from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp_shared.errors import ValidationError

_SUPPORTED = {".pdf", ".docx", ".pptx"}


def resolve_document(root: Path, path: str, max_file_size_mb: int) -> Path:
    base = root.resolve()
    document = (base / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if not document.is_relative_to(base):
        raise ValidationError(field="path", message="El documento está fuera de DOCUMENTS_ROOT.")
    if not document.is_file():
        raise ValidationError(field="path", message="El documento no existe.")
    if document.suffix.lower() not in _SUPPORTED:
        raise ValidationError(field="path", message="Formato soportado: PDF, DOCX o PPTX.")
    if document.stat().st_size > max_file_size_mb * 1024 * 1024:
        raise ValidationError(field="path", message="El documento supera el tamaño máximo.")
    return document


def extract_document(
    root: Path, path: str, max_file_size_mb: int, max_pages: int
) -> dict[str, Any]:
    document = resolve_document(root, path, max_file_size_mb)
    suffix = document.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(document, max_pages)
    if suffix == ".docx":
        return _extract_docx(document)
    return _extract_pptx(document, max_pages)


def _extract_pdf(path: Path, max_pages: int) -> dict[str, Any]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [
        {"number": index + 1, "text": page.extract_text() or ""}
        for index, page in enumerate(reader.pages[:max_pages])
    ]
    return {
        "format": "pdf",
        "pages": pages,
        "page_count": len(reader.pages),
        "truncated": len(reader.pages) > max_pages,
        "text": "\n\n".join(str(page["text"]) for page in pages),
    }


def _extract_docx(path: Path) -> dict[str, Any]:
    from docx import Document

    document = Document(str(path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
    tables = [
        [[cell.text for cell in row.cells] for row in table.rows] for table in document.tables
    ]
    return {
        "format": "docx",
        "paragraphs": paragraphs,
        "tables": tables,
        "text": "\n".join(paragraphs),
    }


def _extract_pptx(path: Path, max_pages: int) -> dict[str, Any]:
    from pptx import Presentation

    presentation = Presentation(str(path))
    slides: list[dict[str, Any]] = []
    for index, slide in enumerate(presentation.slides[:max_pages]):
        texts = [shape.text for shape in slide.shapes if hasattr(shape, "text") and shape.text]
        slides.append({"number": index + 1, "text": "\n".join(texts)})
    return {
        "format": "pptx",
        "slides": slides,
        "slide_count": len(presentation.slides),
        "truncated": len(presentation.slides) > max_pages,
        "text": "\n\n".join(slide["text"] for slide in slides),
    }


def get_document_metadata(root: Path, path: str, max_file_size_mb: int) -> dict[str, Any]:
    document = resolve_document(root, path, max_file_size_mb)
    stat = document.stat()
    return {
        "name": document.name,
        "format": document.suffix.lower().lstrip("."),
        "size": stat.st_size,
        "modified": stat.st_mtime,
    }
