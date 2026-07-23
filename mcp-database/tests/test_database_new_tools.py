from __future__ import annotations

import json

import pytest
from mcp_database.tools.database_tools import (
    create_database_engine,
    execute_query,
    export_to_csv,
    export_to_json,
    get_schemas,
    get_table_stats,
    get_views,
    query_to_markdown,
    table_distinct_values,
    table_row_count,
    table_sample,
)
from mcp_shared.errors import ValidationError
from sqlalchemy import text


@pytest.fixture
def engine():
    db = create_database_engine("sqlite:///:memory:")
    with db.begin() as conn:
        conn.execute(text("create table users (id integer primary key, name text, active integer)"))
        conn.execute(text("insert into users(name, active) values ('Ada', 1), ('Linus', 1), ('Grace', 0)"))
        conn.execute(text("create view active_users as select * from users where active = 1"))
    yield db
    db.dispose()


def test_table_row_count(engine) -> None:
    result = table_row_count(engine, "users")
    assert result["row_count"] == 3


def test_table_row_count_missing(engine) -> None:
    with pytest.raises(ValidationError, match="no existe"):
        table_row_count(engine, "nonexistent")


def test_table_sample(engine) -> None:
    result = table_sample(engine, "users", n=2)
    assert result["row_count"] == 2
    assert "id" in result["columns"]


def test_table_distinct_values(engine) -> None:
    result = table_distinct_values(engine, "users", "active")
    assert set(result["values"]) == {0, 1}


def test_table_distinct_values_missing_column(engine) -> None:
    with pytest.raises(ValidationError, match="no existe"):
        table_distinct_values(engine, "users", "nonexistent")


def test_get_table_stats(engine) -> None:
    result = get_table_stats(engine, "users")
    assert result["row_count"] == 3
    assert result["column_count"] == 3
    assert "id" in result["columns"]


def test_export_to_csv(engine) -> None:
    csv_data = export_to_csv(engine, "users")
    assert "id,name,active" in csv_data
    assert "Ada" in csv_data


def test_export_to_json(engine) -> None:
    json_data = export_to_json(engine, "users")
    parsed = json.loads(json_data)
    assert len(parsed) == 3


def test_get_schemas(engine) -> None:
    schemas = get_schemas(engine)
    assert isinstance(schemas, list)
    assert len(schemas) > 0


def test_get_views(engine) -> None:
    views = get_views(engine)
    assert "active_users" in views


def test_query_to_markdown(engine) -> None:
    md = query_to_markdown(engine, "SELECT * FROM users LIMIT 2")
    assert "| id" in md
    assert "---" in md
    assert "Ada" in md


def test_query_to_markdown_no_results(engine) -> None:
    md = query_to_markdown(engine, "SELECT * FROM users WHERE id > 100")
    assert "Sin resultados" in md
