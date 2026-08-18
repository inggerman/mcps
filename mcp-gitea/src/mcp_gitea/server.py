"""Servidor FastMCP para mcp-gitea."""

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

from mcp_gitea.config import settings
from mcp_gitea.tools import (
    create_issue,
    create_pr,
    get_run_logs,
    get_workflow_runs,
    list_issues,
    list_prs,
    list_repos,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-gitea",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-gitea")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-gitea",
    instructions=(
        "Servidor MCP para Gitea. "
        "Herramientas: list_repos, list_prs, create_pr (requiere GITEA_ALLOW_WRITE=true), "
        "list_issues, create_issue (requiere GITEA_ALLOW_WRITE=true), "
        "get_workflow_runs (Gitea Actions), get_run_logs."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_repos", description="Lista repositorios de Gitea. Parámetros: limit (int, default 50). Retorna: lista de {id, name, full_name, owner, private, stars, forks, default_branch, updated_at}.")
def tool_list_repos(limit: int = 50) -> list[dict[str, Any]]:
    logger.info("list_repos llamado", limit=limit)
    try:
        return list_repos(limit=limit)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_repos", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_prs", description="Lista PRs de un repo. Parámetros: owner, repo, state (open/closed/all, default open). Retorna: lista de {number, title, state, user, merged, mergeable, head, base}.")
def tool_list_prs(owner: str, repo: str, state: str = "open") -> list[dict[str, Any]]:
    logger.info("list_prs llamado", owner=owner, repo=repo, state=state)
    try:
        return list_prs(owner=owner, repo=repo, state=state)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_prs", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="create_pr", description="Crea un PR. Requiere GITEA_ALLOW_WRITE=true. Parámetros: owner, repo, title, head, base, body. Retorna: {number, title, state, url}.")
def tool_create_pr(owner: str, repo: str, title: str, head: str, base: str, body: str = "") -> dict[str, Any]:
    logger.info("create_pr llamado", owner=owner, repo=repo, title=title)
    try:
        return create_pr(owner=owner, repo=repo, title=title, head=head, base=base, body=body)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en create_pr", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_issues", description="Lista issues de un repo. Parámetros: owner, repo, state (open/closed/all). Retorna: lista de {number, title, state, user, labels, assignee}.")
def tool_list_issues(owner: str, repo: str, state: str = "open") -> list[dict[str, Any]]:
    logger.info("list_issues llamado", owner=owner, repo=repo, state=state)
    try:
        return list_issues(owner=owner, repo=repo, state=state)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_issues", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="create_issue", description="Crea un issue. Requiere GITEA_ALLOW_WRITE=true. Parámetros: owner, repo, title, body. Retorna: {number, title, state, url}.")
def tool_create_issue(owner: str, repo: str, title: str, body: str = "") -> dict[str, Any]:
    logger.info("create_issue llamado", owner=owner, repo=repo, title=title)
    try:
        return create_issue(owner=owner, repo=repo, title=title, body=body)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en create_issue", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_workflow_runs", description="Lista ejecuciones de Gitea Actions. Parámetros: owner, repo, limit (default 20). Retorna: lista de {id, name, status, conclusion, event, head_branch}.")
def tool_get_workflow_runs(owner: str, repo: str, limit: int = 20) -> list[dict[str, Any]]:
    logger.info("get_workflow_runs llamado", owner=owner, repo=repo, limit=limit)
    try:
        return get_workflow_runs(owner=owner, repo=repo, limit=limit)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_workflow_runs", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_run_logs", description="Obtiene logs de una ejecución de Gitea Actions. Parámetros: owner, repo, run_id. Retorna: {run_id, logs}.")
def tool_get_run_logs(owner: str, repo: str, run_id: int) -> dict[str, Any]:
    logger.info("get_run_logs llamado", owner=owner, repo=repo, run_id=run_id)
    try:
        return get_run_logs(owner=owner, repo=repo, run_id=run_id)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_run_logs", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
