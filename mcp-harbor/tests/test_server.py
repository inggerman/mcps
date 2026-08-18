"""Tests básicos del servidor mcp-harbor."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_harbor.server import mcp

_EXPECTED_TOOLS = {
    "list_projects", "list_repositories", "list_tags",
    "get_scan_report", "image_exists", "delete_tag",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-harbor"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 6
