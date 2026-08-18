"""Tests básicos del servidor mcp-health-monitor."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_health_monitor.server import mcp

_EXPECTED_TOOLS = {
    "get_probe_status", "get_hpa_status",
    "check_endpoint_health", "get_unhealthy_pods",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-health-monitor"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 4
