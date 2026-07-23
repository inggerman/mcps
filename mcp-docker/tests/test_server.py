"""Tests básicos del servidor mcp-docker."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_docker.server import mcp

_EXPECTED_TOOLS = {
    "containers_list",
    "containers_stats",
    "container_logs",
    "container_exec",
    "run_container",
    "stop_container",
    "images_list",
    "image_pull",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-docker"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 20

    def test_resources_registered(self) -> None:
        resources = asyncio.run(mcp.list_resources())
        assert len(resources) == 15
