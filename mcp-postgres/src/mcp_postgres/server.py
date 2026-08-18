"""Servidor FastMCP para mcp-postgres."""

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

from mcp_postgres.config import settings
from mcp_postgres.tools import (
    describe_table,
    execute_query,
    list_databases,
    list_tables,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-postgres",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-postgres")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-postgres",
    instructions=(
        "Servidor MCP para PostgreSQL. "
        "Herramientas: list_databases, list_tables, describe_table, "
        "execute_query (read-only por defecto, POSTGRES_ALLOW_WRITE=true para escritura). "
        "Limita resultados a POSTGRES_MAX_ROWS filas."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_databases", description="Lista las bases de datos de PostgreSQL. Retorna: lista de {name, encoding, size}.")
def tool_list_databases() -> list[dict[str, Any]]:
    logger.info("list_databases llamado")
    try:
        return list_databases()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_databases", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_tables", description="Lista las tablas de una base de datos. Parámetros: database (str opcional). Retorna: lista de {name, schema, size}.")
def tool_list_tables(database: str | None = None) -> list[dict[str, Any]]:
    logger.info("list_tables llamado", database=database)
    try:
        return list_tables(database=database)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_tables", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="describe_table", description="Describe la estructura de una tabla. Parámetros: table_name (str, formato schema.table), database (str opcional). Retorna: lista de {column, type, nullable, default, max_length}.")
def tool_describe_table(table_name: str, database: str | None = None) -> list[dict[str, Any]]:
    logger.info("describe_table llamado", table_name=table_name, database=database)
    try:
        return describe_table(table_name=table_name, database=database)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en describe_table", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="execute_query", description="Ejecuta una query SQL. Read-only por defecto (POSTGRES_ALLOW_WRITE=true para escritura). Parámetros: sql (str), database (str opcional). Retorna: {columns, rows, row_count, truncated}.")
def tool_execute_query(sql: str, database: str | None = None) -> dict[str, Any]:
    logger.info("execute_query llamado", sql=sql[:100], database=database)
    try:
        return execute_query(sql=sql, database=database)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en execute_query", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
