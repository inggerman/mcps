"""Safe database inspection and query tools."""

from __future__ import annotations

import re
from typing import Any

from mcp_shared.errors import ValidationError
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

_MUTATING_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|replace|merge|grant|revoke|call)\b",
    re.IGNORECASE,
)


def create_database_engine(database_url: str, timeout_seconds: int = 30) -> Engine:
    connect_args: dict[str, Any] = {}
    if database_url.startswith("sqlite"):
        connect_args["timeout"] = timeout_seconds
    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


def _validate_query(query: str, read_only: bool) -> str:
    normalized = query.strip().rstrip(";").strip()
    if not normalized:
        raise ValidationError(field="query", message="La consulta no puede estar vacía.")
    if ";" in normalized:
        raise ValidationError(field="query", message="Solo se permite una sentencia SQL.")
    if read_only and _MUTATING_SQL.search(normalized):
        raise ValidationError(
            field="query",
            message="La consulta modifica datos y DATABASE_READ_ONLY está activo.",
        )
    return normalized


def get_database_info(engine: Engine) -> dict[str, Any]:
    inspector = inspect(engine)
    return {
        "dialect": engine.dialect.name,
        "driver": engine.dialect.driver,
        "schemas": inspector.get_schema_names(),
    }


def list_tables(engine: Engine, schema: str | None = None) -> list[dict[str, Any]]:
    inspector = inspect(engine)
    tables = [{"name": name, "type": "table"} for name in inspector.get_table_names(schema=schema)]
    views = [{"name": name, "type": "view"} for name in inspector.get_view_names(schema=schema)]
    return sorted([*tables, *views], key=lambda item: (item["type"], item["name"]))


def describe_table(
    engine: Engine,
    table: str,
    schema: str | None = None,
) -> dict[str, Any]:
    if not table.strip():
        raise ValidationError(field="table", message="La tabla no puede estar vacía.")
    inspector = inspect(engine)
    if table not in inspector.get_table_names(
        schema=schema
    ) and table not in inspector.get_view_names(schema=schema):
        raise ValidationError(field="table", message=f"La tabla o vista '{table}' no existe.")
    return {
        "name": table,
        "columns": inspector.get_columns(table, schema=schema),
        "primary_key": inspector.get_pk_constraint(table, schema=schema),
        "foreign_keys": inspector.get_foreign_keys(table, schema=schema),
        "indexes": inspector.get_indexes(table, schema=schema),
    }


def execute_query(
    engine: Engine,
    query: str,
    parameters: dict[str, Any] | None = None,
    max_rows: int = 500,
    read_only: bool = True,
) -> dict[str, Any]:
    statement = _validate_query(query, read_only)
    with engine.begin() as connection:
        result = connection.execute(text(statement), parameters or {})
        if not result.returns_rows:
            return {"columns": [], "rows": [], "row_count": result.rowcount, "truncated": False}
        rows = result.mappings().fetchmany(max_rows + 1)
    truncated = len(rows) > max_rows
    selected = rows[:max_rows]
    return {
        "columns": list(result.keys()),
        "rows": [dict(row) for row in selected],
        "row_count": len(selected),
        "truncated": truncated,
    }
