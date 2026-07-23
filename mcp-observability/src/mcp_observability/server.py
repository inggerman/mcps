from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_observability.config import settings
from mcp_observability.tools import (
    check_endpoint,
    check_multiple_endpoints,
    generate_slo_report,
    get_prometheus_metadata,
    get_prometheus_series,
    list_prometheus_alerts,
    list_prometheus_rules,
    list_prometheus_targets,
    loki_label_values,
    loki_labels,
    loki_status,
    prometheus_range_query,
    prometheus_status,
    query_loki,
    query_prometheus,
)
from mcp_observability import resources as res

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


@mcp.tool(name="observability_prometheus_range")
def tool_prom_range(query: str, start: float, end: float, step: str) -> dict[str, Any]:
    return _handle(prometheus_range_query, settings.prometheus_url, query, start, end, step, settings.timeout_seconds, settings.bearer_token)


@mcp.tool(name="observability_prometheus_targets")
def tool_prom_targets() -> dict[str, Any]:
    return _handle(list_prometheus_targets, settings.prometheus_url, settings.timeout_seconds, settings.bearer_token)


@mcp.tool(name="observability_prometheus_alerts")
def tool_prom_alerts() -> dict[str, Any]:
    return _handle(list_prometheus_alerts, settings.prometheus_url, settings.timeout_seconds, settings.bearer_token)


@mcp.tool(name="observability_prometheus_rules")
def tool_prom_rules() -> dict[str, Any]:
    return _handle(list_prometheus_rules, settings.prometheus_url, settings.timeout_seconds, settings.bearer_token)


@mcp.tool(name="observability_prometheus_series")
def tool_prom_series(match: str, start: float, end: float) -> dict[str, Any]:
    return _handle(get_prometheus_series, settings.prometheus_url, match, start, end, settings.timeout_seconds, settings.bearer_token)


@mcp.tool(name="observability_loki_labels")
def tool_loki_labels() -> dict[str, Any]:
    return _handle(loki_labels, settings.loki_url, settings.timeout_seconds, settings.bearer_token)


@mcp.tool(name="observability_loki_label_values")
def tool_loki_label_values(label: str) -> dict[str, Any]:
    return _handle(loki_label_values, settings.loki_url, label, settings.timeout_seconds, settings.bearer_token)


@mcp.tool(name="observability_check_endpoints")
def tool_check_endpoints(urls: list[str]) -> list[dict[str, Any]]:
    return _handle(check_multiple_endpoints, urls, settings.timeout_seconds)


@mcp.tool(name="observability_prometheus_metadata")
def tool_prom_metadata() -> dict[str, Any]:
    return _handle(get_prometheus_metadata, settings.prometheus_url, settings.timeout_seconds, settings.bearer_token)


@mcp.tool(name="observability_prometheus_status")
def tool_prom_status() -> dict[str, Any]:
    return _handle(prometheus_status, settings.prometheus_url, settings.timeout_seconds, settings.bearer_token)


@mcp.tool(name="observability_loki_status")
def tool_loki_status() -> dict[str, Any]:
    return _handle(loki_status, settings.loki_url, settings.timeout_seconds, settings.bearer_token)


@mcp.tool(name="observability_slo_report")
def tool_slo(slo_query: str, error_query: str) -> dict[str, Any]:
    return _handle(generate_slo_report, settings.prometheus_url, slo_query, error_query, settings.timeout_seconds, settings.bearer_token)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("observability://configuration")
def res_config() -> str:
    return res.observability_configuration()


@mcp.resource("observability://basics")
def res_basics() -> str:
    return res.observability_basics()


@mcp.resource("observability://best-practices")
def res_best() -> str:
    return res.observability_best_practices()


@mcp.resource("observability://quick-reference")
def res_quick() -> str:
    return res.observability_quick_reference()


@mcp.resource("observability://error-codes")
def res_errors() -> str:
    return res.observability_error_codes()


@mcp.resource("observability://troubleshooting")
def res_trouble() -> str:
    return res.observability_troubleshooting()


@mcp.resource("observability://examples")
def res_examples() -> str:
    return res.observability_examples()


@mcp.resource("observability://promql-guide")
def res_promql() -> str:
    return res.observability_promql_guide()


@mcp.resource("observability://logql-guide")
def res_logql() -> str:
    return res.observability_logql_guide()


@mcp.resource("observability://alerting")
def res_alerting() -> str:
    return res.observability_alerting()


@mcp.resource("observability://grafana")
def res_grafana() -> str:
    return res.observability_grafana()


@mcp.resource("observability://tracing")
def res_tracing() -> str:
    return res.observability_tracing()


@mcp.resource("observability://slo")
def res_slo() -> str:
    return res.observability_slo()


@mcp.resource("observability://service-mesh")
def res_mesh() -> str:
    return res.observability_service_mesh()


@mcp.resource("observability://metrics-guide")
def res_metrics() -> str:
    return res.observability_metrics_guide()


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
