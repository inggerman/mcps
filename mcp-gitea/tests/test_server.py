"""Tests básicos del servidor mcp-gitea."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_gitea.server import mcp

_EXPECTED_TOOLS = {
    "list_repos", "list_prs", "create_pr",
    "list_issues", "create_issue",
    "get_workflow_runs", "get_run_logs",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-gitea"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 7
