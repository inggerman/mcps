"""Tests unitarios para schema_tools: validate_schema, generate_schema, sanitize_schema."""

from __future__ import annotations

import pytest
from mcp_shared.errors import ValidationError
from mcp_structured_output.tools.schema_tools import (
    generate_schema,
    sanitize_schema,
    validate_schema,
)

# ---------------------------------------------------------------------------
# validate_schema
# ---------------------------------------------------------------------------


class TestValidateSchema:
    def test_valid_simple_schema(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name", "age"],
            "additionalProperties": False,
        }
        result = validate_schema(schema)
        assert result["valid"] is True
        assert result["issues"] == []

    def test_invalid_not_dict(self) -> None:
        with pytest.raises(ValidationError):
            validate_schema("not a dict")  # type: ignore[arg-type]

    def test_detects_numeric_constraints(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number", "minimum": 0, "maximum": 100},
            },
            "additionalProperties": False,
        }
        result = validate_schema(schema)
        assert result["valid"] is False
        paths = [i["path"] for i in result["issues"]]
        assert any("minimum" in p for p in paths)
        assert any("maximum" in p for p in paths)

    def test_detects_string_constraints(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
            },
            "additionalProperties": False,
        }
        result = validate_schema(schema)
        assert result["valid"] is False
        paths = [i["path"] for i in result["issues"]]
        assert any("minLength" in p for p in paths)
        assert any("maxLength" in p for p in paths)

    def test_detects_additional_properties_true(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "additionalProperties": True,
        }
        result = validate_schema(schema)
        assert result["valid"] is False
        assert any("additionalProperties" in i["path"] for i in result["issues"])

    def test_detects_external_ref(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "item": {"$ref": "https://example.com/schema.json"},
            },
            "additionalProperties": False,
        }
        result = validate_schema(schema)
        assert result["valid"] is False
        assert any("$ref" in i["path"] for i in result["issues"])

    def test_internal_ref_is_allowed(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "address": {"$ref": "#/$defs/Address"},
            },
            "required": ["address"],
            "additionalProperties": False,
            "$defs": {
                "Address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                    },
                    "required": ["street", "city"],
                    "additionalProperties": False,
                }
            },
        }
        result = validate_schema(schema)
        errors = [i for i in result["issues"] if i["severity"] == "error"]
        assert errors == []

    def test_detects_invalid_min_items(self) -> None:
        schema = {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 5,
        }
        result = validate_schema(schema)
        assert result["valid"] is False
        assert any("minItems" in i["path"] for i in result["issues"])

    def test_valid_min_items_zero(self) -> None:
        schema = {"type": "array", "items": {"type": "string"}, "minItems": 0}
        result = validate_schema(schema)
        errors = [i for i in result["issues"] if i["severity"] == "error"]
        assert errors == []

    def test_detects_recursive_schema(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "children": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/Node"},
                }
            },
            "additionalProperties": False,
            "$defs": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                        "children": {
                            "type": "array",
                            "items": {"$ref": "#/$defs/Node"},
                        },
                    },
                    "additionalProperties": False,
                }
            },
        }
        result = validate_schema(schema)
        assert result["valid"] is False
        assert any("Node" in i["path"] for i in result["issues"])

    def test_warning_missing_additional_properties(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        result = validate_schema(schema)
        warnings = [i for i in result["issues"] if i["severity"] == "warning"]
        assert any("additionalProperties" in i["message"] for i in warnings)

    def test_enum_complex_values_detected(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "status": {"enum": ["active", {"key": "val"}, None, True]},
            },
            "additionalProperties": False,
        }
        result = validate_schema(schema)
        assert result["valid"] is False
        assert any("enum" in i["path"] for i in result["issues"])


# ---------------------------------------------------------------------------
# generate_schema
# ---------------------------------------------------------------------------


class TestGenerateSchema:
    def test_simple_flat_object(self) -> None:
        example = {"name": "Alice", "age": 30, "score": 9.5, "active": True}
        result = generate_schema(example)
        schema = result["schema"]
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == {"name", "age", "score", "active"}
        assert schema["properties"]["name"] == {"type": "string"}
        assert schema["properties"]["age"] == {"type": "integer"}
        assert schema["properties"]["score"] == {"type": "number"}
        assert schema["properties"]["active"] == {"type": "boolean"}
        assert result["field_count"] == 4

    def test_nested_object(self) -> None:
        example = {"user": {"id": 1, "email": "a@b.com"}}
        result = generate_schema(example)
        schema = result["schema"]
        user_schema = schema["properties"]["user"]
        assert user_schema["type"] == "object"
        assert user_schema["additionalProperties"] is False
        assert "id" in user_schema["required"]

    def test_array_field(self) -> None:
        example = {"tags": ["python", "aws"]}
        result = generate_schema(example)
        tags = result["schema"]["properties"]["tags"]
        assert tags["type"] == "array"
        assert tags["items"] == {"type": "string"}

    def test_null_value_generates_anyof(self) -> None:
        example = {"optional_field": None}
        result = generate_schema(example)
        field = result["schema"]["properties"]["optional_field"]
        assert "anyOf" in field
        types = {s.get("type") for s in field["anyOf"]}
        assert "null" in types
        assert result["warnings"]

    def test_empty_array_generates_warning(self) -> None:
        example = {"items": []}
        result = generate_schema(example)
        assert result["warnings"]
        items_schema = result["schema"]["properties"]["items"]
        assert items_schema["items"] == {"type": "string"}

    def test_not_strict_omits_required_and_additional(self) -> None:
        example = {"name": "test"}
        result = generate_schema(example, strict=False)
        schema = result["schema"]
        assert "required" not in schema
        assert "additionalProperties" not in schema

    def test_invalid_example_raises(self) -> None:
        with pytest.raises(ValidationError):
            generate_schema("not a dict")  # type: ignore[arg-type]

    def test_name_and_description(self) -> None:
        result = generate_schema({"x": 1}, name="MySchema", description="Test schema")
        assert result["schema"]["title"] == "MySchema"
        assert result["schema"]["description"] == "Test schema"


# ---------------------------------------------------------------------------
# sanitize_schema
# ---------------------------------------------------------------------------


class TestSanitizeSchema:
    def test_already_valid_schema(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        }
        result = sanitize_schema(schema)
        assert result["was_valid"] is True
        assert result["changes"] == []
        assert result["sanitized"] == schema

    def test_removes_numeric_constraints(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "score": {"type": "number", "minimum": 0, "maximum": 100, "multipleOf": 0.5},
            },
            "additionalProperties": False,
        }
        result = sanitize_schema(schema)
        assert result["was_valid"] is False
        score = result["sanitized"]["properties"]["score"]
        assert "minimum" not in score
        assert "maximum" not in score
        assert "multipleOf" not in score
        actions = [c["action"] for c in result["changes"]]
        assert "removed" in actions

    def test_removes_string_constraints(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 2, "maxLength": 50},
            },
            "additionalProperties": False,
        }
        result = sanitize_schema(schema)
        name = result["sanitized"]["properties"]["name"]
        assert "minLength" not in name
        assert "maxLength" not in name

    def test_forces_additional_properties_false(self) -> None:
        schema = {
            "type": "object",
            "properties": {"x": {"type": "string"}},
            "additionalProperties": True,
        }
        result = sanitize_schema(schema)
        assert result["sanitized"]["additionalProperties"] is False
        assert any("additionalProperties" in c["path"] for c in result["changes"])

    def test_adds_missing_additional_properties(self) -> None:
        schema = {
            "type": "object",
            "properties": {"x": {"type": "string"}},
        }
        result = sanitize_schema(schema)
        assert result["sanitized"]["additionalProperties"] is False

    def test_fixes_min_items(self) -> None:
        schema = {"type": "array", "items": {"type": "string"}, "minItems": 5}
        result = sanitize_schema(schema)
        assert result["sanitized"]["minItems"] == 1
        assert any("minItems" in c["path"] for c in result["changes"])

    def test_replaces_external_ref(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "item": {"$ref": "https://external.com/schema.json"},
            },
            "additionalProperties": False,
        }
        result = sanitize_schema(schema)
        item = result["sanitized"]["properties"]["item"]
        assert item == {"type": "string"}
        assert any("$ref" in c["path"] for c in result["changes"])

    def test_removes_complex_enum_values(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "status": {"enum": ["active", {"nested": "obj"}, None, 42]},
            },
            "additionalProperties": False,
        }
        result = sanitize_schema(schema)
        enum_values = result["sanitized"]["properties"]["status"]["enum"]
        assert {"nested": "obj"} not in enum_values
        assert "active" in enum_values
        assert None in enum_values
        assert 42 in enum_values

    def test_does_not_modify_original(self) -> None:
        schema = {
            "type": "object",
            "properties": {"score": {"type": "number", "minimum": 0}},
        }
        original_score = dict(schema["properties"]["score"])
        sanitize_schema(schema)
        assert schema["properties"]["score"] == original_score

    def test_invalid_input_raises(self) -> None:
        with pytest.raises(ValidationError):
            sanitize_schema("not a dict")  # type: ignore[arg-type]
