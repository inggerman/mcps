"""Servidor FastMCP para mcp-image-builder."""

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

from mcp_image_builder.config import settings
from mcp_image_builder.tools import (
    get_image_scan,
    get_image_vulnerabilities,
    inspect_image,
    list_repositories,
    list_tags,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-image-builder",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-image-builder")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-image-builder",
    instructions=(
        "Servidor MCP para operaciones de imágenes de contenedor via Harbor. "
        "Herramientas: list_repositories, list_tags, inspect_image, "
        "get_image_scan, get_image_vulnerabilities."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_repositories", description="Lista repositorios en un proyecto de Harbor. Parámetros: project (str opcional). Retorna: lista de {name, artifact_count, pull_count}.")
def tool_list_repositories(project: str | None = None) -> list[dict[str, Any]]:
    logger.info("list_repositories llamado", project=project)
    try:
        return list_repositories(project=project)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_repositories", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_tags", description="Lista tags/artifacts de un repositorio. Parámetros: repo_name (str), project (str opcional). Retorna: lista de {digest, type, size, tags, push_time}.")
def tool_list_tags(repo_name: str, project: str | None = None) -> list[dict[str, Any]]:
    logger.info("list_tags llamado", repo_name=repo_name)
    try:
        return list_tags(repo_name=repo_name, project=project)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_tags", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="inspect_image", description="Inspecciona un artifact por tag o digest. Parámetros: repo_name, tag_or_digest, project. Retorna: digest, type, size, tags, labels, extra_attrs.")
def tool_inspect_image(repo_name: str, tag_or_digest: str, project: str | None = None) -> dict[str, Any]:
    logger.info("inspect_image llamado", repo_name=repo_name, ref=tag_or_digest)
    try:
        return inspect_image(repo_name=repo_name, tag_or_digest=tag_or_digest, project=project)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en inspect_image", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_image_scan", description="Obtiene el estado del scan de un artifact. Parámetros: repo_name, tag_or_digest, project. Retorna: {status, scan_time, scanner}.")
def tool_get_image_scan(repo_name: str, tag_or_digest: str, project: str | None = None) -> dict[str, Any]:
    logger.info("get_image_scan llamado", repo_name=repo_name, ref=tag_or_digest)
    try:
        return get_image_scan(repo_name=repo_name, tag_or_digest=tag_or_digest, project=project)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_image_scan", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_image_vulnerabilities", description="Obtiene vulnerabilidades de un artifact. Parámetros: repo_name, tag_or_digest, project. Retorna: {summary {critical, high, medium, low, total}, vulnerabilities[].}")
def tool_get_image_vulnerabilities(repo_name: str, tag_or_digest: str, project: str | None = None) -> dict[str, Any]:
    logger.info("get_image_vulnerabilities llamado", repo_name=repo_name, ref=tag_or_digest)
    try:
        return get_image_vulnerabilities(repo_name=repo_name, tag_or_digest=tag_or_digest, project=project)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_image_vulnerabilities", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
