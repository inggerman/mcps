"""
Servidor FastMCP para mcp-code-quality.

Expone herramientas de validación de código estático y testing.
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

from mcp_code_quality import __version__
from mcp_code_quality.config import settings
from mcp_code_quality.tools.quality_tools import (
    analyze_dependencies,
    audit_dependencies,
    check_complexity,
    check_coverage,
    check_dependencies_versions,
    check_imports,
    count_lines,
    find_dead_code,
    find_todos,
    generate_quality_report,
    run_format,
    run_lint,
    run_security_scan,
    run_tests,
    run_type_check,
)
from mcp_code_quality import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-code-quality",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Ciclo de vida del servidor de calidad."""
    structlog.contextvars.bind_contextvars(server_name="mcp-code-quality")
    logger.info(
        "mcp-code-quality iniciando",
        version=__version__,
        project_path=str(settings.project_path),
    )
    yield
    logger.info("mcp-code-quality detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-code-quality",
    instructions=(
        "Servidor MCP para validar la calidad del código, garantizando que "
        "las mejores prácticas se cumplan. Usa las herramientas de linting, "
        "formateo y testing frecuentemente durante tus sesiones de programación."
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
        raise SdkMcpError(
            ErrorData(code=-32603, message="Error interno del servidor de calidad.")
        ) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="quality_run_lint",
    description="Ejecuta el linter sobre el proyecto. Puedes especificar un archivo/carpeta con 'target'.",
)
def tool_run_lint(target: str = "") -> dict[str, Any]:
    logger.info("quality_run_lint llamado", target=target)
    return _handle(run_lint, settings.project_path, settings.linter_cmd, target)


@mcp.tool(
    name="quality_run_format",
    description="Ejecuta el formateador de código. Usa check_only=True para ver qué cambiaría sin modificar.",
)
def tool_run_format(check_only: bool = False, target: str = "") -> dict[str, Any]:
    logger.info("quality_run_format llamado", check_only=check_only, target=target)
    return _handle(run_format, settings.project_path, settings.formatter_cmd, check_only, target)


@mcp.tool(
    name="quality_run_tests",
    description="Ejecuta los tests unitarios. Puedes pasar un archivo de tests específico con 'target'.",
)
def tool_run_tests(target: str = "") -> dict[str, Any]:
    logger.info("quality_run_tests llamado", target=target)
    return _handle(run_tests, settings.project_path, settings.test_cmd, target)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="quality_check_complexity",
    description="Analiza la complejidad ciclomatica de un archivo. Parametros: file_path (requerido).",
)
def tool_check_complexity(file_path: str) -> dict[str, Any]:
    logger.info("quality_check_complexity llamado", file_path=file_path)
    return _handle(check_complexity, settings.project_path, file_path)


@mcp.tool(
    name="quality_count_lines",
    description="Cuenta lineas de codigo. Parametros: target (archivo o directorio, default todo).",
)
def tool_count_lines(target: str = "") -> dict[str, Any]:
    logger.info("quality_count_lines llamado", target=target)
    return _handle(count_lines, settings.project_path, target)


@mcp.tool(
    name="quality_find_todos",
    description="Busca TODOs, FIXMEs y HACKs. Parametros: target (archivo o directorio, default todo).",
)
def tool_find_todos(target: str = "") -> list[dict[str, Any]]:
    logger.info("quality_find_todos llamado", target=target)
    return _handle(find_todos, settings.project_path, target)


@mcp.tool(
    name="quality_check_imports",
    description="Analiza imports de un archivo. Parametros: file_path (requerido).",
)
def tool_check_imports(file_path: str) -> dict[str, Any]:
    logger.info("quality_check_imports llamado", file_path=file_path)
    return _handle(check_imports, settings.project_path, file_path)


@mcp.tool(
    name="quality_analyze_dependencies",
    description="Analiza dependencias entre modulos. Parametros: target (directorio, default todo).",
)
def tool_analyze_dependencies(target: str = "") -> dict[str, Any]:
    logger.info("quality_analyze_dependencies llamado", target=target)
    return _handle(analyze_dependencies, settings.project_path, target)


@mcp.tool(
    name="quality_run_type_check",
    description="Ejecuta mypy. Parametros: target (archivo o directorio, default todo).",
)
def tool_run_type_check(target: str = "") -> dict[str, Any]:
    logger.info("quality_run_type_check llamado", target=target)
    return _handle(run_type_check, settings.project_path, target)


@mcp.tool(
    name="quality_run_security_scan",
    description="Ejecuta bandit. Parametros: target (directorio, default todo).",
)
def tool_run_security_scan(target: str = "") -> dict[str, Any]:
    logger.info("quality_run_security_scan llamado", target=target)
    return _handle(run_security_scan, settings.project_path, target)


@mcp.tool(
    name="quality_check_coverage",
    description="Ejecuta pytest con cobertura. Parametros: target (directorio, default todo).",
)
def tool_check_coverage(target: str = "") -> dict[str, Any]:
    logger.info("quality_check_coverage llamado", target=target)
    return _handle(check_coverage, settings.project_path, target)


@mcp.tool(
    name="quality_find_dead_code",
    description="Ejecuta vulture. Parametros: target (directorio, default todo).",
)
def tool_find_dead_code(target: str = "") -> dict[str, Any]:
    logger.info("quality_find_dead_code llamado", target=target)
    return _handle(find_dead_code, settings.project_path, target)


@mcp.tool(
    name="quality_check_dependencies_versions",
    description="Lista versiones de dependencias instaladas.",
)
def tool_check_dependencies_versions() -> dict[str, Any]:
    logger.info("quality_check_dependencies_versions llamado")
    return _handle(check_dependencies_versions, settings.project_path)


@mcp.tool(
    name="quality_audit_dependencies",
    description="Ejecuta pip-audit para auditar vulnerabilidades.",
)
def tool_audit_dependencies() -> dict[str, Any]:
    logger.info("quality_audit_dependencies llamado")
    return _handle(audit_dependencies, settings.project_path)


@mcp.tool(
    name="quality_generate_report",
    description="Genera reporte completo: lint, format, tests. Parametros: target (default todo).",
)
def tool_generate_quality_report(target: str = "") -> dict[str, Any]:
    logger.info("quality_generate_report llamado", target=target)
    return _handle(generate_quality_report, settings.project_path, target)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("quality://configuration")
def res_config() -> str:
    return res.quality_configuration()


@mcp.resource("quality://linting-guide")
def res_lint() -> str:
    return res.quality_linting_guide()


@mcp.resource("quality://formatting-guide")
def res_format() -> str:
    return res.quality_formatting_guide()


@mcp.resource("quality://testing-guide")
def res_test() -> str:
    return res.quality_testing_guide()


@mcp.resource("quality://best-practices")
def res_best() -> str:
    return res.quality_best_practices()


@mcp.resource("quality://quick-reference")
def res_quick() -> str:
    return res.quality_quick_reference()


@mcp.resource("quality://error-codes")
def res_errors() -> str:
    return res.quality_error_codes()


@mcp.resource("quality://troubleshooting")
def res_trouble() -> str:
    return res.quality_troubleshooting()


@mcp.resource("quality://examples")
def res_examples() -> str:
    return res.quality_examples()


@mcp.resource("quality://metrics-guide")
def res_metrics() -> str:
    return res.quality_metrics_guide()


@mcp.resource("quality://ci-integration")
def res_ci() -> str:
    return res.quality_ci_integration()


@mcp.resource("quality://code-smells")
def res_smells() -> str:
    return res.quality_code_smells()


@mcp.resource("quality://security-checks")
def res_sec() -> str:
    return res.quality_security_checks()


@mcp.resource("quality://type-checking")
def res_type() -> str:
    return res.quality_type_checking()


@mcp.resource("quality://refactoring-guide")
def res_refactor() -> str:
    return res.quality_refactoring_guide()


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
