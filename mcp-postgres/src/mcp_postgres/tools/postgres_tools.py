"""Tools de PostgreSQL: list databases/tables, describe, execute query (read-only by default)."""

from __future__ import annotations

from typing import Any

import psycopg

from mcp_postgres.config import settings
from mcp_shared.errors import McpError, ValidationError

_WRITE_KEYWORDS = {"insert", "update", "delete", "drop", "create", "alter", "truncate", "grant", "revoke"}


def _check_read_only(sql: str) -> None:
    if settings.allow_write:
        return
    stripped = sql.strip().lower()
    first_word = stripped.split()[0] if stripped.split() else ""
    if first_word in _WRITE_KEYWORDS:
        raise ValidationError(
            field="sql",
            message="Query de escritura no permitida. Establece POSTGRES_ALLOW_WRITE=true.",
            value=first_word,
        )


def list_databases() -> list[dict[str, Any]]:
    """Lista las bases de datos de PostgreSQL."""
    try:
        with psycopg.connect(settings.connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT datname, pg_encoding_to_char(encoding), "
                    "pg_size_pretty(pg_database_size(datname)) "
                    "FROM pg_database WHERE datistemplate = false ORDER BY datname"
                )
                rows = cur.fetchall()
                return [
                    {"name": r[0], "encoding": r[1], "size": r[2]}
                    for r in rows
                ]
    except psycopg.Error as exc:
        raise McpError(f"PostgreSQL error: {exc}") from exc


def list_tables(database: str | None = None) -> list[dict[str, Any]]:
    """Lista las tablas de una base de datos."""
    try:
        conn_str = settings.connection_string
        if database:
            conn_str = conn_str.replace(f"dbname={settings.database}", f"dbname={database}")
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT table_name, table_schema, "
                    "pg_size_pretty(pg_total_relation_size(table_schema||'.'||table_name)) "
                    "FROM information_schema.tables "
                    "WHERE table_schema NOT IN ('pg_catalog', 'information_schema') "
                    "ORDER BY table_schema, table_name"
                )
                rows = cur.fetchall()
                return [
                    {"name": r[0], "schema": r[1], "size": r[2]}
                    for r in rows
                ]
    except psycopg.Error as exc:
        raise McpError(f"PostgreSQL error: {exc}") from exc


def describe_table(table_name: str, database: str | None = None) -> list[dict[str, Any]]:
    """Describe la estructura de una tabla."""
    try:
        conn_str = settings.connection_string
        if database:
            conn_str = conn_str.replace(f"dbname={settings.database}", f"dbname={database}")
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                schema, table = table_name.split(".", 1) if "." in table_name else ("public", table_name)
                cur.execute(
                    "SELECT column_name, data_type, is_nullable, column_default, "
                    "character_maximum_length "
                    "FROM information_schema.columns "
                    "WHERE table_schema = %s AND table_name = %s "
                    "ORDER BY ordinal_position",
                    (schema, table),
                )
                rows = cur.fetchall()
                if not rows:
                    raise McpError(f"Tabla no encontrada: {table_name}")
                return [
                    {
                        "column": r[0],
                        "type": r[1],
                        "nullable": r[2] == "YES",
                        "default": r[3],
                        "max_length": r[4],
                    }
                    for r in rows
                ]
    except psycopg.Error as exc:
        raise McpError(f"PostgreSQL error: {exc}") from exc


def execute_query(sql: str, database: str | None = None) -> dict[str, Any]:
    """Ejecuta una query SQL (read-only por defecto)."""
    _check_read_only(sql)
    try:
        conn_str = settings.connection_string
        if database:
            conn_str = conn_str.replace(f"dbname={settings.database}", f"dbname={database}")
        with psycopg.connect(conn_str) as conn:
            conn.set_session(timeout=settings.query_timeout)
            with conn.cursor() as cur:
                cur.execute(sql)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = cur.fetchmany(settings.max_rows)
                return {
                    "columns": columns,
                    "rows": [list(r) for r in rows],
                    "row_count": len(rows),
                    "truncated": cur.rowcount > settings.max_rows if cur.rowcount > 0 else False,
                }
    except psycopg.Error as exc:
        raise McpError(f"PostgreSQL error: {exc}") from exc
