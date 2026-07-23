"""
Servidor FastMCP para mcp-design-patterns.

Expone herramientas de validación de antipatrones y sugerencia de patrones.
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

from mcp_design_patterns import __version__
from mcp_design_patterns.config import settings
from mcp_design_patterns.tools.dp_tools import (
    analyze_code_patterns,
    analyze_project_patterns,
    analyze_solid,
    compare_patterns,
    detect_code_smells,
    export_pattern_catalog,
    generate_pattern_code,
    generate_pattern_test,
    get_pattern_examples,
    get_pattern_info,
    get_pattern_stats,
    list_patterns,
    suggest_design_pattern,
    suggest_refactoring,
    validate_pattern_usage,
)
from mcp_design_patterns import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-design-patterns",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-design-patterns")
    logger.info(
        "mcp-design-patterns iniciando",
        version=__version__,
        project_path=str(settings.project_path),
    )
    yield
    logger.info("mcp-design-patterns detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-design-patterns",
    instructions=(
        "Servidor MCP para auditar patrones de diseño de software. "
        "Permite escanear archivos en busca de God Objects, métodos muy largos, y sugerir implementaciones GoF/SOLID."
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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de DP.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="dp_analyze_code_patterns",
    description="Analiza un archivo Python (.py) para detectar posibles antipatrones como God Objects o Long Methods.",
)
def tool_analyze_code_patterns(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("dp_analyze_code_patterns llamado", file=filename)
    return _handle(analyze_code_patterns, file_path)


@mcp.tool(
    name="dp_suggest_pattern",
    description="Sugiere un patrón de diseño (GoF) basado en la descripción del problema de software a resolver.",
)
def tool_suggest_pattern(problem_description: str) -> dict[str, str]:
    logger.info("dp_suggest_pattern llamado")
    return _handle(suggest_design_pattern, problem_description)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="dp_list_patterns",
    description="Lista patrones GoF por categoria. Parametros: category (opcional: creational/structural/behavioral).",
)
def tool_list_patterns(category: str = "") -> list[dict[str, str]]:
    logger.info("dp_list_patterns llamado", category=category)
    return _handle(list_patterns, category)


@mcp.tool(
    name="dp_generate_pattern_code",
    description="Genera codigo de ejemplo para un patron. Parametros: pattern_name.",
)
def tool_generate_pattern_code(pattern_name: str) -> str:
    logger.info("dp_generate_pattern_code llamado", pattern=pattern_name)
    return _handle(generate_pattern_code, pattern_name)


@mcp.tool(
    name="dp_analyze_solid",
    description="Analiza un archivo Python en busca de violaciones SOLID. Parametros: filename.",
)
def tool_analyze_solid(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("dp_analyze_solid llamado", file=filename)
    return _handle(analyze_solid, file_path)


@mcp.tool(
    name="dp_detect_code_smells",
    description="Detecta code smells en un archivo Python. Parametros: filename.",
)
def tool_detect_code_smells(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("dp_detect_code_smells llamado", file=filename)
    return _handle(detect_code_smells, file_path)


@mcp.tool(
    name="dp_suggest_refactoring",
    description="Sugiere refactorings basados en el analisis del archivo. Parametros: filename.",
)
def tool_suggest_refactoring(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("dp_suggest_refactoring llamado", file=filename)
    return _handle(suggest_refactoring, file_path)


@mcp.tool(
    name="dp_analyze_project_patterns",
    description="Analiza todos los archivos Python del proyecto en busca de antipatrones.",
)
def tool_analyze_project_patterns() -> dict[str, Any]:
    logger.info("dp_analyze_project_patterns llamado")
    return _handle(analyze_project_patterns, settings.project_path)


@mcp.tool(
    name="dp_get_pattern_info",
    description="Retorna informacion detallada de un patron. Parametros: pattern_name.",
)
def tool_get_pattern_info(pattern_name: str) -> dict[str, str]:
    logger.info("dp_get_pattern_info llamado", pattern=pattern_name)
    return _handle(get_pattern_info, pattern_name)


@mcp.tool(
    name="dp_compare_patterns",
    description="Compara dos patrones de diseno. Parametros: pattern_a, pattern_b.",
)
def tool_compare_patterns(pattern_a: str, pattern_b: str) -> dict[str, Any]:
    logger.info("dp_compare_patterns llamado", a=pattern_a, b=pattern_b)
    return _handle(compare_patterns, pattern_a, pattern_b)


@mcp.tool(
    name="dp_generate_pattern_test",
    description="Genera un test basico para un patron. Parametros: pattern_name.",
)
def tool_generate_pattern_test(pattern_name: str) -> str:
    logger.info("dp_generate_pattern_test llamado", pattern=pattern_name)
    return _handle(generate_pattern_test, pattern_name)


@mcp.tool(
    name="dp_export_pattern_catalog",
    description="Exporta el catalogo completo de patrones.",
)
def tool_export_pattern_catalog() -> dict[str, Any]:
    logger.info("dp_export_pattern_catalog llamado")
    return _handle(export_pattern_catalog)


@mcp.tool(
    name="dp_get_pattern_stats",
    description="Retorna estadisticas del catalogo de patrones.",
)
def tool_get_pattern_stats() -> dict[str, Any]:
    logger.info("dp_get_pattern_stats llamado")
    return _handle(get_pattern_stats)


@mcp.tool(
    name="dp_get_pattern_examples",
    description="Retorna ejemplos de uso de un patron. Parametros: pattern_name.",
)
def tool_get_pattern_examples(pattern_name: str) -> dict[str, Any]:
    logger.info("dp_get_pattern_examples llamado", pattern=pattern_name)
    return _handle(get_pattern_examples, pattern_name)


@mcp.tool(
    name="dp_validate_pattern_usage",
    description="Valida si un patron esta correctamente implementado en un archivo. Parametros: filename, pattern_name.",
)
def tool_validate_pattern_usage(filename: str, pattern_name: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("dp_validate_pattern_usage llamado", file=filename, pattern=pattern_name)
    return _handle(validate_pattern_usage, file_path, pattern_name)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("dp://configuration")
def res_config() -> str:
    return res.dp_configuration()


@mcp.resource("dp://gof-catalog")
def res_gof() -> str:
    return res.dp_gof_catalog()


@mcp.resource("dp://solid-principles")
def res_solid() -> str:
    return res.dp_solid_principles()


@mcp.resource("dp://anti-patterns")
def res_anti() -> str:
    return res.dp_anti_patterns()


@mcp.resource("dp://quick-reference")
def res_quick() -> str:
    return res.dp_quick_reference()


@mcp.resource("dp://error-codes")
def res_errors() -> str:
    return res.dp_error_codes()


@mcp.resource("dp://troubleshooting")
def res_trouble() -> str:
    return res.dp_troubleshooting()


@mcp.resource("dp://examples")
def res_examples() -> str:
    return res.dp_examples()


@mcp.resource("dp://refactoring-guide")
def res_refactor() -> str:
    return res.dp_refactoring_guide()


@mcp.resource("dp://code-smells")
def res_smells() -> str:
    return res.dp_code_smells()


@mcp.resource("dp://pattern-relationships")
def res_relations() -> str:
    return res.dp_pattern_relationships()


@mcp.resource("dp://python-patterns")
def res_python() -> str:
    return res.dp_python_patterns()


@mcp.resource("dp://testing-patterns")
def res_testing() -> str:
    return res.dp_testing_patterns()


@mcp.resource("dp://ddd-patterns")
def res_ddd() -> str:
    return res.dp_ddd_patterns()


@mcp.resource("dp://microservice-patterns")
def res_micro() -> str:
    return res.dp_microservice_patterns()


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
