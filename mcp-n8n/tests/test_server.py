"""Tests básicos del servidor mcp-n8n."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_n8n.server import mcp

_EXPECTED_TOOLS = {
    "list_workflows", "get_workflow", "trigger_webhook",
    "list_executions", "get_execution_detail", "activate_workflow",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-n8n"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 6
