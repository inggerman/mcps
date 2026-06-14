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
    update_project_state,
    update_servers_reference,
)

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
