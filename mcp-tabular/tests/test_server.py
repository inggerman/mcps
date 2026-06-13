from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_tabular.server import mcp


def test_server_registers_tabular_tools() -> None:
    assert isinstance(mcp, FastMCP)
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert {"read_tabular_file", "filter_rows", "get_column_stats"} <= names
    assert len(names) == 8
