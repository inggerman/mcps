"""Servidor FastMCP para mcp-rabbitmq."""

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

from mcp_rabbitmq.config import settings
from mcp_rabbitmq.tools import (
    get_overview,
    get_queue_details,
    list_exchanges,
    list_queues,
    publish_message,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-rabbitmq",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-rabbitmq")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-rabbitmq",
    instructions=(
        "Servidor MCP para RabbitMQ. "
        "Herramientas: get_overview, list_queues, get_queue_details, "
        "list_exchanges, publish_message (requiere RABBITMQ_ALLOW_PUBLISH=true)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="get_overview", description="Obtiene el overview del cluster RabbitMQ. Retorna: version, cluster_name, object_totals, queue_totals, message_stats.")
def tool_get_overview() -> dict[str, Any]:
    logger.info("get_overview llamado")
    try:
        return get_overview()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_overview", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_queues", description="Lista las colas de un vhost. Parámetros: vhost (str, default '/'). Retorna: lista de {name, vhost, durable, messages, consumers, state}.")
def tool_list_queues(vhost: str = "/") -> list[dict[str, Any]]:
    logger.info("list_queues llamado", vhost=vhost)
    try:
        return list_queues(vhost=vhost)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_queues", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_queue_details", description="Obtiene detalles de una cola. Parámetros: queue_name (str), vhost (str, default '/'). Retorna: name, messages, consumers, state, arguments, message_stats.")
def tool_get_queue_details(queue_name: str, vhost: str = "/") -> dict[str, Any]:
    logger.info("get_queue_details llamado", queue_name=queue_name, vhost=vhost)
    try:
        return get_queue_details(queue_name=queue_name, vhost=vhost)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_queue_details", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_exchanges", description="Lista los exchanges de un vhost. Parámetros: vhost (str, default '/'). Retorna: lista de {name, type, durable, internal, auto_delete}.")
def tool_list_exchanges(vhost: str = "/") -> list[dict[str, Any]]:
    logger.info("list_exchanges llamado", vhost=vhost)
    try:
        return list_exchanges(vhost=vhost)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_exchanges", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="publish_message", description="Publica un mensaje en un exchange. Requiere RABBITMQ_ALLOW_PUBLISH=true. Parámetros: exchange, routing_key, payload, vhost, properties. Retorna: resultado de la publicación.")
def tool_publish_message(exchange: str, routing_key: str, payload: str, vhost: str = "/", properties: dict[str, Any] | None = None) -> dict[str, Any]:
    logger.info("publish_message llamado", exchange=exchange, routing_key=routing_key)
    try:
        return publish_message(exchange=exchange, routing_key=routing_key, payload=payload, vhost=vhost, properties=properties)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en publish_message", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
