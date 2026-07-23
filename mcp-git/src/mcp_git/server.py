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
    git_branch_delete,
    git_branch_list,
    git_merge,
    git_pull,
    git_push,
    git_remote_add,
    git_remote_list,
    git_reset,
    git_stash,
    git_stash_apply,
    git_stash_drop,
    git_stash_list,
    git_tag,
    git_tag_delete,
    git_tag_list,
    prepare_commit,
)
from mcp_git import resources as res

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
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="git_branch_list",
    description="Lista todas las ramas locales y remotas. Retorna: branches[], count.",
)
def tool_git_branch_list() -> dict[str, Any]:
    logger.info("git_branch_list llamado")
    return _handle(git_branch_list, settings.repo_path)


@mcp.tool(
    name="git_branch_delete",
    description="Elimina una rama local. Parametros: branch_name (requerido).",
)
def tool_git_branch_delete(branch_name: str) -> str:
    logger.info("git_branch_delete llamado", branch=branch_name)
    return _handle(git_branch_delete, settings.repo_path, branch_name)


@mcp.tool(
    name="git_merge",
    description="Hace merge de una rama en la rama actual. Parametros: branch_name (requerido).",
)
def tool_git_merge(branch_name: str) -> str:
    logger.info("git_merge llamado", branch=branch_name)
    return _handle(git_merge, settings.repo_path, branch_name)


@mcp.tool(
    name="git_stash",
    description="Guarda cambios temporales en stash. Parametros: message (string opcional).",
)
def tool_git_stash(message: str = "") -> str:
    logger.info("git_stash llamado")
    return _handle(git_stash, settings.repo_path, message)


@mcp.tool(
    name="git_stash_list",
    description="Lista todos los stashes guardados.",
)
def tool_git_stash_list() -> list[dict[str, Any]]:
    logger.info("git_stash_list llamado")
    return _handle(git_stash_list, settings.repo_path)


@mcp.tool(
    name="git_stash_apply",
    description="Aplica un stash sin eliminarlo. Parametros: index (int, default 0).",
)
def tool_git_stash_apply(index: int = 0) -> str:
    logger.info("git_stash_apply llamado", index=index)
    return _handle(git_stash_apply, settings.repo_path, index)


@mcp.tool(
    name="git_stash_drop",
    description="Elimina un stash. Parametros: index (int, default 0).",
)
def tool_git_stash_drop(index: int = 0) -> str:
    logger.info("git_stash_drop llamado", index=index)
    return _handle(git_stash_drop, settings.repo_path, index)


@mcp.tool(
    name="git_tag",
    description="Crea un tag anotado. Parametros: name (requerido), message (string opcional).",
)
def tool_git_tag(name: str, message: str = "") -> str:
    logger.info("git_tag llamado", tag=name)
    return _handle(git_tag, settings.repo_path, name, message)


@mcp.tool(
    name="git_tag_list",
    description="Lista todos los tags con su hash.",
)
def tool_git_tag_list() -> list[dict[str, Any]]:
    logger.info("git_tag_list llamado")
    return _handle(git_tag_list, settings.repo_path)


@mcp.tool(
    name="git_tag_delete",
    description="Elimina un tag. Parametros: name (requerido).",
)
def tool_git_tag_delete(name: str) -> str:
    logger.info("git_tag_delete llamado", tag=name)
    return _handle(git_tag_delete, settings.repo_path, name)


@mcp.tool(
    name="git_remote_list",
    description="Lista los remotos configurados con sus URLs.",
)
def tool_git_remote_list() -> list[dict[str, Any]]:
    logger.info("git_remote_list llamado")
    return _handle(git_remote_list, settings.repo_path)


@mcp.tool(
    name="git_remote_add",
    description="Anade un remoto. Parametros: name (requerido), url (requerido).",
)
def tool_git_remote_add(name: str, url: str) -> str:
    logger.info("git_remote_add llamado", name=name)
    return _handle(git_remote_add, settings.repo_path, name, url)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("git://configuration")
def res_config() -> str:
    return res.git_configuration()


@mcp.resource("git://workflow-guide")
def res_workflow() -> str:
    return res.git_workflow_guide()


@mcp.resource("git://commit-best-practices")
def res_commit() -> str:
    return res.git_commit_best_practices()


@mcp.resource("git://branching-strategy")
def res_branching() -> str:
    return res.git_branching_strategy()


@mcp.resource("git://troubleshooting")
def res_trouble() -> str:
    return res.git_troubleshooting()


@mcp.resource("git://quick-reference")
def res_quick() -> str:
    return res.git_quick_reference()


@mcp.resource("git://security-guide")
def res_sec() -> str:
    return res.git_security_guide()


@mcp.resource("git://error-codes")
def res_errors() -> str:
    return res.git_error_codes()


@mcp.resource("git://examples")
def res_examples() -> str:
    return res.git_examples()


@mcp.resource("git://merge-guide")
def res_merge() -> str:
    return res.git_merge_guide()


@mcp.resource("git://stash-guide")
def res_stash() -> str:
    return res.git_stash_guide()


@mcp.resource("git://tag-guide")
def res_tag() -> str:
    return res.git_tag_guide()


@mcp.resource("git://remote-guide")
def res_remote() -> str:
    return res.git_remote_guide()


@mcp.resource("git://rebase-guide")
def res_rebase() -> str:
    return res.git_rebase_guide()


@mcp.resource("git://cherry-pick-guide")
def res_cherry() -> str:
    return res.git_cherry_pick_guide()


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
