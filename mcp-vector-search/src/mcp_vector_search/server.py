"""Servidor FastMCP para mcp-vector-search."""

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

from mcp_vector_search.config import settings
from mcp_vector_search.tools import (
    create_collection,
    delete_collection,
    list_collections,
    search_similar,
    upsert_points,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-vector-search",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-vector-search")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-vector-search",
    instructions=(
        "Servidor MCP para vector search con Qdrant + LM Studio embeddings. "
        "Herramientas: list_collections, create_collection (requiere ALLOW_WRITE), "
        "delete_collection (requiere ALLOW_WRITE), "
        "upsert_points (requiere ALLOW_WRITE, genera embeddings automáticamente), "
        "search_similar (busca por similitud semántica)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_collections", description="Lista las colecciones de Qdrant. Retorna: lista de {name}.")
def tool_list_collections() -> list[dict[str, Any]]:
    logger.info("list_collections llamado")
    try:
        return list_collections()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_collections", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="create_collection", description="Crea una colección en Qdrant. Requiere VECTOR_SEARCH_ALLOW_WRITE=true. Parámetros: collection_name (str), vector_dim (int opcional). Retorna: {collection, vector_dim, status}.")
def tool_create_collection(collection_name: str, vector_dim: int | None = None) -> dict[str, Any]:
    logger.info("create_collection llamado", collection_name=collection_name)
    try:
        return create_collection(collection_name=collection_name, vector_dim=vector_dim)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en create_collection", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="delete_collection", description="Elimina una colección de Qdrant. Requiere VECTOR_SEARCH_ALLOW_WRITE=true. Parámetros: collection_name (str). Retorna: {collection, status}.")
def tool_delete_collection(collection_name: str) -> dict[str, Any]:
    logger.info("delete_collection llamado", collection_name=collection_name)
    try:
        return delete_collection(collection_name=collection_name)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en delete_collection", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="upsert_points", description="Inserta puntos con embeddings generados vía LM Studio. Requiere VECTOR_SEARCH_ALLOW_WRITE=true. Parámetros: collection_name (str), points (list de {id, text, metadata?}). Retorna: {collection, points_upserted}.")
def tool_upsert_points(collection_name: str, points: list[dict[str, Any]]) -> dict[str, Any]:
    logger.info("upsert_points llamado", collection_name=collection_name, count=len(points))
    try:
        return upsert_points(collection_name=collection_name, points=points)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en upsert_points", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="search_similar", description="Busca puntos similares por texto. Parámetros: collection_name (str), query (str), limit (int, default 5). Retorna: lista de {id, score, payload}.")
def tool_search_similar(collection_name: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    logger.info("search_similar llamado", collection_name=collection_name, query=query[:50])
    try:
        return search_similar(collection_name=collection_name, query=query, limit=limit)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en search_similar", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
