"""Servidor FastMCP para mcp-plane."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import MCPError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_plane.config import settings
from mcp_plane.tools import (
    create_issue,
    get_issue,
    list_cycles,
    list_issues,
    list_labels,
    list_modules,
    list_projects,
    list_states,
    update_issue,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-plane",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-plane")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-plane",
    instructions=(
        "Servidor MCP para Plane (issue-tracking ágil). "
        "Herramientas: list_projects, list_cycles, list_modules, list_issues, get_issue, "
        "create_issue (requiere PLANE_ALLOW_WRITE=true), update_issue (requiere "
        "PLANE_ALLOW_WRITE=true), list_states, list_labels."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_projects", description="Lista proyectos del workspace de Plane. Parámetros: limit (int, default 50). Retorna: lista de {id, name, identifier, description, state, created_at, updated_at}.")
def tool_list_projects(limit: int = 50) -> list[dict[str, Any]]:
    logger.info("list_projects llamado", limit=limit)
    try:
        return list_projects(limit=limit)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_projects", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="list_cycles", description="Lista cycles (sprints) de un proyecto de Plane. Parámetros: project_id. Retorna: lista de {id, name, description, start_date, end_date, is_active}.")
def tool_list_cycles(project_id: str) -> list[dict[str, Any]]:
    logger.info("list_cycles llamado", project_id=project_id)
    try:
        return list_cycles(project_id=project_id)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_cycles", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="list_modules", description="Lista modules de un proyecto de Plane. Parámetros: project_id. Retorna: lista de {id, name, description, status, start_date, target_date}.")
def tool_list_modules(project_id: str) -> list[dict[str, Any]]:
    logger.info("list_modules llamado", project_id=project_id)
    try:
        return list_modules(project_id=project_id)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_modules", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="list_issues", description="Lista issues de un proyecto de Plane con filtros opcionales. Parámetros: project_id, state (opcional), cycle_id (opcional), module_id (opcional), assignee (opcional), limit (default 50). Retorna: lista de {id, name, sequence_id, state, priority, assignees, labels, cycle, module}.")
def tool_list_issues(
    project_id: str,
    state: str | None = None,
    cycle_id: str | None = None,
    module_id: str | None = None,
    assignee: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    logger.info("list_issues llamado", project_id=project_id, state=state, limit=limit)
    try:
        return list_issues(
            project_id=project_id,
            state=state,
            cycle_id=cycle_id,
            module_id=module_id,
            assignee=assignee,
            limit=limit,
        )
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_issues", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="get_issue", description="Obtiene el detalle de un issue de Plane. Parámetros: project_id, issue_id. Retorna: {id, name, description_html, description_stripped, sequence_id, state, priority, assignees, labels, cycle, module, parent, created_at, updated_at}.")
def tool_get_issue(project_id: str, issue_id: str) -> dict[str, Any]:
    logger.info("get_issue llamado", project_id=project_id, issue_id=issue_id)
    try:
        return get_issue(project_id=project_id, issue_id=issue_id)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_issue", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="create_issue", description="Crea un issue en un proyecto de Plane. Requiere PLANE_ALLOW_WRITE=true. Parámetros: project_id, name, description_html (opcional), state (opcional), priority (opcional), cycle_id (opcional), module_id (opcional), assignees (lista, opcional), labels (lista, opcional). Retorna: {id, name, sequence_id, state, url}.")
def tool_create_issue(
    project_id: str,
    name: str,
    description_html: str = "",
    state: str | None = None,
    priority: str | None = None,
    cycle_id: str | None = None,
    module_id: str | None = None,
    assignees: list[str] | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    logger.info("create_issue llamado", project_id=project_id, name=name)
    try:
        return create_issue(
            project_id=project_id,
            name=name,
            description_html=description_html,
            state=state,
            priority=priority,
            cycle_id=cycle_id,
            module_id=module_id,
            assignees=assignees,
            labels=labels,
        )
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en create_issue", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="update_issue", description="Actualiza un issue de Plane. Requiere PLANE_ALLOW_WRITE=true. Parámetros: project_id, issue_id, state (opcional), priority (opcional), assignees (lista, opcional), labels (lista, opcional), cycle_id (opcional), module_id (opcional). Retorna: {id, name, state, priority, updated_at}.")
def tool_update_issue(
    project_id: str,
    issue_id: str,
    state: str | None = None,
    priority: str | None = None,
    assignees: list[str] | None = None,
    labels: list[str] | None = None,
    cycle_id: str | None = None,
    module_id: str | None = None,
) -> dict[str, Any]:
    logger.info("update_issue llamado", project_id=project_id, issue_id=issue_id)
    try:
        return update_issue(
            project_id=project_id,
            issue_id=issue_id,
            state=state,
            priority=priority,
            assignees=assignees,
            labels=labels,
            cycle_id=cycle_id,
            module_id=module_id,
        )
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en update_issue", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="list_states", description="Lista los estados (workflow) de un proyecto de Plane. Parámetros: project_id. Retorna: lista de {id, name, color, group, default, sequence}.")
def tool_list_states(project_id: str) -> list[dict[str, Any]]:
    logger.info("list_states llamado", project_id=project_id)
    try:
        return list_states(project_id=project_id)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_states", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="list_labels", description="Lista las labels de un proyecto de Plane. Parámetros: project_id. Retorna: lista de {id, name, color, parent, sequence}.")
def tool_list_labels(project_id: str) -> list[dict[str, Any]]:
    logger.info("list_labels llamado", project_id=project_id)
    try:
        return list_labels(project_id=project_id)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_labels", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
