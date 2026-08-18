"""Tests básicos del servidor mcp-deploy-tracker."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_deploy_tracker.server import mcp

_EXPECTED_TOOLS = {
    "list_deployments", "get_deployment_status",
    "get_rollout_status", "get_replica_set_history",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-deploy-tracker"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 4
