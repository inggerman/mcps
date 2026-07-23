"""
Servidor FastMCP para mcp-architecture.

Expone herramientas para análisis estructural de proyectos.
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

from mcp_architecture import __version__
from mcp_architecture.config import settings
from mcp_architecture.tools.arch_tools import (
    analyze_circular_deps,
    analyze_cohesion,
    analyze_coupling,
    analyze_dependencies,
    analyze_inheritance,
    analyze_layering,
    analyze_module_dependencies,
    analyze_solid_heuristics,
    count_classes_functions,
    detect_code_smells,
    find_entry_points,
    find_largest_files,
    generate_architecture_report,
    get_module_summary,
    get_project_tree,
)
from mcp_architecture import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-architecture",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Ciclo de vida del servidor de arquitectura."""
    structlog.contextvars.bind_contextvars(server_name="mcp-architecture")
    logger.info(
        "mcp-architecture iniciando",
        version=__version__,
        project_path=str(settings.project_path),
    )
    yield
    logger.info("mcp-architecture detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-architecture",
    instructions=(
        "Servidor MCP para analizar la arquitectura, dependencias y estructura de proyectos. "
        "Usa las herramientas para ver el árbol del proyecto o encontrar problemas arquitectónicos "
        "en archivos específicos usando AST."
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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de arquitectura.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="arch_get_project_tree",
    description="Retorna la estructura de carpetas y archivos del proyecto. Útil para entender la arquitectura macro.",
)
def tool_get_project_tree(max_depth: int = 3) -> str:
    logger.info("arch_get_project_tree llamado", depth=max_depth)
    return _handle(get_project_tree, settings.project_path, max_depth)


@mcp.tool(
    name="arch_analyze_dependencies",
    description="Usa AST para extraer todas las importaciones de un archivo .py y entender su acoplamiento.",
)
def tool_analyze_dependencies(target_file: str) -> dict[str, Any]:
    logger.info("arch_analyze_dependencies llamado", target_file=target_file)
    return _handle(analyze_dependencies, settings.project_path, target_file)


@mcp.tool(
    name="arch_check_solid_principles",
    description="Revisa un archivo buscando heurísticas como Clases Gigantes o demasiados argumentos, que violan SOLID.",
)
def tool_check_solid_principles(target_file: str) -> dict[str, Any]:
    logger.info("arch_check_solid_principles llamado", target_file=target_file)
    return _handle(analyze_solid_heuristics, settings.project_path, target_file)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="arch_analyze_circular_deps",
    description="Detecta dependencias circulares entre modulos. Parametros: target (directorio, default todo).",
)
def tool_analyze_circular_deps(target: str = "") -> dict[str, Any]:
    logger.info("arch_analyze_circular_deps llamado", target=target)
    return _handle(analyze_circular_deps, settings.project_path, target)


@mcp.tool(
    name="arch_analyze_layering",
    description="Analiza si el proyecto sigue una estructura por capas. Parametros: target (directorio, default todo).",
)
def tool_analyze_layering(target: str = "") -> dict[str, Any]:
    logger.info("arch_analyze_layering llamado", target=target)
    return _handle(analyze_layering, settings.project_path, target)


@mcp.tool(
    name="arch_find_entry_points",
    description="Encuentra puntos de entrada (main, app, __main__). Parametros: target (directorio, default todo).",
)
def tool_find_entry_points(target: str = "") -> list[dict[str, Any]]:
    logger.info("arch_find_entry_points llamado", target=target)
    return _handle(find_entry_points, settings.project_path, target)


@mcp.tool(
    name="arch_analyze_coupling",
    description="Analiza acoplamiento afferent/efferent entre modulos. Parametros: target (directorio, default todo).",
)
def tool_analyze_coupling(target: str = "") -> dict[str, Any]:
    logger.info("arch_analyze_coupling llamado", target=target)
    return _handle(analyze_coupling, settings.project_path, target)


@mcp.tool(
    name="arch_analyze_cohesion",
    description="Analiza cohesion (LCOM) de un archivo. Parametros: target_file (requerido).",
)
def tool_analyze_cohesion(target_file: str) -> dict[str, Any]:
    logger.info("arch_analyze_cohesion llamado", target_file=target_file)
    return _handle(analyze_cohesion, settings.project_path, target_file)


@mcp.tool(
    name="arch_count_classes_functions",
    description="Cuenta clases y funciones. Parametros: target (archivo o directorio, default todo).",
)
def tool_count_classes_functions(target: str = "") -> dict[str, Any]:
    logger.info("arch_count_classes_functions llamado", target=target)
    return _handle(count_classes_functions, settings.project_path, target)


@mcp.tool(
    name="arch_find_largest_files",
    description="Encuentra archivos Python mas grandes. Parametros: target (directorio), top_n (int, default 10).",
)
def tool_find_largest_files(target: str = "", top_n: int = 10) -> list[dict[str, Any]]:
    logger.info("arch_find_largest_files llamado", target=target, top_n=top_n)
    return _handle(find_largest_files, settings.project_path, target, top_n)


@mcp.tool(
    name="arch_analyze_inheritance",
    description="Analiza jerarquia de herencia. Parametros: target_file (requerido).",
)
def tool_analyze_inheritance(target_file: str) -> dict[str, Any]:
    logger.info("arch_analyze_inheritance llamado", target_file=target_file)
    return _handle(analyze_inheritance, settings.project_path, target_file)


@mcp.tool(
    name="arch_detect_code_smells",
    description="Detecta code smells en un archivo. Parametros: target_file (requerido).",
)
def tool_detect_code_smells(target_file: str) -> dict[str, Any]:
    logger.info("arch_detect_code_smells llamado", target_file=target_file)
    return _handle(detect_code_smells, settings.project_path, target_file)


@mcp.tool(
    name="arch_generate_report",
    description="Genera reporte arquitectonico completo. Parametros: target (directorio, default todo).",
)
def tool_generate_architecture_report(target: str = "") -> dict[str, Any]:
    logger.info("arch_generate_report llamado", target=target)
    return _handle(generate_architecture_report, settings.project_path, target)


@mcp.tool(
    name="arch_analyze_module_dependencies",
    description="Analiza dependencias internas vs externas. Parametros: target (directorio, default todo).",
)
def tool_analyze_module_dependencies(target: str = "") -> dict[str, Any]:
    logger.info("arch_analyze_module_dependencies llamado", target=target)
    return _handle(analyze_module_dependencies, settings.project_path, target)


@mcp.tool(
    name="arch_get_module_summary",
    description="Genera resumen rapido de metricas de un modulo. Parametros: target (directorio, default todo).",
)
def tool_get_module_summary(target: str = "") -> dict[str, Any]:
    logger.info("arch_get_module_summary llamado", target=target)
    return _handle(get_module_summary, settings.project_path, target)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("arch://configuration")
def res_config() -> str:
    return res.architecture_configuration()


@mcp.resource("arch://solid-principles")
def res_solid() -> str:
    return res.architecture_solid_principles()


@mcp.resource("arch://clean-architecture")
def res_clean() -> str:
    return res.architecture_clean_architecture()


@mcp.resource("arch://hexagonal")
def res_hex() -> str:
    return res.architecture_hexagonal()


@mcp.resource("arch://design-patterns")
def res_patterns() -> str:
    return res.architecture_design_patterns()


@mcp.resource("arch://anti-patterns")
def res_anti() -> str:
    return res.architecture_anti_patterns()


@mcp.resource("arch://quick-reference")
def res_quick() -> str:
    return res.architecture_quick_reference()


@mcp.resource("arch://error-codes")
def res_errors() -> str:
    return res.architecture_error_codes()


@mcp.resource("arch://troubleshooting")
def res_trouble() -> str:
    return res.architecture_troubleshooting()


@mcp.resource("arch://examples")
def res_examples() -> str:
    return res.architecture_examples()


@mcp.resource("arch://metrics")
def res_metrics() -> str:
    return res.architecture_metrics()


@mcp.resource("arch://refactoring")
def res_refactor() -> str:
    return res.architecture_refactoring()


@mcp.resource("arch://documentation")
def res_docs() -> str:
    return res.architecture_documentation()


@mcp.resource("arch://microservices")
def res_micro() -> str:
    return res.architecture_microservices()


@mcp.resource("arch://best-practices")
def res_best() -> str:
    return res.architecture_best_practices()


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
