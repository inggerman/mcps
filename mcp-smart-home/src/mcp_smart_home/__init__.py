"""
Paquete mcp-smart-home — MCP server para domótica Tuya SmartLife.
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "MCP Framework Team"

__all__ = [
    "SmartHomeSettings",
    "__version__",
    "create_server",
]

from mcp_smart_home.config import SmartHomeSettings
from mcp_smart_home.server import create_server
