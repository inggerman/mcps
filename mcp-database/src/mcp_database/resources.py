"""Resources de solo lectura para mcp-database.

Expone metadatos, esquemas, consejos y vistas de la base de datos
como URIs accesibles para el modelo a través de `@mcp.resource`.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from mcp_database.tools.database_tools import (
    describe_table,
    execute_query,
    get_database_info,
    list_tables,
)


# ---------------------------------------------------------------------------
# Resources estáticos
# ---------------------------------------------------------------------------


def supported_sql_dialects() -> str:
    """Dialectos SQL soportados por SQLAlchemy."""
    return json.dumps(
        {
            "dialects": [
                {"name": "sqlite", "driver": "pysqlite", "url_prefix": "sqlite:///"},
                {"name": "postgresql", "driver": "psycopg2", "url_prefix": "postgresql://"},
                {"name": "mysql", "driver": "pymysql", "url_prefix": "mysql://"},
                {"name": "oracle", "driver": "cx_oracle", "url_prefix": "oracle://"},
                {"name": "mssql", "driver": "pyodbc", "url_prefix": "mssql+pyodbc://"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def sql_safety_tips() -> str:
    """Consejos de seguridad SQL."""
    return (
        "# Seguridad SQL\n\n"
        "- DATABASE_READ_ONLY=true por defecto (solo SELECT).\n"
        "- Solo se permite una sentencia SQL por consulta.\n"
        "- Se bloquean INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE.\n"
        "- Use parámetros nombrados (:param) para evitar SQL injection.\n"
        "- DATABASE_MAX_ROWS limita el número de filas retornadas (default 500).\n"
        "- DATABASE_STATEMENT_TIMEOUT_SECONDS limita el tiempo de ejecución."
    )


def sql_cheatsheet() -> str:
    """Cheatsheet de SQL para consultas comunes."""
    return (
        "# SQL cheatsheet\n\n"
        "- SELECT: `SELECT col1, col2 FROM table WHERE condition`\n"
        "- JOIN: `SELECT a.*, b.* FROM a JOIN b ON a.id = b.a_id`\n"
        "- GROUP BY: `SELECT category, COUNT(*) FROM table GROUP BY category`\n"
        "- ORDER BY: `SELECT * FROM table ORDER BY col DESC`\n"
        "- LIMIT: `SELECT * FROM table LIMIT 10` (SQLite/PostgreSQL)\n"
        "- DISTINCT: `SELECT DISTINCT col FROM table`\n"
        "- AGGREGATE: `SELECT COUNT(*), AVG(col), SUM(col), MIN(col), MAX(col) FROM table`\n"
        "- SUBQUERY: `SELECT * FROM table WHERE id IN (SELECT id FROM other WHERE x > 0)`"
    )


def query_performance_tips() -> str:
    """Consejos para optimizar consultas SQL."""
    return (
        "# Optimización de queries\n\n"
        "- Usa índices en columnas de filtrado frecuente.\n"
        "- Evita SELECT * cuando solo necesitas algunas columnas.\n"
        "- Usa LIMIT para no traer conjuntos enormes.\n"
        "- EXPLAIN / EXPLAIN QUERY PLAN muestra el plan de ejecución.\n"
        "- Las JOINs sobre columnas indexadas son más rápidas.\n"
        "- Evita subconsultas correlacionadas cuando es posible."
    )


def schema_design_tips() -> str:
    """Consejos de diseño de esquema."""
    return (
        "# Diseño de esquema\n\n"
        "- Usa claves primarias en todas las tablas.\n"
        "- Normaliza hasta 3NF; desnormaliza solo con justificación.\n"
        "- Define foreign keys para integridad referencial.\n"
        "- Usa tipos de datos específicos (INTEGER, VARCHAR(n), TIMESTAMP).\n"
        "- Considera índices en columnas de JOIN y WHERE.\n"
        "- Nombra tablas en plural (users, orders) y columnas en singular."
    )


def transaction_tips() -> str:
    """Consejos sobre transacciones."""
    return (
        "# Transacciones\n\n"
        "- Una transacción agrupa varias operaciones en una unidad atómica.\n"
        "- COMMIT confirma los cambios; ROLLBACK los revierte.\n"
        "- Mantén las transacciones lo más cortas posible.\n"
        "- Evita transacciones anidadas en SQLite (limitado soporte).\n"
        "- El modo read-only del MCP no inicia transacciones de escritura."
    )


def data_types_reference() -> str:
    """Referencia de tipos de datos SQL comunes."""
    return json.dumps(
        {
            "types": [
                {"name": "INTEGER", "description": "Entero de 4 bytes"},
                {"name": "BIGINT", "description": "Entero de 8 bytes"},
                {"name": "REAL", "description": "Float de punto flotante"},
                {"name": "TEXT", "description": "Cadena de texto variable"},
                {"name": "VARCHAR(n)", "description": "Cadena de longitud máxima n"},
                {"name": "BLOB", "description": "Datos binarios"},
                {"name": "TIMESTAMP", "description": "Fecha y hora"},
                {"name": "DATE", "description": "Solo fecha"},
                {"name": "BOOLEAN", "description": "Verdadero/falso"},
                {"name": "JSON", "description": "Documento JSON (PostgreSQL/SQLite)"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def example_query_select() -> str:
    """Ejemplo de consulta SELECT."""
    return "SELECT id, name, created_at FROM users WHERE active = 1 ORDER BY created_at DESC LIMIT 10;"


def example_query_join() -> str:
    """Ejemplo de consulta JOIN."""
    return (
        "SELECT u.name, COUNT(o.id) as order_count "
        "FROM users u "
        "LEFT JOIN orders o ON o.user_id = u.id "
        "GROUP BY u.name "
        "ORDER BY order_count DESC;"
    )


def example_query_aggregate() -> str:
    """Ejemplo de consulta con agregación."""
    return (
        "SELECT category, COUNT(*) as count, AVG(price) as avg_price "
        "FROM products "
        "GROUP BY category "
        "HAVING COUNT(*) > 5 "
        "ORDER BY avg_price DESC;"
    )


def connection_string_guide() -> str:
    """Guía de connection strings."""
    return (
        "# Connection strings\n\n"
        "- SQLite: `sqlite:///path/to/database.db`\n"
        "- PostgreSQL: `postgresql://user:pass@host:5432/dbname`\n"
        "- MySQL: `mysql://user:pass@host:3306/dbname`\n"
        "- En memoria: `sqlite:///:memory:`\n"
        "- La variable de entorno DATABASE_URL define la conexión.\n"
        "- Cambiar DATABASE_URL requiere reiniciar el servidor."
    )


def error_codes_reference() -> str:
    """Referencia de códigos de error comunes."""
    return json.dumps(
        {
            "errors": [
                {"code": "23505", "description": "Violación de unicidad (PostgreSQL)"},
                {"code": "23503", "description": "Violación de foreign key (PostgreSQL)"},
                {"code": "23502", "description": "Violación de NOT NULL (PostgreSQL)"},
                {"code": "42P01", "description": "Tabla no definida (PostgreSQL)"},
                {"code": "42703", "description": "Columna no existe (PostgreSQL)"},
                {"code": "SQLITE_CONSTRAINT", "description": "Violación de constraint (SQLite)"},
                {"code": "SQLITE_ERROR", "description": "Error genérico SQL (SQLite)"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# Resources dinámicos
# ---------------------------------------------------------------------------


def database_info(engine: Engine) -> str:
    """Información de la base de datos (dialecto, driver, schemas)."""
    return json.dumps(get_database_info(engine), indent=2, ensure_ascii=False, default=str)


def tables_list(engine: Engine, schema: str | None = None) -> str:
    """Lista de tablas y vistas."""
    return json.dumps(
        {"tables": list_tables(engine, schema=schema)},
        indent=2,
        ensure_ascii=False,
    )


def table_schema(engine: Engine, table: str, schema: str | None = None) -> str:
    """Esquema detallado de una tabla (columnas, PK, FK, índices)."""
    return json.dumps(
        describe_table(engine, table, schema=schema),
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def table_columns(engine: Engine, table: str, schema: str | None = None) -> str:
    """Solo las columnas de una tabla."""
    info = describe_table(engine, table, schema=schema)
    return json.dumps(
        {"table": table, "columns": info["columns"]},
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def table_primary_key(engine: Engine, table: str, schema: str | None = None) -> str:
    """Clave primaria de una tabla."""
    info = describe_table(engine, table, schema=schema)
    return json.dumps(
        {"table": table, "primary_key": info["primary_key"]},
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def table_foreign_keys(engine: Engine, table: str, schema: str | None = None) -> str:
    """Claves foráneas de una tabla."""
    info = describe_table(engine, table, schema=schema)
    return json.dumps(
        {"table": table, "foreign_keys": info["foreign_keys"]},
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def table_indexes(engine: Engine, table: str, schema: str | None = None) -> str:
    """Índices de una tabla."""
    info = describe_table(engine, table, schema=schema)
    return json.dumps(
        {"table": table, "indexes": info["indexes"]},
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def table_row_count(engine: Engine, table: str, schema: str | None = None) -> str:
    """Número aproximado de filas en una tabla."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names(schema=schema):
        from mcp_shared.errors import ValidationError
        raise ValidationError(field="table", message=f"La tabla '{table}' no existe.")
    result = execute_query(
        engine, f"SELECT COUNT(*) AS count FROM {table}", max_rows=1, read_only=True,
    )
    count = result["rows"][0]["count"] if result["rows"] else 0
    return json.dumps(
        {"table": table, "row_count": count},
        indent=2,
        ensure_ascii=False,
    )


def table_sample(engine: Engine, table: str, n: int = 10, schema: str | None = None) -> str:
    """Muestra de n filas de una tabla."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names(schema=schema):
        from mcp_shared.errors import ValidationError
        raise ValidationError(field="table", message=f"La tabla '{table}' no existe.")
    result = execute_query(
        engine, f"SELECT * FROM {table} LIMIT {n}", max_rows=n, read_only=True,
    )
    return json.dumps(
        {"table": table, "columns": result["columns"], "rows": result["rows"], "row_count": result["row_count"]},
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def table_distinct_values(
    engine: Engine, table: str, column: str, n: int = 50, schema: str | None = None,
) -> str:
    """Valores distintos de una columna."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names(schema=schema):
        from mcp_shared.errors import ValidationError
        raise ValidationError(field="table", message=f"La tabla '{table}' no existe.")
    result = execute_query(
        engine,
        f"SELECT DISTINCT {column} FROM {table} LIMIT {n}",
        max_rows=n,
        read_only=True,
    )
    return json.dumps(
        {"table": table, "column": column, "values": [r[column] for r in result["rows"]]},
        indent=2,
        ensure_ascii=False,
        default=str,
    )
