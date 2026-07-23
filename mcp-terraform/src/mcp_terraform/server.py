"""
Servidor FastMCP para mcp-terraform.

Expone comandos Terraform.
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

from mcp_terraform import __version__
from mcp_terraform.config import settings
from mcp_terraform.tools import (
    tf_apply,
    tf_destroy,
    tf_fmt,
    tf_graph,
    tf_import,
    tf_init,
    tf_output,
    tf_plan,
    tf_run,
    tf_show,
    tf_state_list,
    tf_taint,
    tf_validate,
    tf_workspace_list,
    tf_workspace_select,
)
from mcp_terraform import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-terraform",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-terraform")
    logger.info(
        "mcp-terraform iniciando",
        version=__version__,
        project_path=str(settings.project_path),
    )
    yield
    logger.info("mcp-terraform detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-terraform",
    instructions=(
        "Servidor MCP para interactuar con Terraform. "
        "Úsalo para ejecutar `terraform init`, `plan`, `validate`."
    ),
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__, error=str(exc))
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de Terraform.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="tf_run_cmd",
    description="Ejecuta un comando Terraform en el proyecto. Provee los argumentos (ej. 'plan' o 'init')."
)
def tool_tf_run_cmd(args: str) -> dict[str, Any]:
    logger.info("tf_run_cmd llamado", args=args)
    return _handle(tf_run, settings.project_path, args)


@mcp.tool(name="tf_init", description="Ejecuta terraform init.")
def tool_tf_init(backend: bool = True, upgrade: bool = False) -> dict[str, Any]:
    return _handle(tf_init, settings.project_path, backend, upgrade)


@mcp.tool(name="tf_plan", description="Ejecuta terraform plan.")
def tool_tf_plan(destroy: bool = False, var_file: str | None = None) -> dict[str, Any]:
    return _handle(tf_plan, settings.project_path, destroy, var_file)


@mcp.tool(name="tf_validate", description="Ejecuta terraform validate.")
def tool_tf_validate() -> dict[str, Any]:
    return _handle(tf_validate, settings.project_path)


@mcp.tool(name="tf_apply", description="Ejecuta terraform apply.")
def tool_tf_apply(auto_approve: bool = False, var_file: str | None = None) -> dict[str, Any]:
    return _handle(tf_apply, settings.project_path, auto_approve, var_file)


@mcp.tool(name="tf_destroy", description="Ejecuta terraform destroy.")
def tool_tf_destroy(auto_approve: bool = False) -> dict[str, Any]:
    return _handle(tf_destroy, settings.project_path, auto_approve)


@mcp.tool(name="tf_fmt", description="Ejecuta terraform fmt.")
def tool_tf_fmt(check: bool = False, recursive: bool = True) -> dict[str, Any]:
    return _handle(tf_fmt, settings.project_path, check, recursive)


@mcp.tool(name="tf_show", description="Ejecuta terraform show.")
def tool_tf_show(plan_file: str = "tfplan") -> dict[str, Any]:
    return _handle(tf_show, settings.project_path, plan_file)


@mcp.tool(name="tf_output", description="Ejecuta terraform output.")
def tool_tf_output(json_format: bool = True) -> dict[str, Any]:
    return _handle(tf_output, settings.project_path, json_format)


@mcp.tool(name="tf_state_list", description="Lista recursos en el state.")
def tool_tf_state_list() -> dict[str, Any]:
    return _handle(tf_state_list, settings.project_path)


@mcp.tool(name="tf_workspace_list", description="Lista workspaces.")
def tool_tf_workspace_list() -> dict[str, Any]:
    return _handle(tf_workspace_list, settings.project_path)


@mcp.tool(name="tf_workspace_select", description="Selecciona un workspace.")
def tool_tf_workspace_select(workspace: str) -> dict[str, Any]:
    return _handle(tf_workspace_select, settings.project_path, workspace)


@mcp.tool(name="tf_import", description="Importa un recurso al state.")
def tool_tf_import(resource_addr: str, resource_id: str) -> dict[str, Any]:
    return _handle(tf_import, settings.project_path, resource_addr, resource_id)


@mcp.tool(name="tf_taint", description="Marca un recurso como tainted.")
def tool_tf_taint(resource_addr: str) -> dict[str, Any]:
    return _handle(tf_taint, settings.project_path, resource_addr)


@mcp.tool(name="tf_graph", description="Genera el grafo de dependencias.")
def tool_tf_graph(plan: bool = False) -> dict[str, Any]:
    return _handle(tf_graph, settings.project_path, plan)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("terraform://configuration")
def res_config() -> str:
    return res.terraform_configuration()


@mcp.resource("terraform://basics")
def res_basics() -> str:
    return res.terraform_basics()


@mcp.resource("terraform://best-practices")
def res_best() -> str:
    return res.terraform_best_practices()


@mcp.resource("terraform://quick-reference")
def res_quick() -> str:
    return res.terraform_quick_reference()


@mcp.resource("terraform://error-codes")
def res_errors() -> str:
    return res.terraform_error_codes()


@mcp.resource("terraform://troubleshooting")
def res_trouble() -> str:
    return res.terraform_troubleshooting()


@mcp.resource("terraform://examples")
def res_examples() -> str:
    return res.terraform_examples()


@mcp.resource("terraform://state-management")
def res_state() -> str:
    return res.terraform_state_management()


@mcp.resource("terraform://modules")
def res_modules() -> str:
    return res.terraform_modules()


@mcp.resource("terraform://variables")
def res_variables() -> str:
    return res.terraform_variables()


@mcp.resource("terraform://providers")
def res_providers() -> str:
    return res.terraform_providers()


@mcp.resource("terraform://workspaces")
def res_workspaces() -> str:
    return res.terraform_workspaces()


@mcp.resource("terraform://ci-cd")
def res_cicd() -> str:
    return res.terraform_ci_cd()


@mcp.resource("terraform://security")
def res_security() -> str:
    return res.terraform_security()


@mcp.resource("terraform://import")
def res_import() -> str:
    return res.terraform_import()


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
