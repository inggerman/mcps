"""Servidor FastMCP para mcp-web-search."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import MCPError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_web_search.config import settings
from mcp_web_search.tools import (
    search_docs,
    search_github,
    search_stackoverflow,
    search_web,
)
from mcp_web_search.whitelist import get_trust_score, is_trusted, list_whitelist

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-web-search",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-web-search")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()


# ---------------------------------------------------------------------------
# Instancia del servidor
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-web-search",
    instructions=(
        "Servidor MCP para búsqueda web validada. "
        "Herramientas: search_web (búsqueda general), search_docs (documentación oficial), "
        "search_github (repositorios GitHub), search_stackoverflow (Q&A Stack Overflow). "
        "Todos los resultados se filtran por una whitelist de dominios confiables. "
        "Cada resultado incluye trust_score (0-1) basado en la fuente."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="search_web",
    description=(
        "Busca en la web y filtra resultados por whitelist de fuentes confiables. "
        "Parámetros: query (requerido), max_results (default 10), provider (duckduckgo|brave). "
        "Retorna: query, results[] con url/title/snippet/trust_score/domain, "
        "total_raw, total_filtered, provider."
    ),
)
def tool_search_web(
    query: str,
    max_results: int | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    logger.info("search_web llamado", query=query)
    try:
        result = search_web(query, max_results, provider)
        logger.info(
            "search_web completado",
            query=query,
            total_filtered=result["total_filtered"],
        )
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en search_web", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="search_docs",
    description=(
        "Busca específicamente en documentación oficial (trust_score >= 0.9). "
        "Parámetros: query (requerido), technology (ej: 'fastapi', 'kubernetes'), max_results. "
        "Retorna: results[] filtrados a solo fuentes oficiales."
    ),
)
def tool_search_docs(
    query: str,
    technology: str = "",
    max_results: int | None = None,
) -> dict[str, Any]:
    logger.info("search_docs llamado", query=query, technology=technology)
    try:
        result = search_docs(query, technology, max_results)
        logger.info(
            "search_docs completado",
            query=query,
            technology=technology,
            results=len(result["results"]),
        )
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en search_docs", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="search_github",
    description=(
        "Busca específicamente en GitHub. "
        "Parámetros: query (requerido), max_results. "
        "Retorna: results[] de GitHub con trust_score."
    ),
)
def tool_search_github(query: str, max_results: int | None = None) -> dict[str, Any]:
    logger.info("search_github llamado", query=query)
    try:
        result = search_github(query, max_results)
        logger.info("search_github completado", query=query, results=len(result["results"]))
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en search_github", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="search_stackoverflow",
    description=(
        "Busca específicamente en Stack Overflow. "
        "Parámetros: query (requerido), max_results. "
        "Retorna: results[] de Stack Overflow con trust_score."
    ),
)
def tool_search_stackoverflow(query: str, max_results: int | None = None) -> dict[str, Any]:
    logger.info("search_stackoverflow llamado", query=query)
    try:
        result = search_stackoverflow(query, max_results)
        logger.info("search_stackoverflow completado", query=query, results=len(result["results"]))
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en search_stackoverflow", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="get_trust_score",
    description=(
        "Obtiene el trust score (0-1) de una URL basado en la whitelist de dominios. "
        "Parámetros: url (requerido). "
        "Retorna: url, trust_score, is_trusted."
    ),
)
def tool_get_trust_score(url: str) -> dict[str, Any]:
    score = get_trust_score(url)
    return {
        "url": url,
        "trust_score": score,
        "is_trusted": is_trusted(url, settings.trust_threshold),
    }


@mcp.tool(
    name="list_trusted_sources",
    description=(
        "Lista todos los dominios en la whitelist con sus trust scores. "
        "Sin parámetros. Retorna: domains dict con domain -> trust_score."
    ),
)
def tool_list_trusted_sources() -> dict[str, Any]:
    return {
        "domains": list_whitelist(),
        "total": len(list_whitelist()),
        "threshold": settings.trust_threshold,
    }


if __name__ == "__main__":
    mcp.run(transport=settings.mcp_transport)
