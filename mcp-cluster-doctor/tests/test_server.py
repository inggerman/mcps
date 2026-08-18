"""Tests básicos del servidor mcp-cluster-doctor."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_cluster_doctor.server import mcp

_EXPECTED_TOOLS = {
    "get_node_health", "get_pod_status",
    "get_cluster_events", "get_resource_usage",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-cluster-doctor"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 4
