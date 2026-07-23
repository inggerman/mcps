"""Tests for mcp-browser server registration."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_browser.server import mcp

_EXPECTED_TOOLS = {
    "browser_extract", "browser_screenshot",
    "browser_get_title", "browser_get_links", "browser_get_metadata",
    "browser_get_text", "browser_click", "browser_fill_form",
    "browser_wait_for", "browser_scroll", "browser_evaluate",
    "browser_get_cookies", "browser_set_viewport",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-browser"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 13

    def test_resources_registered(self) -> None:
        resources = asyncio.run(mcp.list_resources())
        assert len(resources) == 14
