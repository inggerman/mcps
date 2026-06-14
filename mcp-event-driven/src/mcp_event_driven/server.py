"""
Servidor FastMCP para mcp-event-driven.

Expone herramientas para analizar esquemas de eventos y simular flujos.
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

from mcp_event_driven import __version__
from mcp_event_driven.config import settings
from mcp_event_driven.tools.event_tools import (
    analyze_choreography,
    generate_event_payload,
    parse_event_schema,
)

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-event-driven",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-event-driven")
    logger.info(
        "mcp-event-driven iniciando",
        version=__version__,
        schemas_path=str(settings.schemas_path),
    )
    yield
    logger.info("mcp-event-driven detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-event-driven",
    instructions=(
        "Servidor MCP para analizar esquemas de eventos (JSON Schema, AsyncAPI) "
        "y simular flujos de datos en arquitecturas coreografiadas."
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
        raise SdkMcpError(
            ErrorData(code=-32603, message="Error interno del servidor de eventos.")
        ) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="event_parse_schema",
    description="Parsea un esquema de evento (JSON Schema o AsyncAPI) para extraer metadata y propiedades.",
)
def tool_parse_schema(filename: str) -> dict[str, Any]:
    file_path = settings.schemas_path / filename
    logger.info("event_parse_schema llamado", file=filename)
    return _handle(parse_event_schema, file_path)


@mcp.tool(
    name="event_analyze_choreography",
    description="Escanea el directorio de esquemas configurado para encontrar todos los eventos registrados.",
)
def tool_analyze_choreography() -> dict[str, Any]:
    logger.info("event_analyze_choreography llamado")
    return _handle(analyze_choreography, settings.schemas_path)


@mcp.tool(
    name="event_generate_mock_payload",
    description="Genera un payload JSON simulado para un evento, dado un arreglo de sus propiedades.",
)
def tool_generate_payload(properties: list[str]) -> dict[str, Any]:
    logger.info("event_generate_mock_payload llamado")
    return _handle(generate_event_payload, properties)


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
