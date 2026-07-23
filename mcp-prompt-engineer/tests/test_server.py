from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_prompt_engineer.server import mcp


def test_server_registers_prompt_tools() -> None:
    assert isinstance(mcp, FastMCP)
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert {"analyze_prompt", "improve_prompt", "get_prompt_template"} <= names
    assert len(names) == 20


def test_resources_registered() -> None:
    resources = asyncio.run(mcp.list_resources())
    assert len(resources) == 15
