"""Servidor FastMCP para mcp-deploy-tracker."""

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

from mcp_deploy_tracker.config import settings
from mcp_deploy_tracker.tools import (
    get_deployment_status,
    get_replica_set_history,
    get_rollout_status,
    list_deployments,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-deploy-tracker",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-deploy-tracker")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-deploy-tracker",
    instructions=(
        "Servidor MCP para tracking de deployments en k8s. "
        "Herramientas: list_deployments, get_deployment_status, "
        "get_rollout_status, get_replica_set_history."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_deployments", description="Lista Deployments en un namespace. Parámetros: namespace (str opcional). Retorna: lista de {name, replicas, ready_replicas, image, strategy}.")
def tool_list_deployments(namespace: str | None = None) -> list[dict[str, Any]]:
    logger.info("list_deployments llamado", namespace=namespace)
    try:
        return list_deployments(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_deployments", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_deployment_status", description="Obtiene estado detallado de un Deployment. Parámetros: name (str), namespace (str opcional). Retorna: {name, replicas, ready, conditions, all_ready}.")
def tool_get_deployment_status(name: str, namespace: str | None = None) -> dict[str, Any]:
    logger.info("get_deployment_status llamado", name=name, namespace=namespace)
    try:
        return get_deployment_status(name=name, namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_deployment_status", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_rollout_status", description="Obtiene estado del rollout. Parámetros: name (str), namespace (str opcional). Retorna: {rollout_status, message, desired, updated, available, complete}.")
def tool_get_rollout_status(name: str, namespace: str | None = None) -> dict[str, Any]:
    logger.info("get_rollout_status llamado", name=name, namespace=namespace)
    try:
        return get_rollout_status(name=name, namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_rollout_status", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_replica_set_history", description="Obtiene historial de ReplicaSets de un Deployment. Parámetros: name (str), namespace (str opcional). Retorna: lista de {name, revision, change_cause, image}.")
def tool_get_replica_set_history(name: str, namespace: str | None = None) -> list[dict[str, Any]]:
    logger.info("get_replica_set_history llamado", name=name, namespace=namespace)
    try:
        return get_replica_set_history(name=name, namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_replica_set_history", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
