"""Tests básicos para el servidor FastMCP mcp-markdown."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_markdown.server import mcp


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-markdown"

    def test_tools_registered(self) -> None:
        """Verifica que todas las herramientas esperadas están registradas."""
        tools = mcp._tool_manager.list_tools()
        tool_names = {t.name for t in tools}
        expected = {
            "read_markdown",
            "extract_headings",
            "extract_links",
            "extract_code_blocks",
            "get_toc",
            "markdown_to_html",
            "markdown_to_plain_text",
            "validate_markdown",
            "search_in_markdown",
            "format_markdown",
            "get_frontmatter",
            "list_markdown_files",
        }
        assert expected.issubset(tool_names), (
            f"Tools faltantes: {expected - tool_names}"
        )

    def test_tool_count(self) -> None:
        tools = mcp._tool_manager.list_tools()
        assert len(tools) >= 12
