from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_calendar.server import mcp


def test_server_registers_calendar_tools() -> None:
    assert isinstance(mcp, FastMCP)
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert {"get_holidays", "calculate_business_days", "get_exchange_rate"} <= names
    assert len(names) == 15
