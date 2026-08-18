"""Servidor FastMCP para mcp-storage-doctor."""

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

from mcp_storage_doctor.config import settings
from mcp_storage_doctor.tools import (
    get_pvc_status,
    get_volume_mounts,
    list_persistent_volumes,
    list_pvcs,
    list_storage_classes,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-storage-doctor",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-storage-doctor")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-storage-doctor",
    instructions=(
        "Servidor MCP para diagnósticos de almacenamiento en k8s. "
        "Herramientas: list_persistent_volumes, list_pvcs, "
        "get_pvc_status, list_storage_classes, get_volume_mounts."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_persistent_volumes", description="Lista todos los PersistentVolumes. Retorna: lista de {name, capacity, phase, storage_class, claim, reclaim_policy}.")
def tool_list_persistent_volumes() -> list[dict[str, Any]]:
    logger.info("list_persistent_volumes llamado")
    try:
        return list_persistent_volumes()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_persistent_volumes", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_pvcs", description="Lista PersistentVolumeClaims. Parámetros: namespace (str opcional). Retorna: lista de {name, namespace, phase, capacity, storage_class}.")
def tool_list_pvcs(namespace: str | None = None) -> list[dict[str, Any]]:
    logger.info("list_pvcs llamado", namespace=namespace)
    try:
        return list_pvcs(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_pvcs", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_pvc_status", description="Obtiene estado detallado de un PVC. Parámetros: name (str), namespace (str). Retorna: {name, phase, capacity, bound, storage_class}.")
def tool_get_pvc_status(name: str, namespace: str) -> dict[str, Any]:
    logger.info("get_pvc_status llamado", name=name, namespace=namespace)
    try:
        return get_pvc_status(name=name, namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_pvc_status", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_storage_classes", description="Lista StorageClasses disponibles. Retorna: lista de {name, provisioner, reclaim_policy, is_default, parameters}.")
def tool_list_storage_classes() -> list[dict[str, Any]]:
    logger.info("list_storage_classes llamado")
    try:
        return list_storage_classes()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_storage_classes", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_volume_mounts", description="Obtiene volume mounts de pods. Parámetros: namespace (str opcional). Retorna: lista de {pod, namespace, mounts[]}.")
def tool_get_volume_mounts(namespace: str | None = None) -> list[dict[str, Any]]:
    logger.info("get_volume_mounts llamado", namespace=namespace)
    try:
        return get_volume_mounts(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_volume_mounts", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
