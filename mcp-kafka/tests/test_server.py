"""Tests básicos del servidor mcp-kafka."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_kafka.server import mcp

_EXPECTED_TOOLS = {
    "topics_list",
    "topic_describe",
    "consumer_groups_list",
    "consumer_group_offsets",
    "produce_message",
    "consume_messages",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-kafka"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) >= 6
