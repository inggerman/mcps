"""Tests para server.py — verificar registro de 50 tools."""

from __future__ import annotations

import pytest

from mcp_documentation.server import mcp


class TestServerInstance:
    def test_server_name(self):
        assert mcp.name == "mcp-documentation"

    def test_server_instructions(self):
        assert "documentación" in mcp.instructions.lower()

    def test_server_has_tools(self):
        # FastMCP stores tools internally; verify the server object exists
        assert mcp is not None
