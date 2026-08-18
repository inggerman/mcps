"""Servidor FastMCP para mcp-argocd."""

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

from mcp_argocd.config import settings
from mcp_argocd.tools import (
    get_app_diff,
    get_app_history,
    get_app_status,
    list_apps,
    rollback_app,
    sync_app,
)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-argocd",
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-argocd")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

# ---------------------------------------------------------------------------
# Instancia del servidor
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-argocd",
    instructions=(
        "Servidor MCP para ArgoCD. "
        "Herramientas: list_apps (listar aplicaciones), get_app_status (estado detallado), "
        "sync_app (forzar sync, requiere ARGOCD_ALLOW_SYNC=true), "
        "get_app_diff (diff entre deseado y actual), "
        "get_app_history (historial de syncs), "
        "rollback_app (rollback a revisión anterior, requiere ARGOCD_ALLOW_ROLLBACK=true)."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="list_apps",
    description=(
        "Lista todas las aplicaciones de ArgoCD. "
        "Parámetros: project (str opcional, filtra por proyecto). "
        "Retorna: lista de {name, project, sync_status, health_status, target_revision}."
    ),
)
def tool_list_apps(project: str | None = None) -> list[dict[str, Any]]:
    logger.info("list_apps llamado", project=project)
    try:
        return list_apps(project=project)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_apps", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="get_app_status",
    description=(
        "Obtiene el estado detallado de una aplicación de ArgoCD. "
        "Parámetros: app_name (str requerido). "
        "Retorna: name, project, sync_status, health_status, health_message, "
        "target_revision, source, destination, resources, conditions."
    ),
)
def tool_get_app_status(app_name: str) -> dict[str, Any]:
    logger.info("get_app_status llamado", app_name=app_name)
    try:
        return get_app_status(app_name=app_name)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_app_status", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="sync_app",
    description=(
        "Fuerza la sincronización de una aplicación de ArgoCD. "
        "Requiere ARGOCD_ALLOW_SYNC=true. "
        "Parámetros: app_name (str requerido), revision (str opcional), "
        "dry_run (bool, default false). "
        "Retorna: resultado de la operación de sync."
    ),
)
def tool_sync_app(app_name: str, revision: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    logger.info("sync_app llamado", app_name=app_name, revision=revision, dry_run=dry_run)
    try:
        return sync_app(app_name=app_name, revision=revision, dry_run=dry_run)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en sync_app", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="get_app_diff",
    description=(
        "Obtiene el diff entre el estado deseado y el actual de una aplicación. "
        "Parámetros: app_name (str requerido), revision (str opcional). "
        "Retorna: recursos managed con sus diffs."
    ),
)
def tool_get_app_diff(app_name: str, revision: str | None = None) -> dict[str, Any]:
    logger.info("get_app_diff llamado", app_name=app_name, revision=revision)
    try:
        return get_app_diff(app_name=app_name, revision=revision)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_app_diff", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="get_app_history",
    description=(
        "Obtiene el historial de sincronizaciones de una aplicación. "
        "Parámetros: app_name (str requerido). "
        "Retorna: lista de entradas de historial con revision, deployStartedAt, etc."
    ),
)
def tool_get_app_history(app_name: str) -> list[dict[str, Any]]:
    logger.info("get_app_history llamado", app_name=app_name)
    try:
        return get_app_history(app_name=app_name)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_app_history", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="rollback_app",
    description=(
        "Hace rollback de una aplicación a una revisión anterior del historial. "
        "Requiere ARGOCD_ALLOW_ROLLBACK=true. "
        "Parámetros: app_name (str requerido), revision_index (int requerido). "
        "Retorna: confirmación del rollback."
    ),
)
def tool_rollback_app(app_name: str, revision_index: int) -> dict[str, Any]:
    logger.info("rollback_app llamado", app_name=app_name, revision_index=revision_index)
    try:
        return rollback_app(app_name=app_name, revision_index=revision_index)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en rollback_app", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
