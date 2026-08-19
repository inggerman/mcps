"""Tests para backup + export tools."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from mcp_documentation.backup import (
    backup_documents,
    export_documents,
    list_backups,
    restore_backup,
)


def test_backup_documents(tmp_root: Path, doc_directory: str):
    result = backup_documents(tmp_root)
    assert result["files_included"] > 0
    assert result["size_bytes"] > 0
    assert Path(result["backup_file"]).exists()
    assert zipfile.is_zipfile(result["backup_file"])


def test_backup_empty_root(tmp_root: Path):
    result = backup_documents(tmp_root)
    assert result["files_included"] == 0
    assert Path(result["backup_file"]).exists()


def test_backup_exclude_versions(tmp_root: Path, sample_md_file: str):
    from mcp_documentation.versioning import save_version
    save_version(tmp_root, Path(sample_md_file), action="update")

    result_with = backup_documents(tmp_root, include_versions=True)
    result_without = backup_documents(tmp_root, include_versions=False)
    assert result_with["files_included"] > result_without["files_included"]


def test_restore_backup(tmp_root: Path, doc_directory: str):
    backup_result = backup_documents(tmp_root)

    for f in tmp_root.rglob("*.md"):
        if not str(f).startswith("."):
            f.unlink()

    restore_result = restore_backup(tmp_root, backup_result["backup_file"])
    assert restore_result["files_restored"] > 0

    docs = list(tmp_root.rglob("*.md"))
    assert len(docs) > 0


def test_export_documents_all(tmp_root: Path, doc_directory: str):
    result = export_documents(tmp_root)
    assert result["files_exported"] > 0
    assert Path(result["export_file"]).exists()


def test_export_by_category(tmp_root: Path, doc_directory: str):
    result = export_documents(tmp_root, category="feature")
    assert result["files_exported"] == 1
    assert result["category_filter"] == "feature"


def test_export_by_directory(tmp_root: Path, doc_directory: str):
    result = export_documents(tmp_root, directory="fix")
    assert result["files_exported"] == 1
    assert result["directory_filter"] == "fix"


def test_list_backups(tmp_root: Path, sample_md_file: str):
    backup_documents(tmp_root)
    backup_documents(tmp_root)
    backups = list_backups(tmp_root)
    assert len(backups) == 2
    assert backups[0]["name"].startswith("mcp-doc-backup-")
    assert backups[0]["size_mb"] >= 0


def test_list_backups_empty(tmp_root: Path):
    backups = list_backups(tmp_root)
    assert backups == []


def test_backup_tools_integration(mock_settings, doc_directory: str):
    from mcp_documentation.tools.backup_tools import (
        backup_documents_tool,
        list_backups_tool,
    )

    result = backup_documents_tool()
    assert result["files_included"] > 0

    backups = list_backups_tool()
    assert len(backups) >= 1
