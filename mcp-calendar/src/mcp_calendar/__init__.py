"""
Paquete mcp-calendar — MCP server para días hábiles y tasas de cambio.
"""

__version__ = "1.0.0"
__all__ = ["CalendarSettings", "create_server"]

from mcp_calendar.config import CalendarSettings
from mcp_calendar.server import create_server
