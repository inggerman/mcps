"""Tests para mcp-event-driven."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from mcp_event_driven.tools.event_tools import (
    analyze_choreography,
    generate_event_payload,
    parse_event_schema,
)
from mcp_shared.errors import FileNotFoundError, ParseError


@pytest.fixture
def schemas_dir(tmp_path: Path) -> Path:
    s_dir = tmp_path / "schemas"
    s_dir.mkdir()

    # Schema 1: JSON Schema
    s1 = {
        "title": "UserCreated",
        "type": "object",
        "properties": {"user_id": {"type": "string"}, "created_at": {"type": "string"}},
    }
    (s_dir / "user_created.json").write_text(json.dumps(s1), encoding="utf-8")

    # Schema 2: AsyncAPI
    s2 = {"asyncapi": "2.0.0", "info": {"title": "PaymentService"}, "channels": {}}
    (s_dir / "payment.json").write_text(json.dumps(s2), encoding="utf-8")

    # Schema 3: Invalid
    (s_dir / "invalid.json").write_text("not a json", encoding="utf-8")

    return s_dir


def test_parse_event_schema_json_schema(schemas_dir: Path) -> None:
    res = parse_event_schema(schemas_dir / "user_created.json")
    assert res["type"] == "JSON_SCHEMA"
    assert res["title"] == "UserCreated"
    assert "user_id" in res["properties"]


def test_parse_event_schema_asyncapi(schemas_dir: Path) -> None:
    res = parse_event_schema(schemas_dir / "payment.json")
    assert res["type"] == "ASYNC_API"
    assert res["title"] == "PaymentService"


def test_parse_event_schema_invalid(schemas_dir: Path) -> None:
    with pytest.raises(ParseError):
        parse_event_schema(schemas_dir / "invalid.json")


def test_parse_event_schema_not_found(schemas_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        parse_event_schema(schemas_dir / "missing.json")


def test_analyze_choreography(schemas_dir: Path) -> None:
    res = analyze_choreography(schemas_dir)
    assert res["events_found"] == 2  # Ignora el inválido


def test_generate_event_payload() -> None:
    payload = generate_event_payload(["user_id", "created_at", "total_amount", "description"])
    assert payload["user_id"] == "evt_123456"
    assert payload["created_at"] == "2024-01-01T00:00:00Z"
    assert payload["total_amount"] == 99.99
    assert payload["description"] == "sample_data"
