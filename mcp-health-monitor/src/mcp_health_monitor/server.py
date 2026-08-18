"""Servidor FastMCP para mcp-health-monitor."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_health_monitor.config import settings
from mcp_health_monitor.tools import (
    check_endpoint_health,
    get_hpa_status,
    get_probe_status,
    get_unhealthy_pods,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-health-monitor",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-health-monitor")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-health-monitor",
    instructions=(
        "Servidor MCP para monitoreo de salud de k8s. "
        "Herramientas: get_probe_status (readiness/liveness), "
        "get_hpa_status (HPA status), "
        "check_endpoint_health (endpoints), "
        "get_unhealthy_pods (pods con problemas)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="get_probe_status", description="Obtiene estado de readiness/liveness probes. Parámetros: namespace (str opcional). Retorna: lista de {pod, container, ready, probes}.")
def tool_get_probe_status(namespace: str | None = None) -> list[dict[str, Any]]:
    logger.info("get_probe_status llamado", namespace=namespace)
    try:
        return get_probe_status(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_probe_status", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_hpa_status", description="Obtiene estado de HorizontalPodAutoscalers. Parámetros: namespace (str opcional). Retorna: lista de {name, target, min/max/current/desired replicas, metrics}.")
def tool_get_hpa_status(namespace: str | None = None) -> list[dict[str, Any]]:
    logger.info("get_hpa_status llamado", namespace=namespace)
    try:
        return get_hpa_status(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_hpa_status", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="check_endpoint_health", description="Verifica salud de Endpoints en un namespace. Parámetros: namespace (str). Retorna: lista de {name, ready_addresses, not_ready_addresses, healthy}.")
def tool_check_endpoint_health(namespace: str) -> list[dict[str, Any]]:
    logger.info("check_endpoint_health llamado", namespace=namespace)
    try:
        return check_endpoint_health(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en check_endpoint_health", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_unhealthy_pods", description="Obtiene pods con problemas (no Running, restarts altos, containers not ready). Parámetros: namespace (str opcional). Retorna: lista de {pod, phase, restarts, not_ready_containers}.")
def tool_get_unhealthy_pods(namespace: str | None = None) -> list[dict[str, Any]]:
    logger.info("get_unhealthy_pods llamado", namespace=namespace)
    try:
        return get_unhealthy_pods(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_unhealthy_pods", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
