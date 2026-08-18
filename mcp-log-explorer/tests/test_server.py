"""Tests básicos del servidor mcp-log-explorer."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_log_explorer.server import mcp

_EXPECTED_TOOLS = {"get_pod_logs", "tail_pod_logs", "search_logs_across_pods"}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-log-explorer"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 3
