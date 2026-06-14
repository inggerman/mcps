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
    suggest_design_pattern,
)

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
