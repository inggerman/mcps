"""Tests para health + metrics tools."""

from __future__ import annotations

from pathlib import Path

from mcp_documentation.health import get_metrics, health_check


def test_health_check_empty_root(tmp_root: Path):
    result = health_check(tmp_root, tmp_root / ".index")
    assert result["status"] in ("healthy", "degraded")
    assert result["filesystem"]["exists"] is True
    assert result["documents"]["count"] == 0
    assert result["sessions"]["count"] == 0
    assert result["versions"]["count"] == 0
    assert "timestamp" in result


def test_health_check_with_docs(tmp_root: Path):
    (tmp_root / "feature").mkdir()
    (tmp_root / "feature" / "doc1.md").write_text(
        "---\ntitle: Test\ntype: feature\n---\nContent", encoding="utf-8"
    )
    result = health_check(tmp_root, tmp_root / ".index")
    assert result["documents"]["count"] == 1
    assert result["status"] in ("healthy", "degraded")


def test_health_check_writable(tmp_root: Path):
    result = health_check(tmp_root, tmp_root / ".index")
    assert result["filesystem"]["writable"] is True


def test_get_metrics_format(tmp_root: Path):
    metrics = get_metrics(tmp_root, tmp_root / ".index")
    assert "mcp_documentation_docs_total" in metrics
    assert "mcp_documentation_sessions_total" in metrics
    assert "mcp_documentation_versions_total" in metrics
    assert "mcp_documentation_audit_entries_total" in metrics
    assert "mcp_documentation_health_status" in metrics


def test_health_tools_integration(mock_settings):
    from mcp_documentation.tools.health_tools import (
        get_metrics_tool,
        health_check_tool,
    )

    health = health_check_tool()
    assert "status" in health
    assert "documents" in health

    metrics = get_metrics_tool()
    assert "mcp_documentation_docs_total" in metrics
