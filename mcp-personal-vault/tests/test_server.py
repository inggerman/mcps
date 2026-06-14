from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_personal_vault.server import mcp


def test_server_contract() -> None:
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "mcp-personal-vault"
    tools = {tool.name for tool in asyncio.run(mcp.list_tools())}
    assert tools == {
        "personal_vault_status",
        "personal_upsert",
        "personal_get",
        "personal_list",
        "search_personal_context",
        "personal_delete",
    }
