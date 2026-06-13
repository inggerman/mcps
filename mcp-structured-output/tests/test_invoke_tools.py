"""Tests for provider-independent structured output validation."""

from __future__ import annotations

import pytest
from mcp_shared.errors import ParseError, ValidationError
from mcp_structured_output.tools.invoke_tools import _build_result

SCHEMA = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"],
    "additionalProperties": False,
}


def test_build_result_accepts_schema_compliant_json() -> None:
    result = _build_result(
        raw_text='{"name": "Ada"}',
        provider="test",
        model_id="test-model",
        input_tokens=2,
        output_tokens=3,
        schema=SCHEMA,
    )

    assert result["result"] == {"name": "Ada"}


def test_build_result_rejects_schema_violation() -> None:
    with pytest.raises(ParseError, match="no cumple el JSON Schema"):
        _build_result(
            raw_text='{"name": 42}',
            provider="test",
            model_id="test-model",
            input_tokens=0,
            output_tokens=0,
            schema=SCHEMA,
        )


def test_build_result_rejects_invalid_schema() -> None:
    with pytest.raises(ValidationError, match="JSON Schema no es válido"):
        _build_result(
            raw_text='{"name": "Ada"}',
            provider="test",
            model_id="test-model",
            input_tokens=0,
            output_tokens=0,
            schema={"type": "not-a-json-schema-type"},
        )
