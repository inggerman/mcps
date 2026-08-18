"""Servidor FastMCP para mcp-harbor."""

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

from mcp_harbor.config import settings
from mcp_harbor.tools import (
    delete_tag,
    get_scan_report,
    image_exists,
    list_projects,
    list_repositories,
    list_tags,
)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-harbor",
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-harbor")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

# ---------------------------------------------------------------------------
# Instancia del servidor
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-harbor",
    instructions=(
        "Servidor MCP para Harbor registry. "
        "Herramientas: list_projects, list_repositories, list_tags, "
        "get_scan_report (vulnerabilidades), image_exists (verificar imagen), "
        "delete_tag (requiere HARBOR_ALLOW_DELETE=true)."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="list_projects",
    description="Lista todos los proyectos de Harbor. Retorna: lista de {project_id, name, repo_count, metadata}.",
)
def tool_list_projects() -> list[dict[str, Any]]:
    logger.info("list_projects llamado")
    try:
        return list_projects()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_projects", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="list_repositories",
    description="Lista los repositorios de un proyecto. Parámetros: project_name (str requerido). Retorna: lista de {id, name, artifact_count, pull_count}.",
)
def tool_list_repositories(project_name: str) -> list[dict[str, Any]]:
    logger.info("list_repositories llamado", project_name=project_name)
    try:
        return list_repositories(project_name=project_name)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_repositories", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="list_tags",
    description="Lista los tags de un repositorio. Parámetros: project_name (str), repo_name (str). Retorna: lista de {digest, tag, size, push_time, pull_time, scan_status}.",
)
def tool_list_tags(project_name: str, repo_name: str) -> list[dict[str, Any]]:
    logger.info("list_tags llamado", project_name=project_name, repo_name=repo_name)
    try:
        return list_tags(project_name=project_name, repo_name=repo_name)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_tags", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="get_scan_report",
    description="Obtiene el reporte de vulnerabilidades de un artifact. Parámetros: project_name, repo_name, tag. Retorna: tag, repository, scan_status, severity, vulnerabilities {critical, high, medium, low, none}, details.",
)
def tool_get_scan_report(project_name: str, repo_name: str, tag: str) -> dict[str, Any]:
    logger.info("get_scan_report llamado", project_name=project_name, repo_name=repo_name, tag=tag)
    try:
        return get_scan_report(project_name=project_name, repo_name=repo_name, tag=tag)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_scan_report", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="image_exists",
    description="Verifica si una imagen existe en Harbor. Parámetros: project_name, repo_name, tag (default 'latest'). Retorna: bool.",
)
def tool_image_exists(project_name: str, repo_name: str, tag: str = "latest") -> bool:
    logger.info("image_exists llamado", project_name=project_name, repo_name=repo_name, tag=tag)
    try:
        return image_exists(project_name=project_name, repo_name=repo_name, tag=tag)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en image_exists", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="delete_tag",
    description="Elimina un tag de Harbor. Requiere HARBOR_ALLOW_DELETE=true. Parámetros: project_name, repo_name, tag. Retorna: confirmación.",
)
def tool_delete_tag(project_name: str, repo_name: str, tag: str) -> dict[str, Any]:
    logger.info("delete_tag llamado", project_name=project_name, repo_name=repo_name, tag=tag)
    try:
        return delete_tag(project_name=project_name, repo_name=repo_name, tag=tag)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en delete_tag", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
