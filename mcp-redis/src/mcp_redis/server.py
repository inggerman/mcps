"""Servidor FastMCP para mcp-redis."""

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

from mcp_redis.config import settings
from mcp_redis.tools import (
    delete_key,
    get_key,
    get_key_type,
    get_ttl,
    list_keys,
    redis_info,
    set_key,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-redis",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-redis")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-redis",
    instructions=(
        "Servidor MCP para Redis. "
        "Herramientas: redis_info, list_keys, get_key, set_key (requiere REDIS_ALLOW_WRITE=true), "
        "get_ttl, get_key_type, delete_key (requiere REDIS_ALLOW_WRITE=true)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="redis_info", description="Obtiene información del servidor Redis. Retorna: redis_version, connected_clients, used_memory, db_size.")
def tool_redis_info() -> dict[str, Any]:
    logger.info("redis_info llamado")
    try:
        return redis_info()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en redis_info", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_keys", description="Lista claves que coinciden con un patrón. Parámetros: pattern (str, default '*'), limit (int, default 100). Retorna: lista de keys.")
def tool_list_keys(pattern: str = "*", limit: int = 100) -> list[str]:
    logger.info("list_keys llamado", pattern=pattern, limit=limit)
    try:
        return list_keys(pattern=pattern, limit=limit)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_keys", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_key", description="Obtiene el valor de una clave. Parámetros: key (str). Retorna: {key, type, value}.")
def tool_get_key(key: str) -> dict[str, Any]:
    logger.info("get_key llamado", key=key)
    try:
        return get_key(key=key)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_key", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="set_key", description="Establece una clave string. Requiere REDIS_ALLOW_WRITE=true. Parámetros: key, value, ttl (int opcional). Retorna: {key, value, ttl, status}.")
def tool_set_key(key: str, value: str, ttl: int | None = None) -> dict[str, Any]:
    logger.info("set_key llamado", key=key)
    try:
        return set_key(key=key, value=value, ttl=ttl)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en set_key", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_ttl", description="Obtiene el TTL de una clave. Parámetros: key (str). Retorna: {key, ttl_seconds}.")
def tool_get_ttl(key: str) -> dict[str, Any]:
    logger.info("get_ttl llamado", key=key)
    try:
        return get_ttl(key=key)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_ttl", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_key_type", description="Obtiene el tipo de una clave. Parámetros: key (str). Retorna: {key, type}.")
def tool_get_key_type(key: str) -> dict[str, Any]:
    logger.info("get_key_type llamado", key=key)
    try:
        return get_key_type(key=key)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_key_type", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="delete_key", description="Elimina una clave. Requiere REDIS_ALLOW_WRITE=true. Parámetros: key (str). Retorna: {key, deleted}.")
def tool_delete_key(key: str) -> dict[str, Any]:
    logger.info("delete_key llamado", key=key)
    try:
        return delete_key(key=key)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en delete_key", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
