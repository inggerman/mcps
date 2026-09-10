"""Servidor FastMCP para mcp-source-validator."""

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

from mcp_source_validator.config import settings
from mcp_source_validator.tools import (
    get_trust_score_for_url,
    list_whitelist_domains,
    validate_content,
    validate_url,
)

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-source-validator",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-source-validator")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()


mcp = FastMCP(
    name="mcp-source-validator",
    instructions=(
        "Servidor MCP para validación de fuentes web. "
        "Herramientas: validate_url (URL + SSL + accesibilidad), "
        "validate_content (contenido HTML + metadata + anti-spam), "
        "get_trust_score (score de dominio), list_whitelist (dominios confiables)."
    ),
    lifespan=lifespan,
)


@mcp.tool(
    name="validate_url",
    description=(
        "Valida una URL: esquema, dominio, trust score, SSL, accesibilidad HTTP. "
        "Parámetros: url (requerido). "
        "Retorna: valid, trust_score, domain, ssl_valid, accessible, status_code, issues[]."
    ),
)
def tool_validate_url(url: str) -> dict[str, Any]:
    logger.info("validate_url llamado", url=url)
    try:
        result = validate_url(url)
        logger.info("validate_url completado", url=url, valid=result["valid"])
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en validate_url", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="validate_content",
    description=(
        "Valida contenido de una URL: trust score + metadata HTML + anti-spam AI. "
        "Parámetros: url (requerido), content (opcional, se descarga si vacío). "
        "Retorna: valid, trust_score, title, has_author, has_date, word_count, issues[]."
    ),
)
def tool_validate_content(url: str, content: str = "") -> dict[str, Any]:
    logger.info("validate_content llamado", url=url)
    try:
        result = validate_content(url, content)
        logger.info("validate_content completado", url=url, valid=result["valid"])
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en validate_content", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(
    name="get_trust_score",
    description=(
        "Obtiene el trust score (0-1) de una URL. "
        "Parámetros: url (requerido). "
        "Retorna: url, trust_score, is_trusted, domain."
    ),
)
def tool_get_trust_score(url: str) -> dict[str, Any]:
    return get_trust_score_for_url(url)


@mcp.tool(
    name="list_whitelist",
    description=(
        "Lista todos los dominios en la whitelist con sus trust scores. "
        "Sin parámetros. Retorna: domains dict, total, min_trust_score."
    ),
)
def tool_list_whitelist() -> dict[str, Any]:
    return list_whitelist_domains()


if __name__ == "__main__":
    mcp.run(transport=settings.mcp_transport)
