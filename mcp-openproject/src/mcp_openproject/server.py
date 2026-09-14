"""Servidor FastMCP para mcp-openproject."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import MCPError as SdkMcpError
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_openproject.config import settings
from mcp_openproject.tools import (
    create_relation,
    create_time_entry,
    create_work_package,
    get_work_package,
    list_projects,
    list_relations,
    list_statuses,
    list_time_entries,
    list_types,
    list_work_packages,
    update_work_package,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-openproject",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-openproject")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-openproject",
    instructions=(
        "Servidor MCP para OpenProject (gestión clásica de proyectos). "
        "Herramientas: list_projects, list_work_packages, get_work_package, "
        "create_work_package (requiere OPENPROJECT_ALLOW_WRITE=true), "
        "update_work_package (requiere OPENPROJECT_ALLOW_WRITE=true), list_types, "
        "list_statuses, list_relations, create_relation (requiere write), "
        "list_time_entries, create_time_entry (requiere write)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_projects", description="Lista proyectos de OpenProject. Parámetros: limit (int, default 50). Retorna: lista de {id, identifier, name, description, status, created_at, updated_at}.")
def tool_list_projects(limit: int = 50) -> list[dict[str, Any]]:
    logger.info("list_projects llamado", limit=limit)
    try:
        return list_projects(limit=limit)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_projects", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="list_work_packages", description="Lista work packages de OpenProject con filtros opcionales. Parámetros: project_id (opcional), type_id (opcional), status_id (opcional), assignee_id (opcional), limit (default 50). Retorna: lista de {id, subject, type, status, priority, assignee, project, created_at, updated_at, start_date, due_date}.")
def tool_list_work_packages(
    project_id: int | None = None,
    type_id: int | None = None,
    status_id: int | None = None,
    assignee_id: int | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    logger.info("list_work_packages llamado", project_id=project_id, limit=limit)
    try:
        return list_work_packages(
            project_id=project_id,
            type_id=type_id,
            status_id=status_id,
            assignee_id=assignee_id,
            limit=limit,
        )
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_work_packages", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="get_work_package", description="Obtiene el detalle de un work package de OpenProject. Parámetros: work_package_id. Retorna: {id, subject, description, description_html, type, status, priority, assignee, project, created_at, updated_at, start_date, due_date, estimated_time, spent_time}.")
def tool_get_work_package(work_package_id: int) -> dict[str, Any]:
    logger.info("get_work_package llamado", work_package_id=work_package_id)
    try:
        return get_work_package(work_package_id=work_package_id)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_work_package", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="create_work_package", description="Crea un work package en OpenProject. Requiere OPENPROJECT_ALLOW_WRITE=true. Parámetros: project_id, subject, type_id (opcional), description (opcional), assignee_id (opcional), status_id (opcional), priority_id (opcional), start_date (opcional), due_date (opcional). Retorna: {id, subject, type, status}.")
def tool_create_work_package(
    project_id: int,
    subject: str,
    type_id: int | None = None,
    description: str = "",
    assignee_id: int | None = None,
    status_id: int | None = None,
    priority_id: int | None = None,
    start_date: str | None = None,
    due_date: str | None = None,
) -> dict[str, Any]:
    logger.info("create_work_package llamado", project_id=project_id, subject=subject)
    try:
        return create_work_package(
            project_id=project_id,
            subject=subject,
            type_id=type_id,
            description=description,
            assignee_id=assignee_id,
            status_id=status_id,
            priority_id=priority_id,
            start_date=start_date,
            due_date=due_date,
        )
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en create_work_package", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="update_work_package", description="Actualiza un work package de OpenProject. Requiere OPENPROJECT_ALLOW_WRITE=true. Parámetros: work_package_id, status_id (opcional), assignee_id (opcional), type_id (opcional), priority_id (opcional), subject (opcional), description (opcional), start_date (opcional), due_date (opcional). Retorna: {id, subject, status, type, updated_at}.")
def tool_update_work_package(
    work_package_id: int,
    status_id: int | None = None,
    assignee_id: int | None = None,
    type_id: int | None = None,
    priority_id: int | None = None,
    subject: str | None = None,
    description: str | None = None,
    start_date: str | None = None,
    due_date: str | None = None,
) -> dict[str, Any]:
    logger.info("update_work_package llamado", work_package_id=work_package_id)
    try:
        return update_work_package(
            work_package_id=work_package_id,
            status_id=status_id,
            assignee_id=assignee_id,
            type_id=type_id,
            priority_id=priority_id,
            subject=subject,
            description=description,
            start_date=start_date,
            due_date=due_date,
        )
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en update_work_package", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="list_types", description="Lista los tipos de work package de OpenProject (Task, Bug, Milestone, etc.). Retorna: lista de {id, name, color, is_default, is_milestone}.")
def tool_list_types() -> list[dict[str, Any]]:
    logger.info("list_types llamado")
    try:
        return list_types()
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_types", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="list_statuses", description="Lista los estados de work package de OpenProject. Retorna: lista de {id, name, color, is_default, is_closed}.")
def tool_list_statuses() -> list[dict[str, Any]]:
    logger.info("list_statuses llamado")
    try:
        return list_statuses()
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_statuses", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="list_relations", description="Lista las relaciones de un work package de OpenProject (blocks, blocked_by, relates). Parámetros: work_package_id. Retorna: lista de {id, type, from_id, to_id, from, to}.")
def tool_list_relations(work_package_id: int) -> list[dict[str, Any]]:
    logger.info("list_relations llamado", work_package_id=work_package_id)
    try:
        return list_relations(work_package_id=work_package_id)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_relations", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="create_relation", description="Crea una relación entre work packages de OpenProject. Requiere OPENPROJECT_ALLOW_WRITE=true. Parámetros: from_id, to_id, relation_type (relates|blocks|blocked_by|follows|precedes|duplicates|duplicated_by, default relates). Retorna: {id, type, from_id, to_id}.")
def tool_create_relation(from_id: int, to_id: int, relation_type: str = "relates") -> dict[str, Any]:
    logger.info("create_relation llamado", from_id=from_id, to_id=to_id, relation_type=relation_type)
    try:
        return create_relation(from_id=from_id, to_id=to_id, relation_type=relation_type)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en create_relation", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="list_time_entries", description="Lista entradas de time-tracking de OpenProject. Parámetros: work_package_id (opcional), limit (default 50). Retorna: lista de {id, hours, spent_on, activity, work_package, user, comment, created_at}.")
def tool_list_time_entries(work_package_id: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
    logger.info("list_time_entries llamado", work_package_id=work_package_id, limit=limit)
    try:
        return list_time_entries(work_package_id=work_package_id, limit=limit)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_time_entries", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


@mcp.tool(name="create_time_entry", description="Registra tiempo en un work package de OpenProject. Requiere OPENPROJECT_ALLOW_WRITE=true. Parámetros: work_package_id, hours (float), spent_on (YYYY-MM-DD), activity_id (opcional), comment (opcional). Retorna: {id, hours, spent_on}.")
def tool_create_time_entry(
    work_package_id: int,
    hours: float,
    spent_on: str,
    activity_id: int | None = None,
    comment: str = "",
) -> dict[str, Any]:
    logger.info("create_time_entry llamado", work_package_id=work_package_id, hours=hours)
    try:
        return create_time_entry(
            work_package_id=work_package_id,
            hours=hours,
            spent_on=spent_on,
            activity_id=activity_id,
            comment=comment,
        )
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado en create_time_entry", exc_info=exc)
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
