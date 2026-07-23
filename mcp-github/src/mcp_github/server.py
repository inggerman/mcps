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
    create_branch,
    create_issue,
    create_pull_request,
    get_file_content,
    get_issue,
    get_issue_comments,
    get_pull_request_diff,
    get_pull_request_files,
    get_repo_info,
    get_user_info,
    list_branches,
    list_commits,
    list_issues,
    list_pull_requests,
)
from mcp_github import resources as res

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
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(name="github_list_issues", description="Lista issues de un repositorio.")
def tool_list_issues(
    state: str = "open", per_page: int = 30, owner: str = "", repo: str = "",
) -> list[dict[str, Any]]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    return _handle(list_issues, settings.token, settings.api_url, settings.timeout_seconds, target_owner, target_repo, state, per_page)


@mcp.tool(name="github_list_branches", description="Lista branches de un repositorio.")
def tool_list_branches(
    per_page: int = 30, owner: str = "", repo: str = "",
) -> list[dict[str, Any]]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    return _handle(list_branches, settings.token, settings.api_url, settings.timeout_seconds, target_owner, target_repo, per_page)


@mcp.tool(name="github_list_commits", description="Lista commits de un repositorio.")
def tool_list_commits(
    sha: str | None = None, per_page: int = 30, owner: str = "", repo: str = "",
) -> list[dict[str, Any]]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    return _handle(list_commits, settings.token, settings.api_url, settings.timeout_seconds, target_owner, target_repo, sha, per_page)


@mcp.tool(name="github_get_file_content", description="Obtiene el contenido de un archivo del repo.")
def tool_get_file_content(
    path: str, ref: str | None = None, owner: str = "", repo: str = "",
) -> dict[str, Any]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    return _handle(get_file_content, settings.token, settings.api_url, settings.timeout_seconds, target_owner, target_repo, path, ref)


@mcp.tool(name="github_get_repo_info", description="Obtiene informacion del repositorio.")
def tool_get_repo_info(owner: str = "", repo: str = "") -> dict[str, Any]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    return _handle(get_repo_info, settings.token, settings.api_url, settings.timeout_seconds, target_owner, target_repo)


@mcp.tool(name="github_get_user_info", description="Obtiene informacion de un usuario de GitHub.")
def tool_get_user_info(username: str) -> dict[str, Any]:
    return _handle(get_user_info, settings.token, settings.api_url, settings.timeout_seconds, username)


@mcp.tool(name="github_list_pull_requests", description="Lista pull requests de un repositorio.")
def tool_list_pull_requests(
    state: str = "open", per_page: int = 30, owner: str = "", repo: str = "",
) -> list[dict[str, Any]]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    return _handle(list_pull_requests, settings.token, settings.api_url, settings.timeout_seconds, target_owner, target_repo, state, per_page)


@mcp.tool(name="github_get_pull_request_files", description="Obtiene los archivos modificados en un PR.")
def tool_get_pull_request_files(
    pull_number: int, owner: str = "", repo: str = "",
) -> list[dict[str, Any]]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    return _handle(get_pull_request_files, settings.token, settings.api_url, settings.timeout_seconds, target_owner, target_repo, pull_number)


@mcp.tool(name="github_create_branch", description="Crea una nueva branch desde una existente.")
def tool_create_branch(
    branch_name: str, from_branch: str = "main", owner: str = "", repo: str = "",
) -> dict[str, Any]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    return _handle(create_branch, settings.token, settings.api_url, settings.timeout_seconds, target_owner, target_repo, branch_name, from_branch)


@mcp.tool(name="github_get_issue_comments", description="Obtiene los comentarios de un issue.")
def tool_get_issue_comments(
    issue_number: int, per_page: int = 30, owner: str = "", repo: str = "",
) -> list[dict[str, Any]]:
    target_owner = owner or settings.owner
    target_repo = repo or settings.repo
    return _handle(get_issue_comments, settings.token, settings.api_url, settings.timeout_seconds, target_owner, target_repo, issue_number, per_page)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("github://api-endpoints")
def res_api_endpoints() -> str:
    return res.github_api_endpoints()


@mcp.resource("github://auth-guide")
def res_auth_guide() -> str:
    return res.github_authentication_guide()


@mcp.resource("github://issue-tips")
def res_issue_tips() -> str:
    return res.issue_management_tips()


@mcp.resource("github://pr-best-practices")
def res_pr_tips() -> str:
    return res.pull_request_best_practices()


@mcp.resource("github://rate-limits")
def res_rate_limits() -> str:
    return res.github_rate_limits()


@mcp.resource("github://configuration")
def res_config() -> str:
    return res.github_configuration()


@mcp.resource("github://common-workflows")
def res_workflows() -> str:
    return res.common_github_workflows()


@mcp.resource("github://error-codes")
def res_errors() -> str:
    return res.github_error_codes()


@mcp.resource("github://markdown-syntax")
def res_markdown() -> str:
    return res.github_markdown_syntax()


@mcp.resource("github://branch-strategy")
def res_branch_strategy() -> str:
    return res.github_branch_strategy()


@mcp.resource("github://security-tips")
def res_security() -> str:
    return res.github_security_tips()


@mcp.resource("github://release-guide")
def res_release() -> str:
    return res.github_release_guide()


@mcp.resource("github://examples/create-issue")
def res_example_issue() -> str:
    return res.example_create_issue()


@mcp.resource("github://examples/create-pr")
def res_example_pr() -> str:
    return res.example_create_pr()


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
