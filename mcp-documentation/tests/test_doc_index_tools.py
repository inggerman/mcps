"""Tests para Doc Index Tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_documentation.index import (
    get_index_stats,
    index_all,
    index_document,
    rebuild_index,
    search_documents,
    suggest_similar_documents,
)
from mcp_documentation.tools.doc_index_tools import (
    get_index_stats_tool,
    index_documents_tool,
    rebuild_index_tool,
    search_documents_tool,
    suggest_similar_documents_tool,
)


class TestIndexDocument:
    def test_index_single(self, mock_settings, sample_md_file, tmp_root):
        result = index_document(Path(sample_md_file), tmp_root, tmp_root / ".index")
        assert result["indexed"] is True
        assert result["title"] == "Test Document"

    def test_index_yaml(self, mock_settings, sample_yaml_file, tmp_root):
        result = index_document(Path(sample_yaml_file), tmp_root, tmp_root / ".index")
        assert result["indexed"] is True


class TestIndexAll:
    def test_index_directory(self, mock_settings, doc_directory, tmp_root):
        result = index_all(tmp_root, tmp_root / ".index", [".md", ".yaml", ".yml", ".xml", ".txt", ".json"])
        assert result["total_indexed"] == 3
        assert len(result["errors"]) == 0


class TestSearchDocuments:
    def test_search_found(self, mock_settings, doc_directory, tmp_root):
        idx_path = tmp_root / ".index"
        index_all(tmp_root, idx_path, [".md"])
        results = search_documents("Feature", idx_path)
        assert len(results) > 0
        assert "score" in results[0]
        assert "snippet" in results[0]

    def test_search_not_found(self, mock_settings, doc_directory, tmp_root):
        idx_path = tmp_root / ".index"
        index_all(tmp_root, idx_path, [".md"])
        results = search_documents("nonexistent_xyz_query", idx_path)
        assert len(results) == 0

    def test_search_with_category_filter(self, mock_settings, doc_directory, tmp_root):
        idx_path = tmp_root / ".index"
        index_all(tmp_root, idx_path, [".md"])
        results = search_documents("content", idx_path, category_filter="feature")
        assert all(r["category"] == "feature" for r in results)


class TestGetIndexStats:
    def test_stats(self, mock_settings, doc_directory, tmp_root):
        idx_path = tmp_root / ".index"
        index_all(tmp_root, idx_path, [".md"])
        stats = get_index_stats(idx_path)
        assert stats["total_documents"] == 3
        assert "feature" in stats["by_category"]
        assert "by_file_type" in stats


class TestRebuildIndex:
    def test_rebuild(self, mock_settings, doc_directory, tmp_root):
        idx_path = tmp_root / ".index"
        index_all(tmp_root, idx_path, [".md"])
        result = rebuild_index(tmp_root, idx_path, [".md"])
        assert result["total_indexed"] == 3


class TestSuggestSimilar:
    def test_similar(self, mock_settings, doc_directory, tmp_root):
        idx_path = tmp_root / ".index"
        index_all(tmp_root, idx_path, [".md"])
        docs = list(tmp_root.rglob("*.md"))
        if docs:
            results = suggest_similar_documents(docs[0], tmp_root, idx_path)
            assert isinstance(results, list)


class TestIndexToolsIntegration:
    def test_index_tool(self, mock_settings, doc_directory):
        result = index_documents_tool()
        assert result["total_indexed"] > 0

    def test_search_tool(self, mock_settings, doc_directory):
        index_documents_tool()
        results = search_documents_tool("Feature")
        assert isinstance(results, list)

    def test_stats_tool(self, mock_settings, doc_directory):
        index_documents_tool()
        stats = get_index_stats_tool()
        assert stats["total_documents"] > 0

    def test_rebuild_tool(self, mock_settings, doc_directory):
        index_documents_tool()
        result = rebuild_index_tool()
        assert result["total_indexed"] > 0
