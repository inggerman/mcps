"""FastMCP server for database access."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_database.config import settings
from mcp_database.tools import describe_table, execute_query, get_database_info, list_tables
from mcp_database.tools.database_tools import create_database_engine

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-database",
)
logger = get_logger(__name__)
engine = create_database_engine(settings.url, settings.statement_timeout_seconds)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-database")
    logger.info("mcp-database iniciando", **settings.to_log_context())
    yield
    engine.dispose()
    structlog.contextvars.clear_contextvars()


mcp = FastMCP(
    name="mcp-database",
    instructions="Inspección y consultas SQL seguras. El modo solo lectura está activo por defecto.",
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="database_info")
def tool_database_info() -> dict[str, Any]:
    return _handle(get_database_info, engine)


@mcp.tool(name="database_list_tables")
def tool_list_tables(schema: str | None = None) -> list[dict[str, Any]]:
    return _handle(list_tables, engine, schema)


@mcp.tool(name="database_describe_table")
def tool_describe_table(table: str, schema: str | None = None) -> dict[str, Any]:
    return _handle(describe_table, engine, table, schema)


@mcp.tool(name="database_query")
def tool_execute_query(
    query: str,
    parameters: dict[str, Any] | None = None,
    max_rows: int | None = None,
) -> dict[str, Any]:
    return _handle(
        execute_query,
        engine,
        query,
        parameters,
        min(max_rows or settings.max_rows, settings.max_rows),
        settings.read_only,
    )


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
