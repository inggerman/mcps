"""Servidor FastMCP para mcp-notify."""

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

from mcp_notify.config import settings
from mcp_notify.tools import (
    send_email,
    send_telegram_message,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-notify",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-notify")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-notify",
    instructions=(
        "Servidor MCP para notificaciones. "
        "Herramientas: send_email (SMTP), send_telegram_message (Telegram Bot API). "
        "Requiere configurar NOTIFY_SMTP_* o NOTIFY_TELEGRAM_BOT_TOKEN."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="send_email", description="Envía un email vía SMTP. Parámetros: to (str), subject (str), body (str), html (bool, default false). Retorna: {to, subject, status}.")
def tool_send_email(to: str, subject: str, body: str, html: bool = False) -> dict[str, Any]:
    logger.info("send_email llamado", to=to, subject=subject)
    try:
        return send_email(to=to, subject=subject, body=body, html=html)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en send_email", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="send_telegram_message", description="Envía un mensaje vía Telegram Bot API. Parámetros: chat_id (str), text (str). Retorna: {chat_id, message_id, status}.")
def tool_send_telegram_message(chat_id: str, text: str) -> dict[str, Any]:
    logger.info("send_telegram_message llamado", chat_id=chat_id)
    try:
        return send_telegram_message(chat_id=chat_id, text=text)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en send_telegram_message", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
