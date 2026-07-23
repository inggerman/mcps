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
from mcp_database.tools import (
    describe_table,
    execute_query,
    explain_query,
    export_to_csv,
    export_to_json,
    get_database_info,
    get_schemas,
    get_table_stats,
    get_views,
    list_tables,
    query_to_markdown,
    table_distinct_values,
    table_row_count,
    table_sample,
)
from mcp_database.tools.database_tools import create_database_engine
from mcp_database import resources as res

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


# ---------------------------------------------------------------------------
# Tools originales
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(name="database_table_row_count")
def tool_table_row_count(table: str, schema: str | None = None) -> dict[str, Any]:
    return _handle(table_row_count, engine, table, schema)


@mcp.tool(name="database_table_sample")
def tool_table_sample(table: str, n: int = 10, schema: str | None = None) -> dict[str, Any]:
    return _handle(table_sample, engine, table, n, schema)


@mcp.tool(name="database_distinct_values")
def tool_distinct_values(table: str, column: str, n: int = 50, schema: str | None = None) -> dict[str, Any]:
    return _handle(table_distinct_values, engine, table, column, n, schema)


@mcp.tool(name="database_table_stats")
def tool_table_stats(table: str, schema: str | None = None) -> dict[str, Any]:
    return _handle(get_table_stats, engine, table, schema)


@mcp.tool(name="database_explain")
def tool_explain(query: str) -> dict[str, Any]:
    return _handle(explain_query, engine, query, settings.read_only)


@mcp.tool(name="database_export_csv")
def tool_export_csv(table: str, max_rows: int = 1000, schema: str | None = None) -> str:
    return _handle(export_to_csv, engine, table, min(max_rows, settings.max_rows), schema)


@mcp.tool(name="database_export_json")
def tool_export_json(table: str, max_rows: int = 1000, schema: str | None = None) -> str:
    return _handle(export_to_json, engine, table, min(max_rows, settings.max_rows), schema)


@mcp.tool(name="database_schemas")
def tool_schemas() -> list[str]:
    return _handle(get_schemas, engine)


@mcp.tool(name="database_views")
def tool_views(schema: str | None = None) -> list[str]:
    return _handle(get_views, engine, schema)


@mcp.tool(name="database_query_markdown")
def tool_query_markdown(query: str, max_rows: int = 50) -> str:
    return _handle(query_to_markdown, engine, query, min(max_rows, settings.max_rows), settings.read_only)


# ---------------------------------------------------------------------------
# Resources estáticos
# ---------------------------------------------------------------------------


@mcp.resource("db://supported-dialects")
def res_supported_dialects() -> str:
    return res.supported_sql_dialects()


@mcp.resource("db://sql-safety-tips")
def res_sql_safety_tips() -> str:
    return res.sql_safety_tips()


@mcp.resource("db://sql-cheatsheet")
def res_sql_cheatsheet() -> str:
    return res.sql_cheatsheet()


@mcp.resource("db://query-performance-tips")
def res_query_performance_tips() -> str:
    return res.query_performance_tips()


@mcp.resource("db://schema-design-tips")
def res_schema_design_tips() -> str:
    return res.schema_design_tips()


@mcp.resource("db://transaction-tips")
def res_transaction_tips() -> str:
    return res.transaction_tips()


@mcp.resource("db://data-types")
def res_data_types() -> str:
    return res.data_types_reference()


@mcp.resource("db://examples/select")
def res_example_select() -> str:
    return res.example_query_select()


@mcp.resource("db://examples/join")
def res_example_join() -> str:
    return res.example_query_join()


@mcp.resource("db://examples/aggregate")
def res_example_aggregate() -> str:
    return res.example_query_aggregate()


@mcp.resource("db://connection-string-guide")
def res_connection_guide() -> str:
    return res.connection_string_guide()


@mcp.resource("db://error-codes")
def res_error_codes() -> str:
    return res.error_codes_reference()


# ---------------------------------------------------------------------------
# Resources dinámicos
# ---------------------------------------------------------------------------


@mcp.resource("db://info")
def res_db_info() -> str:
    return res.database_info(engine)


@mcp.resource("db://tables")
def res_tables() -> str:
    return res.tables_list(engine)


@mcp.resource("db://table/{table}/schema")
def res_table_schema(table: str) -> str:
    return res.table_schema(engine, table)


@mcp.resource("db://table/{table}/columns")
def res_table_columns(table: str) -> str:
    return res.table_columns(engine, table)


@mcp.resource("db://table/{table}/primary-key")
def res_table_pk(table: str) -> str:
    return res.table_primary_key(engine, table)


@mcp.resource("db://table/{table}/foreign-keys")
def res_table_fk(table: str) -> str:
    return res.table_foreign_keys(engine, table)


@mcp.resource("db://table/{table}/indexes")
def res_table_idx(table: str) -> str:
    return res.table_indexes(engine, table)


@mcp.resource("db://table/{table}/row-count")
def res_table_row_count(table: str) -> str:
    return res.table_row_count(engine, table)


@mcp.resource("db://table/{table}/sample")
def res_table_sample(table: str) -> str:
    return res.table_sample(engine, table)


@mcp.resource("db://table/{table}/column/{column}/distinct")
def res_table_distinct(table: str, column: str) -> str:
    return res.table_distinct_values(engine, table, column)


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
