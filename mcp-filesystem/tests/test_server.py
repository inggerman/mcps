from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from fastmcp import FastMCP
from mcp_filesystem.server import mcp  # noqa: F401


def test_server_registers_filesystem_tools() -> None:
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert {"filesystem_list", "filesystem_read_text", "filesystem_search"} <= names
    assert "filesystem_head" in names
    assert "filesystem_tree" in names
    assert "filesystem_copy" in names
    assert len(names) == 16


def test_server_registers_filesystem_resources() -> None:
    resources = asyncio.run(mcp.list_resources())
    templates = asyncio.run(mcp.list_resource_templates())
    assert len(resources) == 12
    assert len(templates) == 8
    resource_uris = {str(r.uri) for r in resources}
    assert "fs://supported-operations" in resource_uris
    assert "fs://symlink-tips" in resource_uris
    template_uris = {str(t.uri_template) for t in templates}
    assert "fs://file/{path}/info" in template_uris
    assert "fs://dir/{path}/tree" in template_uris
