"""
Servidor FastMCP para mcp-covaf.

Tools específicas para los motores COVAF: Java (Cartas + Oficios PLD),
Python (DataRefineryIA), Vue (Alternativos Front), Derechos, y transversales
(lifecycle, templates, reportes).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import MCPError as SdkMcpError
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_covaf import __version__
from mcp_covaf.config import settings
from mcp_covaf.tools import (
    back_analyze_cartas_pipeline,
    back_analyze_oficios_pipeline,
    back_get_endpoint_map,
    back_list_extraction_strategies,
    back_list_quality_gates,
    back_list_templates,
    back_search_code,
    front_get_mfe_config,
    front_list_modules,
    front_list_routes,
    front_list_services,
    front_search_code,
    ia_analyze_extraction_output,
    ia_get_plugin_schema,
    ia_list_eval_tests,
    ia_list_pipeline_tiers,
    ia_list_plugins,
    ia_search_code,
    lifecycle_get_dependencies,
    lifecycle_get_deploy_manifests,
    lifecycle_get_git_info,
    lifecycle_get_status,
    lifecycle_get_test_command,
    lifecycle_list_components,
    report_format_for_team,
    report_generate_summary,
    report_get_health,
    report_list_findings,
    template_get_schema,
    template_list,
    template_scaffold_new,
    template_validate,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-covaf",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-covaf")
    logger.info(
        "mcp-covaf iniciando",
        version=__version__,
        workspace=str(settings.workspace_path),
    )
    yield
    logger.info("mcp-covaf detenido")


# ---------------------------------------------------------------------------
# FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-covaf",
    instructions=(
        "Servidor MCP para COVAF. Tools específicas para los motores Java "
        "(Cartas de Confirmación + Oficios PLD), Python (DataRefineryIA), "
        "Vue (Alternativos Front) y transversales (lifecycle, templates, reportes)."
    ),
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=getattr(fn, "__name__", "?"), error=str(exc))
        raise SdkMcpError(code=-32603, message=f"Error interno: {exc}") from exc


# ---------------------------------------------------------------------------
# Tools — Motor Java (back)
# ---------------------------------------------------------------------------

@mcp.tool(
    name="back_list_extraction_strategies",
    description="Lista las estrategias de extracción del motor Java COVAF (REGEX, KEY_WORD, TABLE, etc.).",
)
def tool_back_list_extraction_strategies() -> dict[str, Any]:
    return _handle(back_list_extraction_strategies, settings.workspace_path, settings.java_back_path)


@mcp.tool(
    name="back_list_templates",
    description="Lista los templates de extracción del motor Java COVAF (Cartas, Oficios PLD).",
)
def tool_back_list_templates() -> dict[str, Any]:
    return _handle(back_list_templates, settings.workspace_path, settings.java_back_path)


@mcp.tool(
    name="back_list_quality_gates",
    description="Lista los quality gates del motor Java COVAF (ExtractionQualityEvaluator, etc.).",
)
def tool_back_list_quality_gates() -> dict[str, Any]:
    return _handle(back_list_quality_gates, settings.workspace_path, settings.java_back_path)


@mcp.tool(
    name="back_search_code",
    description="Busca un patrón (regex) en el código Java del motor COVAF.",
)
def tool_back_search_code(pattern: str, max_results: int = 20) -> dict[str, Any]:
    return _handle(back_search_code, settings.workspace_path, settings.java_back_path, pattern, max_results)


@mcp.tool(
    name="back_get_endpoint_map",
    description="Retorna el mapa de endpoints REST del motor Java COVAF.",
)
def tool_back_get_endpoint_map() -> dict[str, Any]:
    return _handle(back_get_endpoint_map, settings.workspace_path, settings.java_back_path)


@mcp.tool(
    name="back_analyze_oficios_pipeline",
    description="Analiza el pipeline de extracción de Oficios PLD del motor Java.",
)
def tool_back_analyze_oficios_pipeline() -> dict[str, Any]:
    return _handle(back_analyze_oficios_pipeline, settings.workspace_path, settings.java_back_path)


@mcp.tool(
    name="back_analyze_cartas_pipeline",
    description="Analiza el pipeline de extracción de Cartas de Confirmación del motor Java.",
)
def tool_back_analyze_cartas_pipeline() -> dict[str, Any]:
    return _handle(back_analyze_cartas_pipeline, settings.workspace_path, settings.java_back_path)


# ---------------------------------------------------------------------------
# Tools — Motor Python (ia)
# ---------------------------------------------------------------------------

@mcp.tool(
    name="ia_list_plugins",
    description="Lista los plugins del motor Python DataRefineryIA (prospectos_cnbv, cartas_confirmacion).",
)
def tool_ia_list_plugins() -> dict[str, Any]:
    return _handle(ia_list_plugins, settings.workspace_path, settings.python_api_path)


@mcp.tool(
    name="ia_list_pipeline_tiers",
    description="Lista los tiers del pipeline de extracción del motor Python (Tier 1, 2, 3, merge, validate).",
)
def tool_ia_list_pipeline_tiers() -> dict[str, Any]:
    return _handle(ia_list_pipeline_tiers, settings.workspace_path, settings.python_api_path)


@mcp.tool(
    name="ia_get_plugin_schema",
    description="Obtiene el schema de campos de un plugin específico del motor Python.",
)
def tool_ia_get_plugin_schema(plugin_name: str) -> dict[str, Any]:
    return _handle(ia_get_plugin_schema, settings.workspace_path, settings.python_api_path, plugin_name)


@mcp.tool(
    name="ia_search_code",
    description="Busca un patrón (regex) en el código Python del motor DataRefineryIA.",
)
def tool_ia_search_code(pattern: str, max_results: int = 20) -> dict[str, Any]:
    return _handle(ia_search_code, settings.workspace_path, settings.python_api_path, pattern, max_results)


@mcp.tool(
    name="ia_analyze_extraction_output",
    description="Analiza un JSON de salida de extracción para detectar anomalías (campos vacíos, confidence baja, etc.).",
)
def tool_ia_analyze_extraction_output(output_json: str) -> dict[str, Any]:
    return _handle(ia_analyze_extraction_output, settings.workspace_path, settings.python_api_path, output_json)


@mcp.tool(
    name="ia_list_eval_tests",
    description="Lista los tests de evaluación del motor Python DataRefineryIA.",
)
def tool_ia_list_eval_tests() -> dict[str, Any]:
    return _handle(ia_list_eval_tests, settings.workspace_path, settings.python_api_path)


# ---------------------------------------------------------------------------
# Tools — Frontend (front)
# ---------------------------------------------------------------------------

@mcp.tool(
    name="front_list_routes",
    description="Lista las rutas del frontend Vue CovafAlternativosFront.",
)
def tool_front_list_routes() -> dict[str, Any]:
    return _handle(front_list_routes, settings.workspace_path, settings.frontend_path)


@mcp.tool(
    name="front_list_modules",
    description="Lista los módulos/páginas del frontend Vue.",
)
def tool_front_list_modules() -> dict[str, Any]:
    return _handle(front_list_modules, settings.workspace_path, settings.frontend_path)


@mcp.tool(
    name="front_list_services",
    description="Lista los servicios API del frontend Vue.",
)
def tool_front_list_services() -> dict[str, Any]:
    return _handle(front_list_services, settings.workspace_path, settings.frontend_path)


@mcp.tool(
    name="front_search_code",
    description="Busca un patrón (regex) en el código del frontend Vue COVAF.",
)
def tool_front_search_code(pattern: str, max_results: int = 20) -> dict[str, Any]:
    return _handle(front_search_code, settings.workspace_path, settings.frontend_path, pattern, max_results)


@mcp.tool(
    name="front_get_mfe_config",
    description="Retorna la configuración de Module Federation del frontend Vue.",
)
def tool_front_get_mfe_config() -> dict[str, Any]:
    return _handle(front_get_mfe_config, settings.workspace_path, settings.frontend_path)


# ---------------------------------------------------------------------------
# Tools — Lifecycle
# ---------------------------------------------------------------------------

@mcp.tool(
    name="lifecycle_list_components",
    description="Lista todos los componentes COVAF con su metadata (Java, Python, Vue, Derechos).",
)
def tool_lifecycle_list_components() -> dict[str, Any]:
    return _handle(lifecycle_list_components, settings.workspace_path)


@mcp.tool(
    name="lifecycle_get_status",
    description="Retorna el estado consolidado de todos los componentes COVAF (Git, dirty files).",
)
def tool_lifecycle_get_status() -> dict[str, Any]:
    return _handle(lifecycle_get_status, settings.workspace_path)


@mcp.tool(
    name="lifecycle_get_git_info",
    description="Obtiene información de Git (HEAD, branch, dirty) para un componente COVAF.",
)
def tool_lifecycle_get_git_info(component_key: str) -> dict[str, Any]:
    return _handle(lifecycle_get_git_info, settings.workspace_path, component_key)


@mcp.tool(
    name="lifecycle_get_dependencies",
    description="Obtiene las dependencias clave de un componente COVAF (pom.xml, requirements.txt, package.json).",
)
def tool_lifecycle_get_dependencies(component_key: str) -> dict[str, Any]:
    return _handle(lifecycle_get_dependencies, settings.workspace_path, component_key)


@mcp.tool(
    name="lifecycle_get_test_command",
    description="Retorna el comando de test y build para un componente COVAF.",
)
def tool_lifecycle_get_test_command(component_key: str) -> dict[str, Any]:
    return _handle(lifecycle_get_test_command, settings.workspace_path, component_key)


@mcp.tool(
    name="lifecycle_get_deploy_manifests",
    description="Lista los manifests de despliegue de un componente COVAF (Dockerfile, compose, buildspec).",
)
def tool_lifecycle_get_deploy_manifests(component_key: str) -> dict[str, Any]:
    return _handle(lifecycle_get_deploy_manifests, settings.workspace_path, component_key)


# ---------------------------------------------------------------------------
# Tools — Reportes
# ---------------------------------------------------------------------------

@mcp.tool(
    name="report_get_health",
    description="Retorna el estado de salud documentado de COVAF desde STATE.md.",
)
def tool_report_get_health() -> dict[str, Any]:
    return _handle(report_get_health, settings.workspace_path, settings.docs_path)


@mcp.tool(
    name="report_list_findings",
    description="Lista los hallazgos de seguridad documentados de COVAF.",
)
def tool_report_list_findings() -> dict[str, Any]:
    return _handle(report_list_findings, settings.workspace_path, settings.docs_path)


@mcp.tool(
    name="report_generate_summary",
    description="Genera un resumen ejecutivo del estado de COVAF o un componente.",
)
def tool_report_generate_summary(component_key: str | None = None) -> dict[str, Any]:
    return _handle(report_generate_summary, settings.workspace_path, settings.docs_path, component_key)


@mcp.tool(
    name="report_format_for_team",
    description="Formatea un reporte para envío al equipo COVAF (status, security, lifecycle).",
)
def tool_report_format_for_team(
    report_type: str = "status",
    component_key: str | None = None,
) -> dict[str, Any]:
    return _handle(
        report_format_for_team,
        settings.workspace_path,
        settings.docs_path,
        report_type,
        component_key,
    )


# ---------------------------------------------------------------------------
# Tools — Templates
# ---------------------------------------------------------------------------

@mcp.tool(
    name="template_list",
    description="Lista los templates de extracción disponibles en COVAF.",
)
def tool_template_list() -> dict[str, Any]:
    return _handle(template_list, settings.workspace_path, settings.docs_path)


@mcp.tool(
    name="template_get_schema",
    description="Obtiene el schema completo de un template específico.",
)
def tool_template_get_schema(template_name: str) -> dict[str, Any]:
    return _handle(template_get_schema, template_name)


@mcp.tool(
    name="template_validate",
    description="Valida un JSON de datos contra el schema de un template.",
)
def tool_template_validate(template_name: str, data_json: str) -> dict[str, Any]:
    return _handle(template_validate, template_name, data_json)


@mcp.tool(
    name="template_scaffold_new",
    description="Genera un scaffold de nuevo plugin para el motor Python DataRefineryIA.",
)
def tool_template_scaffold_new(
    plugin_name: str,
    domain_description: str = "",
) -> dict[str, Any]:
    return _handle(
        template_scaffold_new,
        settings.workspace_path,
        settings.python_api_path,
        plugin_name,
        domain_description,
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
