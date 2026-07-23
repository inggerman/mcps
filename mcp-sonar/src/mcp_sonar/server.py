"""
Servidor FastMCP para mcp-sonar.

Expone integración con SonarQube.
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

from mcp_sonar import __version__
from mcp_sonar.config import settings
from mcp_sonar.tools import (
    sonar_components_search,
    sonar_health,
    sonar_hotspots_search,
    sonar_issues_search,
    sonar_languages_list,
    sonar_measures_component,
    sonar_measures_history,
    sonar_project_create,
    sonar_project_delete,
    sonar_projects_search,
    sonar_qualitygates_list,
    sonar_qualitygates_status,
    sonar_qualityprofiles_list,
    sonar_rules_search,
    sonar_scan,
)
from mcp_sonar import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-sonar",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-sonar")
    logger.info(
        "mcp-sonar iniciando",
        version=__version__,
        project_path=str(settings.project_path),
    )
    yield
    logger.info("mcp-sonar detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-sonar",
    instructions=(
        "Servidor MCP para interactuar con SonarQube/SonarCloud. "
        "Úsalo para ejecutar escaneos de calidad (bugs, code smells, deuda técnica, cobertura)."
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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de Sonar.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="sonar_run_scan",
    description="Ejecuta 'sonar-scanner' en el proyecto actual y devuelve un resumen de calidad."
)
def tool_sonar_run_scan() -> dict[str, Any]:
    logger.info("sonar_run_scan llamado")
    return _handle(sonar_scan, settings.project_path, settings.host_url, settings.api_token)


@mcp.tool(name="sonar_components_search", description="Busca componentes en SonarQube.")
def tool_sonar_components_search(query: str) -> dict[str, Any]:
    return _handle(sonar_components_search, settings.host_url, settings.api_token, query)


@mcp.tool(name="sonar_issues_search", description="Busca issues en un proyecto.")
def tool_sonar_issues_search(project_key: str) -> dict[str, Any]:
    return _handle(sonar_issues_search, settings.host_url, settings.api_token, project_key)


@mcp.tool(name="sonar_measures_component", description="Obtiene medidas de un componente.")
def tool_sonar_measures_component(component: str, metric_keys: str) -> dict[str, Any]:
    return _handle(sonar_measures_component, settings.host_url, settings.api_token, component, metric_keys)


@mcp.tool(name="sonar_measures_history", description="Obtiene historico de medidas.")
def tool_sonar_measures_history(component: str, metrics: str) -> dict[str, Any]:
    return _handle(sonar_measures_history, settings.host_url, settings.api_token, component, metrics)


@mcp.tool(name="sonar_qualitygates_list", description="Lista quality gates.")
def tool_sonar_qualitygates_list() -> dict[str, Any]:
    return _handle(sonar_qualitygates_list, settings.host_url, settings.api_token)


@mcp.tool(name="sonar_qualitygates_status", description="Obtiene el estado del quality gate.")
def tool_sonar_qualitygates_status(project_key: str) -> dict[str, Any]:
    return _handle(sonar_qualitygates_status, settings.host_url, settings.api_token, project_key)


@mcp.tool(name="sonar_rules_search", description="Busca reglas en SonarQube.")
def tool_sonar_rules_search(language: str = "", q: str = "") -> dict[str, Any]:
    return _handle(sonar_rules_search, settings.host_url, settings.api_token, language, q)


@mcp.tool(name="sonar_languages_list", description="Lista lenguajes soportados.")
def tool_sonar_languages_list() -> dict[str, Any]:
    return _handle(sonar_languages_list, settings.host_url, settings.api_token)


@mcp.tool(name="sonar_projects_search", description="Busca proyectos en SonarQube.")
def tool_sonar_projects_search(q: str = "") -> dict[str, Any]:
    return _handle(sonar_projects_search, settings.host_url, settings.api_token, q)


@mcp.tool(name="sonar_project_create", description="Crea un proyecto en SonarQube.")
def tool_sonar_project_create(name: str, key: str) -> dict[str, Any]:
    return _handle(sonar_project_create, settings.host_url, settings.api_token, name, key)


@mcp.tool(name="sonar_project_delete", description="Elimina un proyecto en SonarQube.")
def tool_sonar_project_delete(key: str) -> dict[str, Any]:
    return _handle(sonar_project_delete, settings.host_url, settings.api_token, key)


@mcp.tool(name="sonar_hotspots_search", description="Busca hotspots de seguridad.")
def tool_sonar_hotspots_search(project_key: str) -> dict[str, Any]:
    return _handle(sonar_hotspots_search, settings.host_url, settings.api_token, project_key)


@mcp.tool(name="sonar_health", description="Verifica el estado de salud de SonarQube.")
def tool_sonar_health() -> dict[str, Any]:
    return _handle(sonar_health, settings.host_url, settings.api_token)


@mcp.tool(name="sonar_qualityprofiles_list", description="Lista quality profiles disponibles.")
def tool_sonar_qualityprofiles_list(language: str = "") -> dict[str, Any]:
    return _handle(sonar_qualityprofiles_list, settings.host_url, settings.api_token, language)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("sonar://configuration")
def res_config() -> str:
    return res.sonar_configuration()


@mcp.resource("sonar://basics")
def res_basics() -> str:
    return res.sonar_basics()


@mcp.resource("sonar://best-practices")
def res_best() -> str:
    return res.sonar_best_practices()


@mcp.resource("sonar://quick-reference")
def res_quick() -> str:
    return res.sonar_quick_reference()


@mcp.resource("sonar://error-codes")
def res_errors() -> str:
    return res.sonar_error_codes()


@mcp.resource("sonar://troubleshooting")
def res_trouble() -> str:
    return res.sonar_troubleshooting()


@mcp.resource("sonar://examples")
def res_examples() -> str:
    return res.sonar_examples()


@mcp.resource("sonar://quality-gates")
def res_qg() -> str:
    return res.sonar_quality_gates()


@mcp.resource("sonar://metrics")
def res_metrics() -> str:
    return res.sonar_metrics()


@mcp.resource("sonar://rules")
def res_rules() -> str:
    return res.sonar_rules()


@mcp.resource("sonar://scanner")
def res_scanner() -> str:
    return res.sonar_scanner()


@mcp.resource("sonar://issues")
def res_issues() -> str:
    return res.sonar_issues()


@mcp.resource("sonar://hotspots")
def res_hotspots() -> str:
    return res.sonar_hotspots()


@mcp.resource("sonar://ci-cd")
def res_cicd() -> str:
    return res.sonar_ci_cd()


@mcp.resource("sonar://quality-profiles")
def res_profiles() -> str:
    return res.sonar_quality_profiles()


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
