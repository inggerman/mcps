"""Tests for write tools (gated by ALLOW_WRITE)."""

from unittest.mock import patch

import pytest

from mcp_shared.errors import McpError


def test_update_standard_blocked_without_write():
    """update_standard raises when ALLOW_WRITE is false."""
    with patch("mcp_engineering_knowledge.tools.write_tools.settings") as mock_settings:
        mock_settings.allow_write = False
        from mcp_engineering_knowledge.tools.write_tools import update_standard
        with pytest.raises(McpError, match="Write not permitted"):
            update_standard("refactoring", "# New content")


def test_add_pattern_blocked_without_write():
    """add_pattern raises when ALLOW_WRITE is false."""
    with patch("mcp_engineering_knowledge.tools.write_tools.settings") as mock_settings:
        mock_settings.allow_write = False
        from mcp_engineering_knowledge.tools.write_tools import add_pattern
        with pytest.raises(McpError, match="Write not permitted"):
            add_pattern("new-pattern", "# New pattern")


def test_reindex_blocked_without_write():
    """reindex raises when ALLOW_WRITE is false."""
    with patch("mcp_engineering_knowledge.tools.write_tools.settings") as mock_settings:
        mock_settings.allow_write = False
        from mcp_engineering_knowledge.tools.write_tools import reindex
        with pytest.raises(McpError, match="Write not permitted"):
            reindex(full=False)


def test_invalidate_blocked_without_write():
    """invalidate_files raises when ALLOW_WRITE is false."""
    with patch("mcp_engineering_knowledge.tools.write_tools.settings") as mock_settings:
        mock_settings.allow_write = False
        from mcp_engineering_knowledge.tools.write_tools import invalidate_files
        with pytest.raises(McpError, match="Write not permitted"):
            invalidate_files(["test.md"])


def test_get_status_always_available():
    """get_status is always available (read-only)."""
    with patch("mcp_engineering_knowledge.tools.write_tools.settings") as mock_settings:
        mock_settings.allow_write = False
        mock_settings.docs_path = "/nonexistent"
        from mcp_engineering_knowledge.tools.write_tools import get_status
        # Should not raise McpError about write permission
        # It may raise other errors (Qdrant not available) but not the write gate
        try:
            get_status()
        except McpError as exc:
            assert "Write not permitted" not in str(exc)
        except Exception:
            pass  # Qdrant not available in test env
