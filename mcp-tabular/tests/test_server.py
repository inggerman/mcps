from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_tabular.server import mcp


def test_server_registers_tabular_tools() -> None:
    assert isinstance(mcp, FastMCP)
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert {"read_tabular_file", "filter_rows", "get_column_stats"} <= names
    assert "sort_rows" in names
    assert "drop_duplicates" in names
    assert "get_correlation" in names
    assert len(names) == 25


def test_server_registers_tabular_resources() -> None:
    resources = asyncio.run(mcp.list_resources())
    templates = asyncio.run(mcp.list_resource_templates())
    assert len(resources) == 12
    assert len(templates) == 13
    resource_uris = {str(r.uri) for r in resources}
    assert "tabular://supported-formats" in resource_uris
    assert "tabular://cheatsheet/pandas" in resource_uris
    template_uris = {str(t.uri_template) for t in templates}
    assert "tabular://file/{path}/schema" in template_uris
    assert "tabular://file/{path}/column/{column}/stats" in template_uris
