"""Tools públicas de mcp-fetch."""

from __future__ import annotations

from mcp_fetch.tools.fetch_tools import (
    extract_text,
    fetch_json,
    fetch_post,
    fetch_url,
)

__all__ = ["fetch_url", "fetch_post", "extract_text", "fetch_json"]
