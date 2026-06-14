from __future__ import annotations

import pytest
from mcp_database.tools.database_tools import (
    create_database_engine,
    describe_table,
    execute_query,
    list_tables,
)
from mcp_shared.errors import ValidationError
from sqlalchemy import text


@pytest.fixture
def engine():
    database = create_database_engine("sqlite:///:memory:")
    with database.begin() as connection:
        connection.execute(text("create table users (id integer primary key, name text)"))
        connection.execute(text("insert into users(name) values ('Ada'), ('Linus')"))
    yield database
    database.dispose()


def test_inspection_and_query(engine) -> None:
    assert list_tables(engine) == [{"name": "users", "type": "table"}]
    assert describe_table(engine, "users")["primary_key"]["constrained_columns"] == ["id"]
    result = execute_query(engine, "select * from users order by id", max_rows=1)
    assert result["row_count"] == 1
    assert result["truncated"] is True


def test_read_only_blocks_mutation(engine) -> None:
    with pytest.raises(ValidationError, match="READ_ONLY"):
        execute_query(engine, "delete from users", read_only=True)
