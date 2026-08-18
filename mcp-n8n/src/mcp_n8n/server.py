"""Servidor FastMCP para mcp-n8n."""

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

from mcp_n8n.config import settings
from mcp_n8n.tools import (
    activate_workflow,
    get_execution_detail,
    get_workflow,
    list_executions,
    list_workflows,
    trigger_webhook,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-n8n",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-n8n")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-n8n",
    instructions=(
        "Servidor MCP para n8n. "
        "Herramientas: list_workflows, get_workflow, trigger_webhook, "
        "list_executions, get_execution_detail, "
        "activate_workflow (requiere N8N_ALLOW_ACTIVATE=true)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_workflows", description="Lista workflows de n8n. Retorna: lista de {id, name, active, nodes, created_at, updated_at}.")
def tool_list_workflows() -> list[dict[str, Any]]:
    logger.info("list_workflows llamado")
    try:
        return list_workflows()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_workflows", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_workflow", description="Obtiene detalles de un workflow. Parámetros: workflow_id (str). Retorna: id, name, active, nodes, connections, settings.")
def tool_get_workflow(workflow_id: str) -> dict[str, Any]:
    logger.info("get_workflow llamado", workflow_id=workflow_id)
    try:
        return get_workflow(workflow_id=workflow_id)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_workflow", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="trigger_webhook", description="Dispara un webhook de n8n. Parámetros: webhook_id (str), data (dict opcional). Retorna: {webhook_id, status_code, response}.")
def tool_trigger_webhook(webhook_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    logger.info("trigger_webhook llamado", webhook_id=webhook_id)
    try:
        return trigger_webhook(webhook_id=webhook_id, data=data)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en trigger_webhook", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_executions", description="Lista ejecuciones recientes de n8n. Parámetros: limit (int, default 20). Retorna: lista de {id, workflow_id, status, mode, started_at, stopped_at, finished}.")
def tool_list_executions(limit: int = 20) -> list[dict[str, Any]]:
    logger.info("list_executions llamado", limit=limit)
    try:
        return list_executions(limit=limit)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_executions", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_execution_detail", description="Obtiene detalles de una ejecución. Parámetros: execution_id (str). Retorna: id, workflow_id, status, data, error.")
def tool_get_execution_detail(execution_id: str) -> dict[str, Any]:
    logger.info("get_execution_detail llamado", execution_id=execution_id)
    try:
        return get_execution_detail(execution_id=execution_id)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_execution_detail", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="activate_workflow", description="Activa/desactiva un workflow. Requiere N8N_ALLOW_ACTIVATE=true. Parámetros: workflow_id (str), active (bool, default true).")
def tool_activate_workflow(workflow_id: str, active: bool = True) -> dict[str, Any]:
    logger.info("activate_workflow llamado", workflow_id=workflow_id, active=active)
    try:
        return activate_workflow(workflow_id=workflow_id, active=active)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en activate_workflow", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
