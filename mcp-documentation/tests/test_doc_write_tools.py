"""Tests para Doc Write Tools."""

from __future__ import annotations

from pathlib import Path

import pytest
import frontmatter

from mcp_documentation.tools.doc_write_tools import (
    add_tags,
    append_to_document,
    create_document,
    create_from_template,
    delete_document,
    move_document,
    update_document,
    update_frontmatter,
)


class TestCreateDocument:
    def test_create_with_frontmatter(self, mock_settings, tmp_root):
        result = create_document(
            title="New Feature Doc",
            content="# New Feature\n\nContent here.",
            doc_type="feature",
            project="test",
            tags=["test"],
            author="tester",
        )
        assert result["created"] is True
        assert "timestamp" in result
        p = Path(result["path"])
        assert p.exists()
        raw = p.read_text(encoding="utf-8")
        post = frontmatter.loads(raw)
        assert post.metadata["title"] == "New Feature Doc"
        assert post.metadata["type"] == "feature"
        assert "timestamp" in post.metadata

    def test_create_auto_classify_directory(self, mock_settings, tmp_root):
        result = create_document(
            title="Bug Fix Report",
            content="Fix content",
            doc_type="fix",
        )
        assert "fix" in result["path"]

    def test_create_short_title_raises(self, mock_settings, tmp_root):
        with pytest.raises(ValueError, match="título"):
            create_document(title="AB", content="content")

    def test_create_existing_raises(self, mock_settings, tmp_root):
        create_document(title="Test Doc", content="content", filename="test.md", directory="")
        with pytest.raises(ValueError, match="ya existe"):
            create_document(title="Test Doc", content="content", filename="test.md", directory="")


class TestUpdateDocument:
    def test_update_content(self, mock_settings, sample_md_file):
        result = update_document(sample_md_file, "# Updated\n\nNew content.")
        assert result["updated"] is True
        raw = Path(sample_md_file).read_text(encoding="utf-8")
        post = frontmatter.loads(raw)
        assert "Updated" in post.content

    def test_update_timestamp(self, mock_settings, sample_md_file):
        original = frontmatter.loads(Path(sample_md_file).read_text())
        update_document(sample_md_file, "new content")
        updated = frontmatter.loads(Path(sample_md_file).read_text())
        assert updated.metadata["timestamp"] != original.metadata["timestamp"]


class TestAppendToDocument:
    def test_append(self, mock_settings, sample_md_file):
        result = append_to_document(sample_md_file, "Appended section.")
        assert result["appended"] is True
        raw = Path(sample_md_file).read_text(encoding="utf-8")
        assert "Appended section." in raw


class TestUpdateFrontmatter:
    def test_update_field(self, mock_settings, sample_md_file):
        result = update_frontmatter(sample_md_file, {"status": "active"})
        assert result["updated"] is True
        raw = frontmatter.loads(Path(sample_md_file).read_text())
        assert raw.metadata["status"] == "active"


class TestAddTags:
    def test_add_new_tag(self, mock_settings, sample_md_file):
        result = add_tags(sample_md_file, ["new-tag", "python"])
        assert "new-tag" in result["tags"]
        assert "python" in result["tags"]


class TestDeleteDocument:
    def test_delete(self, mock_settings, sample_md_file):
        result = delete_document(sample_md_file)
        assert result["deleted"] is True
        assert not Path(sample_md_file).exists()

    def test_delete_nonexistent(self, mock_settings, tmp_root):
        with pytest.raises(FileNotFoundError):
            delete_document(str(tmp_root / "nope.md"))


class TestCreateFromTemplate:
    def test_create_feature_template(self, mock_settings, tmp_root):
        result = create_from_template("feature", "My Feature", project="test")
        assert result["created"] is True
        assert result["type"] == "feature"
        raw = Path(result["path"]).read_text(encoding="utf-8")
        assert "Descripción" in raw

    def test_create_fix_template(self, mock_settings, tmp_root):
        result = create_from_template("fix", "My Fix")
        assert result["type"] == "fix"
        raw = Path(result["path"]).read_text(encoding="utf-8")
        assert "Root Cause" in raw

    def test_create_decision_template(self, mock_settings, tmp_root):
        result = create_from_template("decision", "My ADR")
        assert result["type"] == "decision"
        raw = Path(result["path"]).read_text(encoding="utf-8")
        assert "ADR" in raw or "Alternativas" in raw


class TestMoveDocument:
    def test_move(self, mock_settings, sample_md_file, tmp_root):
        result = move_document(sample_md_file, "fix")
        assert result["moved"] is True
        assert "fix" in result["new_path"]
        assert not Path(sample_md_file).exists()
        assert Path(result["new_path"]).exists()
