from __future__ import annotations

import asyncio
import inspect

from fastmcp import FastMCP
from mcp_calendar.server import (
    mcp,
    settings,
    tool_calculate_business_days,
    tool_get_exchange_rate,
)


def test_server_registers_calendar_tools() -> None:
    assert isinstance(mcp, FastMCP)
    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert {"get_holidays", "calculate_business_days", "get_exchange_rate"} <= names
    assert len(names) == 15


def test_tool_defaults_come_from_settings() -> None:
    business_days = inspect.signature(tool_calculate_business_days)
    exchange_rate = inspect.signature(tool_get_exchange_rate)

    assert business_days.parameters["country"].default == settings.default_country
    assert exchange_rate.parameters["ttl_seconds"].default == settings.exchange_cache_ttl_seconds
