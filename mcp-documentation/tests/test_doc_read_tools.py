"""Tests para Doc Read Tools."""

from __future__ import annotations

import pytest

from mcp_documentation.tools.doc_read_tools import (
    get_document_metadata,
    get_document_summary,
    get_document_toc,
    get_documents_by_category,
    get_documents_by_tag,
    get_recent_documents,
    list_documents,
    read_document,
    read_document_section,
    search_in_document,
)


class TestReadDocument:
    def test_read_markdown(self, mock_settings, sample_md_file):
        result = read_document(sample_md_file)
        assert result["format"] == "md"
        assert result["title"] == "Test Document"
        assert "frontmatter" in result
        assert result["frontmatter"]["type"] == "feature"

    def test_read_yaml(self, mock_settings, sample_yaml_file):
        result = read_document(sample_yaml_file)
        assert result["format"] == "yaml"
        assert "database" in result["content"]

    def test_read_nonexistent(self, mock_settings, tmp_root):
        with pytest.raises(FileNotFoundError):
            read_document(str(tmp_root / "nope.md"))

    def test_read_unsupported_extension(self, mock_settings, tmp_root):
        p = tmp_root / "file.xyz"
        p.write_text("content", encoding="utf-8")
        with pytest.raises(ValueError, match="no permitida"):
            read_document(str(p))


class TestReadDocumentSection:
    def test_read_section(self, mock_settings, sample_md_file):
        result = read_document_section(sample_md_file, "Section One")
        assert result is not None
        assert result["heading"] == "Section One"
        assert "Subsection" in result["content"]

    def test_read_section_not_found(self, mock_settings, sample_md_file):
        result = read_document_section(sample_md_file, "Nonexistent")
        assert result is None

    def test_read_section_case_insensitive(self, mock_settings, sample_md_file):
        result = read_document_section(sample_md_file, "section one")
        assert result is not None


class TestListDocuments:
    def test_list_all(self, mock_settings, doc_directory):
        docs = list_documents()
        assert len(docs) == 3

    def test_list_non_recursive(self, mock_settings, doc_directory):
        docs = list_documents(recursive=False)
        assert len(docs) == 0  # All in subdirs

    def test_list_nonexistent_dir(self, mock_settings, tmp_root):
        with pytest.raises(FileNotFoundError):
            list_documents(directory="nonexistent")


class TestGetDocumentMetadata:
    def test_metadata(self, mock_settings, sample_md_file):
        meta = get_document_metadata(sample_md_file)
        assert meta["title"] == "Test Document"
        assert meta["category"] == "feature"
        assert meta["format"] == "md"
        assert "timestamp" in meta
        assert meta["tags"] == ["python", "mcp", "documentation"]


class TestSearchInDocument:
    def test_search_found(self, mock_settings, sample_md_file):
        results = search_in_document(sample_md_file, "content")
        assert len(results) > 0
        assert "line_number" in results[0]

    def test_search_not_found(self, mock_settings, sample_md_file):
        results = search_in_document(sample_md_file, "nonexistent_text_xyz")
        assert len(results) == 0

    def test_search_case_insensitive(self, mock_settings, sample_md_file):
        results = search_in_document(sample_md_file, "TEST DOCUMENT")
        assert len(results) > 0


class TestGetDocumentSummary:
    def test_summary(self, mock_settings, sample_md_file):
        s = get_document_summary(sample_md_file)
        assert s["title"] == "Test Document"
        assert s["word_count"] > 0
        assert s["heading_count"] >= 3


class TestGetDocumentToc:
    def test_toc(self, mock_settings, sample_md_file):
        toc = get_document_toc(sample_md_file)
        assert "Section One" in toc
        assert "Section Two" in toc

    def test_toc_empty(self, mock_settings, tmp_root):
        p = tmp_root / "empty.md"
        p.write_text("No headings here.", encoding="utf-8")
        toc = get_document_toc(str(p))
        assert "No se encontraron" in toc


class TestGetRecentDocuments:
    def test_recent(self, mock_settings, doc_directory):
        docs = get_recent_documents(limit=2)
        assert len(docs) == 2
        # Most recent first (by timestamp in frontmatter)
        assert docs[0]["frontmatter"]["timestamp"] >= docs[1]["frontmatter"]["timestamp"]


class TestGetDocumentsByCategory:
    def test_by_category(self, mock_settings, doc_directory):
        docs = get_documents_by_category("feature")
        assert len(docs) == 1
        assert docs[0]["title"] == "Feature One"

    def test_by_category_empty(self, mock_settings, doc_directory):
        docs = get_documents_by_category("nonexistent")
        assert len(docs) == 0


class TestGetDocumentsByTag:
    def test_by_tag(self, mock_settings, doc_directory):
        docs = get_documents_by_tag("bug")
        assert len(docs) == 1
        assert docs[0]["title"] == "Fix One"

    def test_by_tag_empty(self, mock_settings, doc_directory):
        docs = get_documents_by_tag("nonexistent_tag")
        assert len(docs) == 0
