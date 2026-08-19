"""Tests para Investigation Tools."""

from __future__ import annotations

from pathlib import Path

import frontmatter
import pytest

from mcp_documentation.tools.investigation_tools import (
    add_evidence,
    close_investigation,
    create_investigation,
)


class TestCreateInvestigation:
    def test_create(self, mock_settings, tmp_root):
        result = create_investigation(
            "Root Cause Analysis",
            "The issue is caused by a race condition in the auth module.",
            project="test",
        )
        assert result["created"] is True
        assert result["type"] == "investigation"
        content = Path(result["path"]).read_text(encoding="utf-8")
        assert "Hipótesis" in content
        assert "race condition" in content

    def test_short_hypothesis_raises(self, mock_settings, tmp_root):
        with pytest.raises(ValueError, match="hipótesis"):
            create_investigation("Test", "short")


class TestAddEvidence:
    def test_add_log_evidence(self, mock_settings, tmp_root):
        inv = create_investigation("Test Inv", "Hypothesis about the bug in auth.")
        result = add_evidence(inv["path"], "log", "Found error in auth.log at line 42")
        assert result["appended"] is True
        content = Path(inv["path"]).read_text(encoding="utf-8")
        assert "Evidencia [LOG]" in content
        assert "auth.log" in content

    def test_add_with_reference(self, mock_settings, tmp_root):
        inv = create_investigation("Test Inv", "Hypothesis about the bug.")
        result = add_evidence(inv["path"], "code", "Bug in function X", reference="src/auth.py:42")
        content = Path(inv["path"]).read_text(encoding="utf-8")
        assert "src/auth.py" in content

    def test_invalid_evidence_type(self, mock_settings, tmp_root):
        inv = create_investigation("Test Inv", "Hypothesis about the bug.")
        with pytest.raises(ValueError, match="Tipos válidos"):
            add_evidence(inv["path"], "invalid_type", "description")


class TestCloseInvestigation:
    def test_close_resolved(self, mock_settings, tmp_root):
        inv = create_investigation("Test Inv", "Hypothesis about the bug.")
        result = close_investigation(
            inv["path"],
            status="resolved",
            conclusions="The root cause was identified and fixed.",
            lessons="Always check for race conditions.",
        )
        assert result["closed"] is True
        assert result["status"] == "resolved"
        content = Path(inv["path"]).read_text(encoding="utf-8")
        post = frontmatter.loads(content)
        assert post.metadata["status"] == "resolved"
        assert post.metadata["investigation_status"] == "closed"

    def test_close_invalid_status(self, mock_settings, tmp_root):
        inv = create_investigation("Test Inv", "Hypothesis about the bug.")
        with pytest.raises(ValueError, match="Estados válidos"):
            close_investigation(inv["path"], "invalid", "conclusions")

    def test_close_short_conclusions(self, mock_settings, tmp_root):
        inv = create_investigation("Test Inv", "Hypothesis about the bug.")
        with pytest.raises(ValueError, match="conclusiones"):
            close_investigation(inv["path"], "resolved", "short")
