"""Servidor FastMCP para mcp-cluster-doctor."""

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

from mcp_cluster_doctor.config import settings
from mcp_cluster_doctor.tools import (
    get_cluster_events,
    get_node_health,
    get_pod_status,
    get_resource_usage,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-cluster-doctor",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-cluster-doctor")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-cluster-doctor",
    instructions=(
        "Servidor MCP para diagnósticos de cluster k8s. "
        "Herramientas: get_node_health (estado de nodos), "
        "get_pod_status (estado de pods por namespace), "
        "get_cluster_events (eventos recientes), "
        "get_resource_usage (requests/limits)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="get_node_health", description="Obtiene el estado de salud de todos los nodos. Retorna: lista de {name, ready, memory_pressure, disk_pressure, kubelet_version, addresses}.")
def tool_get_node_health() -> list[dict[str, Any]]:
    logger.info("get_node_health llamado")
    try:
        return get_node_health()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_node_health", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_pod_status", description="Obtiene el estado de los pods. Parámetros: namespace (str, 'all' para todos). Retorna: lista de {name, namespace, phase, restart_count, containers}.")
def tool_get_pod_status(namespace: str | None = None) -> list[dict[str, Any]]:
    logger.info("get_pod_status llamado", namespace=namespace)
    try:
        return get_pod_status(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_pod_status", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_cluster_events", description="Obtiene eventos recientes del cluster. Parámetros: namespace (str, 'all' para todos), limit (int, default 50). Retorna: lista de {name, type, reason, message, involved_object}.")
def tool_get_cluster_events(namespace: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    logger.info("get_cluster_events llamado", namespace=namespace, limit=limit)
    try:
        return get_cluster_events(namespace=namespace, limit=limit)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_cluster_events", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_resource_usage", description="Obtiene el uso de recursos (requests/limits). Parámetros: namespace (str, 'all' para todos). Retorna: {namespace, pod_count, total_requests, total_limits}.")
def tool_get_resource_usage(namespace: str | None = None) -> dict[str, Any]:
    logger.info("get_resource_usage llamado", namespace=namespace)
    try:
        return get_resource_usage(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_resource_usage", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
