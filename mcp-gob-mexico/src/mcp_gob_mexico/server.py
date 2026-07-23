"""
Servidor FastMCP para mcp-gob-mexico.

Expone tools para consultar APIs de 15 instituciones del gobierno mexicano
y resources con catalogos, documentacion y referencias.

Transporte: stdio (compatible con Claude Desktop, Cursor, Windsurf).
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp_shared.logging import get_logger, setup_logging

from mcp_gob_mexico import __version__
from mcp_gob_mexico.config import settings
from mcp_gob_mexico.resources import get_all_resources

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-gob-mexico",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-gob-mexico")
    logger.info(
        "Servidor mcp-gob-mexico iniciando",
        version=__version__,
        http_timeout=settings.http_timeout,
        max_retries=settings.max_retries,
        cache_ttl=settings.cache_ttl,
        log_level=settings.log_level,
        log_format=settings.log_format,
    )
    yield
    try:
        logger.info("Servidor mcp-gob-mexico detenido", version=__version__)
    except Exception:
        pass


mcp = FastMCP(
    "gob-mexico-apis",
    version=__version__,
    lifespan=lifespan,
)

# Register all tool modules
from mcp_gob_mexico.tools import (  # noqa: E402
    banxico,
    cdmx,
    cfe,
    conagua,
    datos_gob,
    impi,
    imss,
    infonavit,
    inegi,
    profeco,
    renapo,
    rpc,
    sat,
    semarnat,
)

for module in [inegi, banxico, sat, datos_gob, profeco, cdmx,
               imss, conagua, semarnat, impi, cfe, rpc, renapo, infonavit]:
    module.register(mcp)

# Register all resources
for res in get_all_resources():
    def _make_resource(r: dict[str, Any] = res) -> None:
        @mcp.resource(r["uri"], name=r["name"], mime_type=r["mimeType"])
        def _resource() -> str:
            return r["content"]
    _make_resource()


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
