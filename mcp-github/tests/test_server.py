"""Tests for mcp-github server registration."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP
from mcp_github.server import mcp

_EXPECTED_TOOLS = {
    "github_create_issue", "github_get_issue", "github_create_pull_request",
    "github_get_pull_request_diff", "github_add_issue_comment",
    "github_list_issues", "github_list_branches", "github_list_commits",
    "github_get_file_content", "github_get_repo_info", "github_get_user_info",
    "github_list_pull_requests", "github_get_pull_request_files",
    "github_create_branch", "github_get_issue_comments",
}


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-github"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert _EXPECTED_TOOLS.issubset(tool_names)

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 15

    def test_resources_registered(self) -> None:
        resources = asyncio.run(mcp.list_resources())
        assert len(resources) == 14
