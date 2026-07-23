"""Tests para mcp-kubernetes server."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

from fastmcp import FastMCP


class TestServer:
    @patch("mcp_kubernetes.server.config")
    def test_server_is_fastmcp_instance(self, mock_config: any) -> None:
        from mcp_kubernetes.server import mcp
        assert isinstance(mcp, FastMCP)

    @patch("mcp_kubernetes.server.config")
    def test_server_name(self, mock_config: any) -> None:
        from mcp_kubernetes.server import mcp
        assert mcp.name == "mcp-kubernetes"

    @patch("mcp_kubernetes.server.config")
    def test_tool_count(self, mock_config: any) -> None:
        from mcp_kubernetes.server import mcp
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 15

    @patch("mcp_kubernetes.server.config")
    def test_resources_registered(self, mock_config: any) -> None:
        from mcp_kubernetes.server import mcp
        resources = asyncio.run(mcp.list_resources())
        assert len(resources) == 15
