"""Safe database inspection and query tools."""

from __future__ import annotations

import json
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


def table_row_count(engine: Engine, table: str, schema: str | None = None) -> dict[str, Any]:
    """Número de filas en una tabla."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names(schema=schema):
        raise ValidationError(field="table", message=f"La tabla '{table}' no existe.")
    with engine.begin() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) AS count FROM {table}"))
        count = result.scalar() or 0
    return {"table": table, "row_count": int(count)}


def table_sample(
    engine: Engine, table: str, n: int = 10, schema: str | None = None,
) -> dict[str, Any]:
    """Muestra de n filas de una tabla."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names(schema=schema):
        raise ValidationError(field="table", message=f"La tabla '{table}' no existe.")
    return execute_query(engine, f"SELECT * FROM {table} LIMIT {int(n)}", max_rows=int(n), read_only=True)


def table_distinct_values(
    engine: Engine, table: str, column: str, n: int = 50, schema: str | None = None,
) -> dict[str, Any]:
    """Valores distintos de una columna en una tabla."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names(schema=schema):
        raise ValidationError(field="table", message=f"La tabla '{table}' no existe.")
    cols = {c["name"] for c in inspector.get_columns(table, schema=schema)}
    if column not in cols:
        raise ValidationError(field="column", message=f"La columna '{column}' no existe en '{table}'.")
    result = execute_query(
        engine, f"SELECT DISTINCT {column} AS val FROM {table} LIMIT {int(n)}",
        max_rows=int(n), read_only=True,
    )
    return {
        "table": table,
        "column": column,
        "values": [r["val"] for r in result["rows"]],
        "count": len(result["rows"]),
    }


def get_table_stats(engine: Engine, table: str, schema: str | None = None) -> dict[str, Any]:
    """Estadísticas básicas de una tabla (row count, column count, size for SQLite)."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names(schema=schema):
        raise ValidationError(field="table", message=f"La tabla '{table}' no existe.")
    cols = inspector.get_columns(table, schema=schema)
    with engine.begin() as conn:
        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        row_count = count_result.scalar() or 0
    return {
        "table": table,
        "row_count": int(row_count),
        "column_count": len(cols),
        "columns": [c["name"] for c in cols],
    }


def explain_query(engine: Engine, query: str, read_only: bool = True) -> dict[str, Any]:
    """Ejecuta EXPLAIN QUERY PLAN (SQLite) o EXPLAIN (PostgreSQL)."""
    dialect = engine.dialect.name
    if dialect == "sqlite":
        explain_sql = f"EXPLAIN QUERY PLAN {query}"
    else:
        explain_sql = f"EXPLAIN {query}"
    return execute_query(engine, explain_sql, max_rows=100, read_only=False)


def export_to_csv(
    engine: Engine, table: str, max_rows: int = 1000, schema: str | None = None,
) -> str:
    """Exporta una tabla a formato CSV."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names(schema=schema):
        raise ValidationError(field="table", message=f"La tabla '{table}' no existe.")
    result = execute_query(engine, f"SELECT * FROM {table}", max_rows=max_rows, read_only=True)
    if not result["rows"]:
        return ""
    import csv
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=result["columns"])
    writer.writeheader()
    for row in result["rows"]:
        writer.writerow(row)
    return output.getvalue()


def export_to_json(
    engine: Engine, table: str, max_rows: int = 1000, schema: str | None = None,
) -> str:
    """Exporta una tabla a formato JSON."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names(schema=schema):
        raise ValidationError(field="table", message=f"La tabla '{table}' no existe.")
    result = execute_query(engine, f"SELECT * FROM {table}", max_rows=max_rows, read_only=True)
    return json.dumps(result["rows"], indent=2, ensure_ascii=False, default=str)


def get_schemas(engine: Engine) -> list[str]:
    """Lista los schemas de la base de datos."""
    inspector = inspect(engine)
    return inspector.get_schema_names()


def get_views(engine: Engine, schema: str | None = None) -> list[str]:
    """Lista las vistas de la base de datos."""
    inspector = inspect(engine)
    return inspector.get_view_names(schema=schema)


def query_to_markdown(
    engine: Engine, query: str, max_rows: int = 50, read_only: bool = True,
) -> str:
    """Ejecuta una consulta y retorna el resultado como tabla Markdown."""
    result = execute_query(engine, query, max_rows=max_rows, read_only=read_only)
    if not result["rows"]:
        return "*Sin resultados.*"
    headers = "| " + " | ".join(str(c) for c in result["columns"]) + " |"
    separator = "|" + "|".join(" --- " for _ in result["columns"]) + "|"
    rows = []
    for row in result["rows"]:
        cells = "| " + " | ".join(str(v) for v in row.values()) + " |"
        rows.append(cells)
    return "\n".join([headers, separator, *rows])
