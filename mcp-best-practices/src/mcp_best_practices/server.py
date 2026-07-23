"""
Servidor FastMCP para mcp-best-practices.

Expone herramientas de documentación retroactiva continua.
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

from mcp_best_practices import __version__
from mcp_best_practices.config import settings
from mcp_best_practices.tools.bp_tools import (
    check_env_consistency,
    check_test_coverage,
    count_lines_of_code,
    generate_api_docs,
    generate_architecture_doc,
    generate_changelog,
    generate_dependencies_doc,
    generate_health_report,
    generate_readme,
    get_project_summary,
    list_project_files,
    scan_code_quality,
    update_project_state,
    update_servers_reference,
    validate_dockerfiles,
)
from mcp_best_practices import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-best-practices",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-best-practices")
    logger.info(
        "mcp-best-practices iniciando",
        version=__version__,
        docs_path=str(settings.docs_path),
    )
    yield
    logger.info("mcp-best-practices detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-best-practices",
    instructions=(
        "Servidor MCP para asegurar las Mejores Prácticas documentales. "
        "Úsalo para generar/actualizar la documentación retroactiva del estado del proyecto."
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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de BP.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="bp_update_project_state",
    description="Genera o actualiza el archivo docs/project-state.md escaneando la estructura actual del proyecto.",
)
def tool_update_project_state() -> dict[str, Any]:
    logger.info("bp_update_project_state llamado")
    return _handle(update_project_state, settings.project_path, settings.docs_path)


@mcp.tool(
    name="bp_update_servers_reference",
    description="Genera o actualiza docs/servers-reference.md leyendo claude_desktop_config.json de la raíz.",
)
def tool_update_servers_reference() -> dict[str, Any]:
    logger.info("bp_update_servers_reference llamado")
    return _handle(update_servers_reference, settings.project_path, settings.docs_path)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="bp_generate_architecture_doc",
    description="Genera docs/architecture.md con un diagrama de la arquitectura.",
)
def tool_generate_architecture_doc() -> dict[str, Any]:
    logger.info("bp_generate_architecture_doc llamado")
    return _handle(generate_architecture_doc, settings.project_path, settings.docs_path)


@mcp.tool(
    name="bp_generate_dependencies_doc",
    description="Genera docs/dependencies.md con un mapa de dependencias.",
)
def tool_generate_dependencies_doc() -> dict[str, Any]:
    logger.info("bp_generate_dependencies_doc llamado")
    return _handle(generate_dependencies_doc, settings.project_path, settings.docs_path)


@mcp.tool(
    name="bp_scan_code_quality",
    description="Escanea calidad basica del codigo. Parametros: target (directorio, opcional).",
)
def tool_scan_code_quality(target: str = "") -> dict[str, Any]:
    logger.info("bp_scan_code_quality llamado", target=target)
    return _handle(scan_code_quality, settings.project_path, target)


@mcp.tool(
    name="bp_generate_readme",
    description="Genera un README.md basico para el proyecto.",
)
def tool_generate_readme() -> dict[str, Any]:
    logger.info("bp_generate_readme llamado")
    return _handle(generate_readme, settings.project_path, settings.docs_path)


@mcp.tool(
    name="bp_check_env_consistency",
    description="Verifica consistencia de variables .env entre servidores.",
)
def tool_check_env_consistency() -> dict[str, Any]:
    logger.info("bp_check_env_consistency llamado")
    return _handle(check_env_consistency, settings.project_path)


@mcp.tool(
    name="bp_generate_changelog",
    description="Genera un CHANGELOG.md basico.",
)
def tool_generate_changelog() -> dict[str, Any]:
    logger.info("bp_generate_changelog llamado")
    return _handle(generate_changelog, settings.project_path, settings.docs_path)


@mcp.tool(
    name="bp_validate_dockerfiles",
    description="Valida que todos los Dockerfiles tengan configuracion estandar.",
)
def tool_validate_dockerfiles() -> dict[str, Any]:
    logger.info("bp_validate_dockerfiles llamado")
    return _handle(validate_dockerfiles, settings.project_path)


@mcp.tool(
    name="bp_count_lines_of_code",
    description="Cuenta lineas de codigo por lenguaje. Parametros: target (directorio, opcional).",
)
def tool_count_lines_of_code(target: str = "") -> dict[str, Any]:
    logger.info("bp_count_lines_of_code llamado", target=target)
    return _handle(count_lines_of_code, settings.project_path, target)


@mcp.tool(
    name="bp_generate_api_docs",
    description="Genera documentacion de API de los servidores MCP.",
)
def tool_generate_api_docs() -> dict[str, Any]:
    logger.info("bp_generate_api_docs llamado")
    return _handle(generate_api_docs, settings.project_path, settings.docs_path)


@mcp.tool(
    name="bp_check_test_coverage",
    description="Verifica cobertura basica de tests por servidor.",
)
def tool_check_test_coverage() -> dict[str, Any]:
    logger.info("bp_check_test_coverage llamado")
    return _handle(check_test_coverage, settings.project_path)


@mcp.tool(
    name="bp_generate_health_report",
    description="Genera un reporte de salud del proyecto.",
)
def tool_generate_health_report() -> dict[str, Any]:
    logger.info("bp_generate_health_report llamado")
    return _handle(generate_health_report, settings.project_path)


@mcp.tool(
    name="bp_list_project_files",
    description="Lista archivos del proyecto. Parametros: pattern (glob, default *.py).",
)
def tool_list_project_files(pattern: str = "*.py") -> list[dict[str, Any]]:
    logger.info("bp_list_project_files llamado", pattern=pattern)
    return _handle(list_project_files, settings.project_path, pattern)


@mcp.tool(
    name="bp_get_project_summary",
    description="Genera un resumen rapido del proyecto.",
)
def tool_get_project_summary() -> dict[str, Any]:
    logger.info("bp_get_project_summary llamado")
    return _handle(get_project_summary, settings.project_path)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("bp://configuration")
def res_config() -> str:
    return res.bp_configuration()


@mcp.resource("bp://documentation-guide")
def res_doc_guide() -> str:
    return res.bp_documentation_guide()


@mcp.resource("bp://naming-conventions")
def res_naming() -> str:
    return res.bp_naming_conventions()


@mcp.resource("bp://project-structure")
def res_structure() -> str:
    return res.bp_project_structure()


@mcp.resource("bp://quick-reference")
def res_quick() -> str:
    return res.bp_quick_reference()


@mcp.resource("bp://error-codes")
def res_errors() -> str:
    return res.bp_error_codes()


@mcp.resource("bp://troubleshooting")
def res_trouble() -> str:
    return res.bp_troubleshooting()


@mcp.resource("bp://examples")
def res_examples() -> str:
    return res.bp_examples()


@mcp.resource("bp://code-standards")
def res_code() -> str:
    return res.bp_code_standards()


@mcp.resource("bp://docker-standards")
def res_docker() -> str:
    return res.bp_docker_standards()


@mcp.resource("bp://testing-standards")
def res_testing() -> str:
    return res.bp_testing_standards()


@mcp.resource("bp://git-workflow")
def res_git() -> str:
    return res.bp_git_workflow()


@mcp.resource("bp://security-practices")
def res_security() -> str:
    return res.bp_security_practices()


@mcp.resource("bp://performance-tips")
def res_perf() -> str:
    return res.bp_performance_tips()


@mcp.resource("bp://deployment-guide")
def res_deploy() -> str:
    return res.bp_deployment_guide()


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
