"""Servidor FastMCP para mcp-config-sync."""

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

from mcp_config_sync.config import settings
from mcp_config_sync.tools import (
    compare_configmaps,
    get_configmap,
    list_configmaps,
    list_secrets,
    sync_configmap,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-config-sync",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-config-sync")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-config-sync",
    instructions=(
        "Servidor MCP para sincronización de ConfigMaps y Secrets. "
        "Herramientas: list_configmaps, get_configmap, list_secrets, "
        "compare_configmaps (diff entre namespaces), "
        "sync_configmap (copiar entre namespaces, requiere ALLOW_WRITE)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_configmaps", description="Lista ConfigMaps en un namespace. Parámetros: namespace (str). Retorna: lista de {name, data_keys, key_count, labels}.")
def tool_list_configmaps(namespace: str) -> list[dict[str, Any]]:
    logger.info("list_configmaps llamado", namespace=namespace)
    try:
        return list_configmaps(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_configmaps", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_configmap", description="Obtiene el contenido de un ConfigMap. Parámetros: name (str), namespace (str). Retorna: {name, data, labels, annotations}.")
def tool_get_configmap(name: str, namespace: str) -> dict[str, Any]:
    logger.info("get_configmap llamado", name=name, namespace=namespace)
    try:
        return get_configmap(name=name, namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_configmap", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_secrets", description="Lista Secrets en un namespace (sin exponer valores). Parámetros: namespace (str). Retorna: lista de {name, type, key_count, data_keys}.")
def tool_list_secrets(namespace: str) -> list[dict[str, Any]]:
    logger.info("list_secrets llamado", namespace=namespace)
    try:
        return list_secrets(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_secrets", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="compare_configmaps", description="Compara un ConfigMap entre dos namespaces. Parámetros: name, namespace_a, namespace_b. Retorna: {only_in_a, only_in_b, different_values, identical}.")
def tool_compare_configmaps(name: str, namespace_a: str, namespace_b: str) -> dict[str, Any]:
    logger.info("compare_configmaps llamado", name=name, a=namespace_a, b=namespace_b)
    try:
        return compare_configmaps(name=name, namespace_a=namespace_a, namespace_b=namespace_b)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en compare_configmaps", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="sync_configmap", description="Copia un ConfigMap entre namespaces. Requiere CONFIG_SYNC_ALLOW_WRITE=true. Parámetros: name, source_namespace, target_namespace. Retorna: {configmap, source, target, action}.")
def tool_sync_configmap(name: str, source_namespace: str, target_namespace: str) -> dict[str, Any]:
    logger.info("sync_configmap llamado", name=name, src=source_namespace, tgt=target_namespace)
    try:
        return sync_configmap(name=name, source_namespace=source_namespace, target_namespace=target_namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en sync_configmap", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
