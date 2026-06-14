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
    analyze_dependencies,
    analyze_solid_heuristics,
    get_project_tree,
)

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
