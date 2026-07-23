"""Tools públicas de mcp-structured-output."""

from __future__ import annotations

from mcp_structured_output.tools.invoke_tools import invoke_structured
from mcp_structured_output.tools.schema_tools import (
    check_schema_compatibility,
    count_schema_fields,
    extract_schema_fields,
    flatten_schema,
    generate_schema,
    list_schema_keywords,
    merge_schemas,
    sanitize_schema,
    schema_complexity,
    schema_diff,
    schema_to_json_example,
    schema_to_markdown,
    schema_to_openapi,
    schema_to_python,
    schema_to_table,
    schema_to_typescript,
    simplify_schema,
    validate_json_against_schema,
    validate_schema,
)

__all__ = [
    "check_schema_compatibility",
    "count_schema_fields",
    "extract_schema_fields",
    "flatten_schema",
    "generate_schema",
    "invoke_structured",
    "list_schema_keywords",
    "merge_schemas",
    "sanitize_schema",
    "schema_complexity",
    "schema_diff",
    "schema_to_json_example",
    "schema_to_markdown",
    "schema_to_openapi",
    "schema_to_python",
    "schema_to_table",
    "schema_to_typescript",
    "simplify_schema",
    "validate_json_against_schema",
    "validate_schema",
]
