"""
Servidor FastMCP para mcp-snyk.

Expone integración con Snyk para SAST/SCA.
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

from mcp_snyk import __version__
from mcp_snyk.config import settings
from mcp_snyk.tools import (
    snyk_auth,
    snyk_code_test,
    snyk_container_test,
    snyk_dependency_tree,
    snyk_iac_test,
    snyk_ignore,
    snyk_log4shell,
    snyk_monitor,
    snyk_org_list,
    snyk_policy,
    snyk_projects,
    snyk_test,
    snyk_test_file,
    snyk_test_severity_filter,
    snyk_wizard,
)
from mcp_snyk import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-snyk",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-snyk")
    logger.info(
        "mcp-snyk iniciando",
        version=__version__,
        project_path=str(settings.project_path),
    )
    yield
    logger.info("mcp-snyk detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-snyk",
    instructions=(
        "Servidor MCP para interactuar con Snyk. "
        "Úsalo para ejecutar escaneos de vulnerabilidades en dependencias y código."
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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de Snyk.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="snyk_run_test",
    description="Ejecuta 'snyk test' en el proyecto actual y devuelve un reporte de vulnerabilidades."
)
def tool_snyk_run_test() -> dict[str, Any]:
    logger.info("snyk_run_test llamado")
    return _handle(snyk_test, settings.project_path, settings.api_token)


@mcp.tool(name="snyk_auth", description="Autentica con Snyk usando el API token.")
def tool_snyk_auth() -> dict[str, Any]:
    return _handle(snyk_auth, settings.api_token)


@mcp.tool(name="snyk_monitor", description="Ejecuta snyk monitor para registro continuo.")
def tool_snyk_monitor() -> dict[str, Any]:
    return _handle(snyk_monitor, settings.project_path, settings.api_token)


@mcp.tool(name="snyk_code_test", description="Ejecuta snyk code test (SAST).")
def tool_snyk_code_test() -> dict[str, Any]:
    return _handle(snyk_code_test, settings.project_path, settings.api_token)


@mcp.tool(name="snyk_iac_test", description="Ejecuta snyk iac test para Terraform/CloudFormation.")
def tool_snyk_iac_test() -> dict[str, Any]:
    return _handle(snyk_iac_test, settings.project_path, settings.api_token)


@mcp.tool(name="snyk_container_test", description="Ejecuta snyk container test para imagenes Docker.")
def tool_snyk_container_test(image: str) -> dict[str, Any]:
    return _handle(snyk_container_test, image, settings.api_token)


@mcp.tool(name="snyk_ignore", description="Ignora una vulnerabilidad por issue ID.")
def tool_snyk_ignore(issue_id: str) -> dict[str, Any]:
    return _handle(snyk_ignore, settings.project_path, issue_id, settings.api_token)


@mcp.tool(name="snyk_policy", description="Muestra el .snyk policy file.")
def tool_snyk_policy() -> dict[str, Any]:
    return _handle(snyk_policy, settings.project_path, settings.api_token)


@mcp.tool(name="snyk_projects", description="Lista proyectos de Snyk.")
def tool_snyk_projects() -> dict[str, Any]:
    return _handle(snyk_projects, settings.api_token)


@mcp.tool(name="snyk_org_list", description="Lista organizaciones de Snyk.")
def tool_snyk_org_list() -> dict[str, Any]:
    return _handle(snyk_org_list, settings.api_token)


@mcp.tool(name="snyk_test_severity_filter", description="Ejecuta snyk test filtrando por severidad.")
def tool_snyk_test_severity_filter(severity: str) -> dict[str, Any]:
    return _handle(snyk_test_severity_filter, settings.project_path, severity, settings.api_token)


@mcp.tool(name="snyk_test_file", description="Ejecuta snyk test en un archivo especifico.")
def tool_snyk_test_file(file_path: str) -> dict[str, Any]:
    from pathlib import Path
    return _handle(snyk_test_file, Path(file_path), settings.api_token)


@mcp.tool(name="snyk_dependency_tree", description="Muestra el arbol de dependencias.")
def tool_snyk_dependency_tree() -> dict[str, Any]:
    return _handle(snyk_dependency_tree, settings.project_path, settings.api_token)


@mcp.tool(name="snyk_wizard", description="Ejecuta snyk wizard para crear .snyk policy file.")
def tool_snyk_wizard() -> dict[str, Any]:
    return _handle(snyk_wizard, settings.project_path, settings.api_token)


@mcp.tool(name="snyk_log4shell", description="Ejecuta snyk test para detectar Log4Shell.")
def tool_snyk_log4shell() -> dict[str, Any]:
    return _handle(snyk_log4shell, settings.project_path, settings.api_token)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("snyk://configuration")
def res_config() -> str:
    return res.snyk_configuration()


@mcp.resource("snyk://basics")
def res_basics() -> str:
    return res.snyk_basics()


@mcp.resource("snyk://best-practices")
def res_best() -> str:
    return res.snyk_best_practices()


@mcp.resource("snyk://quick-reference")
def res_quick() -> str:
    return res.snyk_quick_reference()


@mcp.resource("snyk://error-codes")
def res_errors() -> str:
    return res.snyk_error_codes()


@mcp.resource("snyk://troubleshooting")
def res_trouble() -> str:
    return res.snyk_troubleshooting()


@mcp.resource("snyk://examples")
def res_examples() -> str:
    return res.snyk_examples()


@mcp.resource("snyk://oss-guide")
def res_oss() -> str:
    return res.snyk_oss_guide()


@mcp.resource("snyk://code-guide")
def res_code() -> str:
    return res.snyk_code_guide()


@mcp.resource("snyk://iac-guide")
def res_iac() -> str:
    return res.snyk_iac_guide()


@mcp.resource("snyk://container-guide")
def res_container() -> str:
    return res.snyk_container_guide()


@mcp.resource("snyk://severity-guide")
def res_severity() -> str:
    return res.snyk_severity_guide()


@mcp.resource("snyk://policy-guide")
def res_policy() -> str:
    return res.snyk_policy_guide()


@mcp.resource("snyk://ci-cd")
def res_cicd() -> str:
    return res.snyk_ci_cd()


@mcp.resource("snyk://api-guide")
def res_api() -> str:
    return res.snyk_api_guide()


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
