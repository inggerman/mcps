"""
Servidor FastMCP para mcp-github.

Expone herramientas de integración con GitHub.
"""

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

from mcp_github import __version__
from mcp_github.config import settings
from mcp_github.tools.github_tools import (
    add_issue_comment,
    create_issue,
    create_pull_request,
    get_issue,
    get_pull_request_diff,
)

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-github",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Ciclo de vida del servidor GitHub."""
    structlog.contextvars.bind_contextvars(server_name="mcp-github")
    logger.info(
        "mcp-github iniciando",
        version=__version__,
        owner=settings.owner,
        repo=settings.repo,
    )
    yield
    logger.info("mcp-github detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-github",
    instructions=(
        "Servidor MCP para interactuar con la API REST de GitHub. "
        "Requiere GITHUB_TOKEN configurado en el .env. "
        "Usa las herramientas para leer y crear Issues y PRs."
    ),
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Wrapper estándar para captura de errores MCP."""
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__, error=str(exc))
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de github.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="github_create_issue",
    description="Crea un issue en GitHub. Parámetros owner y repo son obligatorios si no están en .env.",
)
def tool_create_issue(
    title: str,
    body: str,
    labels: list[str] | None = None,
    owner: str = "",
    repo: str = "",
) -> dict[str, Any]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    logger.info("create_issue llamado", owner=target_owner, repo=target_repo)
    return _handle(
        create_issue,
        settings.token,
        settings.api_url,
        settings.timeout_seconds,
        target_owner,
        target_repo,
        title,
        body,
        labels,
    )


@mcp.tool(
    name="github_get_issue", description="Obtiene información detallada de un issue por su número."
)
def tool_get_issue(issue_number: int, owner: str = "", repo: str = "") -> dict[str, Any]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    logger.info("get_issue llamado", issue_number=issue_number)
    return _handle(
        get_issue,
        settings.token,
        settings.api_url,
        settings.timeout_seconds,
        target_owner,
        target_repo,
        issue_number,
    )


@mcp.tool(
    name="github_create_pull_request",
    description="Crea un Pull Request de la rama 'head' a 'base'.",
)
def tool_create_pull_request(
    title: str,
    head: str,
    base: str,
    body: str = "",
    owner: str = "",
    repo: str = "",
) -> dict[str, Any]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    logger.info("create_pull_request llamado", head=head, base=base)
    return _handle(
        create_pull_request,
        settings.token,
        settings.api_url,
        settings.timeout_seconds,
        target_owner,
        target_repo,
        title,
        head,
        base,
        body,
    )


@mcp.tool(
    name="github_get_pull_request_diff", description="Obtiene el diff completo de un Pull Request."
)
def tool_get_pull_request_diff(pull_number: int, owner: str = "", repo: str = "") -> str:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    logger.info("get_pull_request_diff llamado", pull_number=pull_number)
    return _handle(
        get_pull_request_diff,
        settings.token,
        settings.api_url,
        settings.timeout_seconds,
        target_owner,
        target_repo,
        pull_number,
    )


@mcp.tool(
    name="github_add_issue_comment", description="Agrega un comentario a un issue o Pull Request."
)
def tool_add_issue_comment(
    issue_number: int,
    body: str,
    owner: str = "",
    repo: str = "",
) -> dict[str, Any]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    logger.info("add_issue_comment llamado", issue_number=issue_number)
    return _handle(
        add_issue_comment,
        settings.token,
        settings.api_url,
        settings.timeout_seconds,
        target_owner,
        target_repo,
        issue_number,
        body,
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
