from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_openapi.config import settings
from mcp_openapi.tools import describe_operation, invoke_operation, list_operations, load_spec

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


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
