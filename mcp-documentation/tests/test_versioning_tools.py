"""Tests para versioning + audit tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_documentation.versioning import (
    audit,
    compare_versions,
    get_audit_log,
    get_document_history,
    restore_version,
    save_version,
)


def test_save_version(tmp_root: Path, sample_md_file: str):
    result = save_version(tmp_root, Path(sample_md_file), action="update")
    assert result["version"] == 1
    assert result["action"] == "update"
    versions_dir = tmp_root / ".versions"
    assert versions_dir.exists()
    assert len(list(versions_dir.glob("*.bak"))) == 1


def test_get_document_history(tmp_root: Path, sample_md_file: str):
    save_version(tmp_root, Path(sample_md_file), action="update")
    save_version(tmp_root, Path(sample_md_file), action="update")
    history = get_document_history(tmp_root, sample_md_file)
    assert len(history) == 2
    assert history[0]["version"] == 1
    assert history[1]["version"] == 2


def test_restore_version(tmp_root: Path, sample_md_file: str):
    original = Path(sample_md_file).read_text(encoding="utf-8")
    save_version(tmp_root, Path(sample_md_file), action="update")

    Path(sample_md_file).write_text("modified content", encoding="utf-8")
    assert Path(sample_md_file).read_text() != original

    result = restore_version(tmp_root, sample_md_file, version=1)
    assert result["restored"] is not None
    assert Path(sample_md_file).read_text(encoding="utf-8") == original


def test_compare_versions(tmp_root: Path, sample_md_file: str):
    save_version(tmp_root, Path(sample_md_file), action="update")
    Path(sample_md_file).write_text("---\ntitle: Changed\n---\nNew content", encoding="utf-8")
    save_version(tmp_root, Path(sample_md_file), action="update")

    result = compare_versions(tmp_root, sample_md_file, 1, 2)
    assert result["version_a"] == 1
    assert result["version_b"] == 2
    assert "diff" in result
    assert result["lines_changed"] > 0


def test_audit_log(tmp_root: Path):
    audit(tmp_root, "create", "test.md", {"title": "Test"})
    audit(tmp_root, "update", "test.md", {"keys": ["status"]})
    audit(tmp_root, "delete", "test.md")

    entries = get_audit_log(tmp_root, limit=10)
    assert len(entries) == 3
    assert entries[0]["action"] == "delete"

    filtered = get_audit_log(tmp_root, action_filter="create")
    assert len(filtered) == 1
    assert filtered[0]["action"] == "create"


def test_audit_log_empty(tmp_root: Path):
    entries = get_audit_log(tmp_root)
    assert entries == []


def test_versioning_tools_integration(mock_settings, sample_md_file: str):
    from mcp_documentation.tools.versioning_tools import (
        get_audit_log_tool,
        get_document_history_tool,
    )

    history = get_document_history_tool(sample_md_file)
    assert isinstance(history, list)

    log = get_audit_log_tool(limit=5)
    assert isinstance(log, list)
