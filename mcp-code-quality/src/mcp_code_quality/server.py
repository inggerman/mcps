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
    run_format,
    run_lint,
    run_tests,
)

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
