"""Tests básicos del servidor mcp-config-sync."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_config_sync.server import mcp

_EXPECTED_TOOLS = {
    "list_configmaps", "get_configmap", "list_secrets",
    "compare_configmaps", "sync_configmap",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-config-sync"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 5
