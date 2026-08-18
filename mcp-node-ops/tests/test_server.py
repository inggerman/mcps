"""Tests básicos del servidor mcp-node-ops."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_node_ops.server import mcp

_EXPECTED_TOOLS = {
    "list_nodes", "get_node_details", "cordon_node", "uncordon_node",
    "drain_node", "get_node_taints", "set_node_label",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-node-ops"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 7
