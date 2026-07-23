"""Tests para mcp-orchestrator server."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from mcp_orchestrator.server import mcp


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-orchestrator"

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 15

    def test_resources_registered(self) -> None:
        resources = asyncio.run(mcp.list_resources())
        assert len(resources) == 15
