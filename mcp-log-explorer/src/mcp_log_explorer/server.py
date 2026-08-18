"""Servidor FastMCP para mcp-log-explorer."""

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

from mcp_log_explorer.config import settings
from mcp_log_explorer.tools import (
    get_pod_logs,
    search_logs_across_pods,
    tail_pod_logs,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-log-explorer",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-log-explorer")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-log-explorer",
    instructions=(
        "Servidor MCP para exploración de logs de k8s. "
        "Herramientas: get_pod_logs (logs de un pod), "
        "tail_pod_logs (últimas N líneas), "
        "search_logs_across_pods (buscar patrón en múltiples pods)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="get_pod_logs", description="Obtiene logs de un pod. Parámetros: pod_name, namespace, container, tail_lines (int), previous (bool). Retorna: {pod, namespace, container, line_count, logs}.")
def tool_get_pod_logs(pod_name: str, namespace: str | None = None, container: str | None = None, tail_lines: int = 100, previous: bool = False) -> dict[str, Any]:
    logger.info("get_pod_logs llamado", pod_name=pod_name, namespace=namespace)
    try:
        return get_pod_logs(pod_name=pod_name, namespace=namespace, container=container, tail_lines=tail_lines, previous=previous)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_pod_logs", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="tail_pod_logs", description="Obtiene las últimas N líneas de logs. Parámetros: pod_name, namespace, container, lines (int, default 50). Retorna: {pod, namespace, container, line_count, logs}.")
def tool_tail_pod_logs(pod_name: str, namespace: str | None = None, container: str | None = None, lines: int = 50) -> dict[str, Any]:
    logger.info("tail_pod_logs llamado", pod_name=pod_name, lines=lines)
    try:
        return tail_pod_logs(pod_name=pod_name, namespace=namespace, container=container, lines=lines)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en tail_pod_logs", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="search_logs_across_pods", description="Busca un patrón en logs de múltiples pods. Parámetros: namespace, pattern (str), label_selector (str), tail_lines (int). Retorna: lista de {pod, container, matches, lines}.")
def tool_search_logs_across_pods(namespace: str | None = None, pattern: str = "", label_selector: str = "", tail_lines: int = 50) -> list[dict[str, Any]]:
    logger.info("search_logs_across_pods llamado", namespace=namespace, pattern=pattern[:50])
    try:
        return search_logs_across_pods(namespace=namespace, pattern=pattern, label_selector=label_selector, tail_lines=tail_lines)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en search_logs_across_pods", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
