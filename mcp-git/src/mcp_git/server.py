"""
Servidor FastMCP para mcp-git.

Expone herramientas de Git asegurando validación en dos pasos
para los commits mediante prepare_commit y confirm_commit.
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

from mcp_git import __version__
from mcp_git.config import settings
from mcp_git.tools.git_tools import (
    confirm_commit,
    get_git_diff,
    get_git_log,
    get_git_status,
    git_add,
    git_branch,
    git_pull,
    git_push,
    git_reset,
    prepare_commit,
)

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-git",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Ciclo de vida del servidor Git."""
    structlog.contextvars.bind_contextvars(server_name="mcp-git")
    logger.info(
        "mcp-git iniciando",
        version=__version__,
        repo_path=str(settings.repo_path),
        allow_force_push=settings.allow_force_push,
    )
    yield
    logger.info("mcp-git detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-git",
    instructions=(
        "Servidor MCP para operaciones locales de Git. "
        "ATENCIÓN: Para hacer un commit, el proceso ESTRICTO es de 2 pasos:\n"
        "1. Usa 'prepare_commit(message)'. Esto te devolverá un diff y un TOKEN.\n"
        "2. Muestra el diff al usuario y pregúntale si confirma el commit.\n"
        "3. SI el usuario confirma, usa 'confirm_commit(token)' para aplicar los cambios."
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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de git.")) from exc


# ---------------------------------------------------------------------------
# Tools de Información
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_git_status",
    description="Retorna el estado de git: branch actual, cambios sin trackear y en stage.",
)
def tool_get_git_status() -> dict[str, Any]:
    logger.info("get_git_status llamado")
    return _handle(get_git_status, settings.repo_path)


@mcp.tool(
    name="get_git_diff",
    description="Retorna el diff de cambios. Parámetros: staged (bool), file_path (str opcional).",
)
def tool_get_git_diff(staged: bool = False, file_path: str = "") -> str:
    logger.info("get_git_diff llamado", staged=staged, file_path=file_path)
    return _handle(get_git_diff, settings.repo_path, staged, file_path)


@mcp.tool(
    name="get_git_log",
    description="Retorna el historial reciente. Parámetro: max_count (int, default 10).",
)
def tool_get_git_log(max_count: int = 10) -> str:
    logger.info("get_git_log llamado", max_count=max_count)
    return _handle(get_git_log, settings.repo_path, max_count)


# ---------------------------------------------------------------------------
# Tools de Modificación (Stage)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="git_add",
    description="Agrega archivos al stage. Parámetro: files (lista de strings, o ['.'] para todos).",
)
def tool_git_add(files: list[str]) -> str:
    logger.info("git_add llamado", files=files)
    return _handle(git_add, settings.repo_path, files)


@mcp.tool(
    name="git_reset",
    description="Quita archivos del stage (unstage). Si no se proveen files, quita todos.",
)
def tool_git_reset(files: list[str] | None = None) -> str:
    logger.info("git_reset llamado", files=files)
    return _handle(git_reset, settings.repo_path, files)


@mcp.tool(
    name="git_branch", description="Cambia de rama (checkout). Usa create=True para crearla (-b)."
)
def tool_git_branch(branch_name: str, create: bool = False) -> str:
    logger.info("git_branch llamado", branch=branch_name, create=create)
    return _handle(git_branch, settings.repo_path, branch_name, create)


# ---------------------------------------------------------------------------
# Commit (Validación de 2 pasos)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="prepare_commit",
    description=(
        "PASO 1 de commit: Prepara el commit con el mensaje dado, revisa qué hay en el stage "
        "y genera un TOKEN. DEBES pedir autorización al usuario mostrando el diff antes de usar confirm_commit."
    ),
)
def tool_prepare_commit(message: str) -> dict[str, Any]:
    logger.info("prepare_commit llamado")
    return _handle(prepare_commit, settings.repo_path, message)


@mcp.tool(
    name="confirm_commit",
    description=(
        "PASO 2 de commit: Aplica el commit previamente preparado usando el TOKEN devuelto "
        "por prepare_commit. SOLO USAR si el usuario aprobó el diff."
    ),
)
def tool_confirm_commit(token: str) -> dict[str, Any]:
    logger.info("confirm_commit llamado", token=token)
    return _handle(confirm_commit, settings.repo_path, token)


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------


@mcp.tool(
    name="git_pull", description="Descarga e integra cambios remotos en la rama actual (git pull)."
)
def tool_git_pull() -> str:
    logger.info("git_pull llamado")
    return _handle(git_pull, settings.repo_path)


@mcp.tool(
    name="git_push",
    description="Sube los commits locales al repositorio remoto. Para --force usa force=True.",
)
def tool_git_push(force: bool = False) -> str:
    logger.info("git_push llamado", force=force)
    return _handle(git_push, settings.repo_path, force, settings.allow_force_push)


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
