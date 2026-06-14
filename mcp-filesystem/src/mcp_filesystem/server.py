"""FastMCP server for sandboxed filesystem access."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_filesystem.config import settings
from mcp_filesystem.tools import list_directory, read_text_file, search_files, write_text_file

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-filesystem",
)
logger = get_logger(__name__)
mcp = FastMCP(
    name="mcp-filesystem",
    instructions="Acceso al filesystem confinado a FILESYSTEM_ROOT. Escritura desactivada por defecto.",
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="filesystem_list")
def tool_list(path: str = ".", recursive: bool = False) -> list[dict[str, Any]]:
    return _handle(list_directory, settings.root, path, recursive, settings.max_results)


@mcp.tool(name="filesystem_read_text")
def tool_read(path: str) -> dict[str, Any]:
    return _handle(read_text_file, settings.root, path, settings.max_read_bytes)


@mcp.tool(name="filesystem_search")
def tool_search(pattern: str = "*", text_query: str | None = None) -> list[dict[str, Any]]:
    return _handle(
        search_files,
        settings.root,
        pattern,
        text_query,
        settings.max_results,
        settings.max_read_bytes,
    )


@mcp.tool(name="filesystem_write_text")
def tool_write(path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
    return _handle(write_text_file, settings.root, path, content, settings.allow_write, overwrite)


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
