"""Tests para mcp-object-storage server."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

from fastmcp import FastMCP


class TestServer:
    @patch("mcp_object_storage.server.boto3")
    def test_server_is_fastmcp_instance(self, mock_boto: any) -> None:
        from mcp_object_storage.server import mcp
        assert isinstance(mcp, FastMCP)

    @patch("mcp_object_storage.server.boto3")
    def test_server_name(self, mock_boto: any) -> None:
        from mcp_object_storage.server import mcp
        assert mcp.name == "mcp-object-storage"

    @patch("mcp_object_storage.server.boto3")
    def test_tool_count(self, mock_boto: any) -> None:
        from mcp_object_storage.server import mcp
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 15

    @patch("mcp_object_storage.server.boto3")
    def test_resources_registered(self, mock_boto: any) -> None:
        from mcp_object_storage.server import mcp
        resources = asyncio.run(mcp.list_resources())
        assert len(resources) == 15
