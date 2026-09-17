"""execute_query: runs at all under psycopg 3, and read-only really is read-only.

Two defects this covers:

- `conn.set_session(...)` is psycopg2 API. Under psycopg 3 it raised
  AttributeError, so every query failed with "Error interno del servidor" and
  PAIOS agents that depend on this MCP could not read a single row.
- Read-only mode only looked at the first word of the statement. A writing CTE
  (`WITH d AS (DELETE ... RETURNING *) SELECT ...`) starts with WITH and went
  through. The transaction is now read-only on the server.

The tests against a real server run only when ``MCP_POSTGRES_TEST_DSN`` points
at a disposable PostgreSQL: they create and drop a table.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

import psycopg
import pytest
from mcp_postgres.config import settings
from mcp_postgres.tools import postgres_tools
from mcp_shared.errors import McpError, ValidationError


class _Cursor:
    def __init__(self, log):
        self.log = log
        self.description = [("one",)]
        self.rowcount = 1

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.log.append((sql, params))

    def fetchmany(self, n):
        return [(1,)]

    def fetchall(self):
        return []


class _Connection:
    def __init__(self):
        self.read_only = None
        self.log: list = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def cursor(self):
        return _Cursor(self.log)


@pytest.fixture
def fake_connection(monkeypatch):
    conn = _Connection()
    monkeypatch.setattr(postgres_tools.psycopg, "connect", lambda *a, **k: conn)
    return conn


def test_query_runs_in_a_read_only_transaction_with_a_timeout(fake_connection, monkeypatch):
    monkeypatch.setattr(settings, "allow_write", False)
    result = postgres_tools.execute_query("SELECT 1")
    assert result["rows"] == [[1]]
    assert fake_connection.read_only is True
    timeout_sql, timeout_params = fake_connection.log[0]
    assert "statement_timeout" in timeout_sql
    assert timeout_params == (str(int(settings.query_timeout * 1000)),)
    assert fake_connection.log[1] == ("SELECT 1", None)


def test_write_mode_does_not_force_read_only(fake_connection, monkeypatch):
    monkeypatch.setattr(settings, "allow_write", True)
    postgres_tools.execute_query("SELECT 1")
    assert fake_connection.read_only is None


@pytest.mark.parametrize(
    "sql",
    [
        "DROP DATABASE visionhub;",
        "COPY (SELECT 1) TO PROGRAM 'id'",
        "do $$ begin perform 1; end $$",
        "CALL some_procedure()",
    ],
)
def test_obvious_writes_are_rejected_before_connecting(sql, monkeypatch):
    monkeypatch.setattr(settings, "allow_write", False)
    monkeypatch.setattr(
        postgres_tools.psycopg, "connect",
        lambda *a, **k: pytest.fail("must not connect for a rejected statement"),
    )
    with pytest.raises(ValidationError):
        postgres_tools.execute_query(sql)


DSN = os.environ.get("MCP_POSTGRES_TEST_DSN")


@pytest.fixture
def real_server(monkeypatch):
    if not DSN:
        pytest.skip("MCP_POSTGRES_TEST_DSN not set: no disposable PostgreSQL")
    url = urlparse(DSN)
    monkeypatch.setattr(settings, "host", url.hostname)
    monkeypatch.setattr(settings, "port", url.port or 5432)
    monkeypatch.setattr(settings, "user", url.username or "postgres")
    monkeypatch.setattr(settings, "password", url.password or "")
    monkeypatch.setattr(settings, "database", (url.path or "/postgres").lstrip("/"))
    monkeypatch.setattr(settings, "allow_write", False)
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS mcp_readonly_probe")
        conn.execute("CREATE TABLE mcp_readonly_probe (id int)")
        conn.execute("INSERT INTO mcp_readonly_probe VALUES (1)")
    yield
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS mcp_readonly_probe")


def _rows_left() -> int:
    with psycopg.connect(DSN) as conn:
        return conn.execute("SELECT count(*) FROM mcp_readonly_probe").fetchone()[0]


def test_real_server_answers_a_select(real_server):
    result = postgres_tools.execute_query("SELECT count(*) FROM mcp_readonly_probe")
    assert result["rows"] == [[1]]


def test_real_server_refuses_a_writing_cte(real_server):
    # Starts with WITH, so the keyword check lets it through; the read-only
    # transaction is what has to stop it.
    with pytest.raises(McpError):
        postgres_tools.execute_query(
            "WITH d AS (DELETE FROM mcp_readonly_probe RETURNING *) SELECT count(*) FROM d"
        )
    assert _rows_left() == 1


def test_listing_tools_also_run_read_only(fake_connection, monkeypatch):
    # They used to open an unrestricted connection of their own.
    monkeypatch.setattr(settings, "allow_write", False)
    postgres_tools.list_databases()
    assert fake_connection.read_only is True
    assert "statement_timeout" in fake_connection.log[0][0]
