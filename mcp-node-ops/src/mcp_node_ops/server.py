"""Servidor FastMCP para mcp-node-ops."""

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

from mcp_node_ops.config import settings
from mcp_node_ops.tools import (
    cordon_node,
    drain_node,
    get_node_details,
    get_node_taints,
    list_nodes,
    set_node_label,
    uncordon_node,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-node-ops",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-node-ops")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-node-ops",
    instructions=(
        "Servidor MCP para operaciones de nodos k8s. "
        "Herramientas: list_nodes, get_node_details, get_node_taints (read-only), "
        "cordon_node, uncordon_node, drain_node, set_node_label "
        "(requieren NODE_OPS_ALLOW_WRITE=true)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_nodes", description="Lista todos los nodos del cluster. Retorna: lista de {name, ready, unschedulable, roles, version, internal_ip}.")
def tool_list_nodes() -> list[dict[str, Any]]:
    logger.info("list_nodes llamado")
    try:
        return list_nodes()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_nodes", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_node_details", description="Obtiene detalles completos de un nodo. Parámetros: node_name (str). Retorna: labels, taints, conditions, capacity, allocatable, node_info.")
def tool_get_node_details(node_name: str) -> dict[str, Any]:
    logger.info("get_node_details llamado", node_name=node_name)
    try:
        return get_node_details(node_name=node_name)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_node_details", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="cordon_node", description="Marca un nodo como no programable. Requiere NODE_OPS_ALLOW_WRITE=true. Parámetros: node_name (str).")
def tool_cordon_node(node_name: str) -> dict[str, Any]:
    logger.info("cordon_node llamado", node_name=node_name)
    try:
        return cordon_node(node_name=node_name)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en cordon_node", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="uncordon_node", description="Marca un nodo como programable. Requiere NODE_OPS_ALLOW_WRITE=true. Parámetros: node_name (str).")
def tool_uncordon_node(node_name: str) -> dict[str, Any]:
    logger.info("uncordon_node llamado", node_name=node_name)
    try:
        return uncordon_node(node_name=node_name)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en uncordon_node", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="drain_node", description="Drena un nodo (evict pods). Requiere NODE_OPS_ALLOW_WRITE=true. Parámetros: node_name, force (bool), ignore_daemonsets (bool). Retorna: {node, evicted, skipped}.")
def tool_drain_node(node_name: str, force: bool = False, ignore_daemonsets: bool = True) -> dict[str, Any]:
    logger.info("drain_node llamado", node_name=node_name, force=force)
    try:
        return drain_node(node_name=node_name, force=force, ignore_daemonsets=ignore_daemonsets)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en drain_node", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_node_taints", description="Obtiene los taints de un nodo. Parámetros: node_name (str). Retorna: lista de {key, value, effect}.")
def tool_get_node_taints(node_name: str) -> list[dict[str, Any]]:
    logger.info("get_node_taints llamado", node_name=node_name)
    try:
        return get_node_taints(node_name=node_name)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_node_taints", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="set_node_label", description="Establece un label en un nodo. Requiere NODE_OPS_ALLOW_WRITE=true. Parámetros: node_name, key, value. Retorna: {node, label, value, status}.")
def tool_set_node_label(node_name: str, key: str, value: str) -> dict[str, Any]:
    logger.info("set_node_label llamado", node_name=node_name, key=key)
    try:
        return set_node_label(node_name=node_name, key=key, value=value)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en set_node_label", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
