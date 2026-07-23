"""Tests para mcp-sonar server."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        from mcp_sonar.server import mcp
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        from mcp_sonar.server import mcp
        assert mcp.name == "mcp-sonar"

    def test_tool_count(self) -> None:
        from mcp_sonar.server import mcp
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 15

    def test_resources_registered(self) -> None:
        from mcp_sonar.server import mcp
        resources = asyncio.run(mcp.list_resources())
        assert len(resources) == 15
