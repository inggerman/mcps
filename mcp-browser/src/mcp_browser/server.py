from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_browser.config import settings
from mcp_browser.tools import capture_page, extract_page

setup_logging(
    log_level=settings.log_level, log_format=settings.log_format, server_name="mcp-browser"
)
logger = get_logger(__name__)
mcp = FastMCP(
    name="mcp-browser", instructions="Automatización web con Playwright y allowlist opcional."
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="browser_extract")
def tool_extract(url: str, selector: str = "body") -> dict[str, Any]:
    return _handle(
        extract_page,
        url,
        settings.allowed_hosts,
        settings.headless,
        settings.timeout_ms,
        selector,
    )


@mcp.tool(name="browser_screenshot")
def tool_screenshot(
    url: str,
    filename: str = "screenshot.png",
    full_page: bool = True,
) -> dict[str, Any]:
    return _handle(
        capture_page,
        url,
        settings.allowed_hosts,
        settings.output_dir,
        settings.headless,
        settings.timeout_ms,
        filename,
        full_page,
    )


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
