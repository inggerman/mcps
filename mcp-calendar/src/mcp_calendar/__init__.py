"""
Paquete mcp-calendar — MCP server para días hábiles y tasas de cambio.
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "MCP Framework Team"

__all__ = [
    "CalendarSettings",
    "__version__",
    "create_server",
]

from mcp_calendar.config import CalendarSettings
from mcp_calendar.server import create_server
