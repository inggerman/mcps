from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_observability.config import settings
from mcp_observability.tools import check_endpoint, query_loki, query_prometheus

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-observability",
)
logger = get_logger(__name__)
mcp = FastMCP(name="mcp-observability", instructions="Consultas PromQL, LogQL y health checks.")


def _handle(fn: Any, *args: Any) -> Any:
    try:
        return fn(*args)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="observability_prometheus_query")
def tool_prometheus(query: str, timestamp: float | None = None) -> dict[str, Any]:
    return _handle(
        query_prometheus,
        settings.prometheus_url,
        query,
        settings.timeout_seconds,
        settings.bearer_token,
        timestamp,
    )


@mcp.tool(name="observability_loki_query")
def tool_loki(
    query: str,
    start_ns: int | None = None,
    end_ns: int | None = None,
) -> dict[str, Any]:
    return _handle(
        query_loki,
        settings.loki_url,
        query,
        settings.timeout_seconds,
        settings.max_entries,
        settings.bearer_token,
        start_ns,
        end_ns,
    )


@mcp.tool(name="observability_health_check")
def tool_health(url: str) -> dict[str, Any]:
    return _handle(check_endpoint, url, settings.timeout_seconds)


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
