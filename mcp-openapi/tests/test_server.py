"""Tests para mcp-openapi server."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

from fastmcp import FastMCP


class TestServer:
    @patch("mcp_openapi.server.load_spec")
    def test_server_is_fastmcp_instance(self, mock_spec: any) -> None:
        mock_spec.return_value = {"openapi": "3.1.0", "info": {"title": "test", "version": "1"}, "paths": {}}
        from mcp_openapi.server import mcp
        assert isinstance(mcp, FastMCP)

    @patch("mcp_openapi.server.load_spec")
    def test_server_name(self, mock_spec: any) -> None:
        mock_spec.return_value = {"openapi": "3.1.0", "info": {"title": "test", "version": "1"}, "paths": {}}
        from mcp_openapi.server import mcp
        assert mcp.name == "mcp-openapi"

    @patch("mcp_openapi.server.load_spec")
    def test_tool_count(self, mock_spec: any) -> None:
        mock_spec.return_value = {"openapi": "3.1.0", "info": {"title": "test", "version": "1"}, "paths": {}}
        from mcp_openapi.server import mcp
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 15

    @patch("mcp_openapi.server.load_spec")
    def test_resources_registered(self, mock_spec: any) -> None:
        mock_spec.return_value = {"openapi": "3.1.0", "info": {"title": "test", "version": "1"}, "paths": {}}
        from mcp_openapi.server import mcp
        resources = asyncio.run(mcp.list_resources())
        assert len(resources) == 15
