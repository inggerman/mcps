from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_openapi.config import settings
from mcp_openapi.tools import (
    compare_specs,
    describe_operation,
    describe_schema,
    export_spec_summary,
    generate_client_code,
    generate_markdown_docs,
    get_response_codes,
    get_schemas,
    get_security_schemes,
    get_spec_info,
    get_tags,
    invoke_operation,
    list_endpoints,
    list_operations,
    list_operations_by_tag,
    load_spec,
    validate_spec,
)
from mcp_openapi import resources as res

setup_logging(
    log_level=settings.log_level, log_format=settings.log_format, server_name="mcp-openapi"
)
logger = get_logger(__name__)
mcp = FastMCP(
    name="mcp-openapi", instructions="Descubre e invoca operaciones OpenAPI con allowlist."
)


def _spec() -> dict[str, Any]:
    return load_spec(settings.spec, settings.allowed_root, settings.timeout_seconds)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="openapi_list_operations")
def tool_list() -> list[dict[str, Any]]:
    return _handle(list_operations, _spec())


@mcp.tool(name="openapi_describe_operation")
def tool_describe(operation_id: str) -> dict[str, Any]:
    return _handle(describe_operation, _spec(), operation_id)


@mcp.tool(name="openapi_invoke")
def tool_invoke(
    operation_id: str,
    path_parameters: dict[str, Any] | None = None,
    query_parameters: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json_body: Any = None,
) -> dict[str, Any]:
    return _handle(
        invoke_operation,
        _spec(),
        operation_id,
        settings.allow_invoke,
        settings.allowed_hosts,
        path_parameters,
        query_parameters,
        headers,
        json_body,
        settings.timeout_seconds,
    )


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(name="openapi_get_spec_info")
def tool_spec_info() -> dict[str, Any]:
    return _handle(get_spec_info, _spec())


@mcp.tool(name="openapi_get_schemas")
def tool_schemas() -> dict[str, Any]:
    return _handle(get_schemas, _spec())


@mcp.tool(name="openapi_describe_schema")
def tool_describe_schema(schema_name: str) -> dict[str, Any]:
    return _handle(describe_schema, _spec(), schema_name)


@mcp.tool(name="openapi_get_security_schemes")
def tool_security_schemes() -> dict[str, Any]:
    return _handle(get_security_schemes, _spec())


@mcp.tool(name="openapi_validate_spec")
def tool_validate() -> dict[str, Any]:
    return _handle(validate_spec, _spec())


@mcp.tool(name="openapi_generate_client_code")
def tool_gen_client(language: str = "python") -> str:
    return _handle(generate_client_code, _spec(), language)


@mcp.tool(name="openapi_export_summary")
def tool_summary() -> dict[str, Any]:
    return _handle(export_spec_summary, _spec())


@mcp.tool(name="openapi_get_tags")
def tool_tags() -> list[dict[str, str]]:
    return _handle(get_tags, _spec())


@mcp.tool(name="openapi_list_by_tag")
def tool_list_by_tag(tag: str) -> list[dict[str, Any]]:
    return _handle(list_operations_by_tag, _spec(), tag)


@mcp.tool(name="openapi_get_response_codes")
def tool_response_codes(operation_id: str) -> dict[str, Any]:
    return _handle(get_response_codes, _spec(), operation_id)


@mcp.tool(name="openapi_compare_specs")
def tool_compare(spec_b_path: str) -> dict[str, Any]:
    spec_b = _handle(load_spec, spec_b_path, settings.allowed_root, settings.timeout_seconds)
    return _handle(compare_specs, _spec(), spec_b)


@mcp.tool(name="openapi_generate_docs")
def tool_gen_docs() -> str:
    return _handle(generate_markdown_docs, _spec())


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("openapi://configuration")
def res_config() -> str:
    return res.openapi_configuration()


@mcp.resource("openapi://spec-basics")
def res_basics() -> str:
    return res.openapi_spec_basics()


@mcp.resource("openapi://best-practices")
def res_best() -> str:
    return res.openapi_best_practices()


@mcp.resource("openapi://quick-reference")
def res_quick() -> str:
    return res.openapi_quick_reference()


@mcp.resource("openapi://error-codes")
def res_errors() -> str:
    return res.openapi_error_codes()


@mcp.resource("openapi://troubleshooting")
def res_trouble() -> str:
    return res.openapi_troubleshooting()


@mcp.resource("openapi://examples")
def res_examples() -> str:
    return res.openapi_examples()


@mcp.resource("openapi://security")
def res_security() -> str:
    return res.openapi_security()


@mcp.resource("openapi://versioning")
def res_versioning() -> str:
    return res.openapi_versioning()


@mcp.resource("openapi://code-generation")
def res_codegen() -> str:
    return res.openapi_code_generation()


@mcp.resource("openapi://testing")
def res_testing() -> str:
    return res.openapi_testing()


@mcp.resource("openapi://documentation")
def res_docs() -> str:
    return res.openapi_documentation()


@mcp.resource("openapi://migration")
def res_migration() -> str:
    return res.openapi_migration()


@mcp.resource("openapi://server-mocking")
def res_mocking() -> str:
    return res.openapi_server_mocking()


@mcp.resource("openapi://webhooks")
def res_webhooks() -> str:
    return res.openapi_webhooks()


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
