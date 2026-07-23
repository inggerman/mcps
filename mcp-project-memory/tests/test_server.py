"""Tests del servidor mcp-project-memory."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_project_memory.server import mcp

_EXPECTED_TOOLS = {
    "get_project_state",
    "generate_project_brief",
    "get_component_map",
    "get_decisions_history",
    "get_session_history",
    "search_memory",
    "diff_state",
    "export_memory_snapshot",
    "snapshot_session",
    "update_component_status",
    "record_decision",
    "add_pending_task",
    "complete_pending_task",
    "initialize_project",
    "sync_from_filesystem",
    "get_pending_tasks",
    "get_completed_tasks",
    "get_invariants",
    "add_invariant",
    "get_memory_stats",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-project-memory"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 20

    def test_resources_registered(self) -> None:
        resources = asyncio.run(mcp.list_resources())
        assert len(resources) == 15
