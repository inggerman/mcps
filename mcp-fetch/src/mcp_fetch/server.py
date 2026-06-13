"""Servidor FastMCP para mcp-fetch."""

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

from mcp_fetch.config import settings
from mcp_fetch.tools import extract_text, fetch_json, fetch_post, fetch_url

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-fetch",
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-fetch")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()


# ---------------------------------------------------------------------------
# Instancia del servidor
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-fetch",
    instructions=(
        "Servidor MCP para peticiones HTTP. "
        "Herramientas: fetch_url (GET crudo), fetch_post (POST), "
        "extract_text (GET + limpiar HTML → texto legible), "
        "fetch_json (GET + parsear JSON con path opcional). "
        "Ideal para consultar APIs REST, leer documentación web, Javadoc, "
        "Spring docs, Kafka docs, Kubernetes docs, Terraform registry, etc."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Tool: fetch_url
# ---------------------------------------------------------------------------


@mcp.tool(
    name="fetch_url",
    description=(
        "Realiza un GET HTTP y devuelve el contenido crudo + metadatos. "
        "Parámetros: url (requerido), headers (dict opcional), "
        "timeout (segundos, default 30), max_bytes (default 5MB). "
        "Retorna: url, status_code, content_type, content, truncated, headers, elapsed_ms."
    ),
)
def tool_fetch_url(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    logger.info("fetch_url llamado", url=url)
    try:
        result = fetch_url(url=url, headers=headers, timeout=timeout, max_bytes=max_bytes)
        logger.info(
            "fetch_url completado",
            url=url,
            status_code=result["status_code"],
            elapsed_ms=result["elapsed_ms"],
            truncated=result["truncated"],
        )
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en fetch_url", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message=f"Error interno: {exc}")) from exc


# ---------------------------------------------------------------------------
# Tool: fetch_post
# ---------------------------------------------------------------------------


@mcp.tool(
    name="fetch_post",
    description=(
        "Realiza un POST HTTP con cuerpo JSON o form-data. "
        "Parámetros: url (requerido), json_body (dict para application/json), "
        "form_data (dict para form-urlencoded), headers, timeout, max_bytes. "
        "Solo uno de json_body o form_data puede estar presente. "
        "Retorna: url, status_code, content_type, content, truncated, headers, elapsed_ms."
    ),
)
def tool_fetch_post(
    url: str,
    json_body: dict[str, Any] | None = None,
    form_data: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    logger.info(
        "fetch_post llamado",
        url=url,
        has_json=json_body is not None,
        has_form=form_data is not None,
    )
    try:
        result = fetch_post(
            url=url,
            json_body=json_body,
            form_data=form_data,
            headers=headers,
            timeout=timeout,
            max_bytes=max_bytes,
        )
        logger.info("fetch_post completado", url=url, status_code=result["status_code"])
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en fetch_post", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message=f"Error interno: {exc}")) from exc


# ---------------------------------------------------------------------------
# Tool: extract_text
# ---------------------------------------------------------------------------


@mcp.tool(
    name="extract_text",
    description=(
        "Descarga una página HTML y extrae el texto limpio (sin tags HTML, scripts ni estilos). "
        "Ideal para leer documentación: Spring Boot docs, Kafka docs, Kubernetes docs, "
        "Terraform registry, Javadoc, Stack Overflow, artículos, etc. "
        "Parámetros: url (requerido), headers, timeout, "
        "include_links (bool, default false), include_title (bool, default true). "
        "Retorna: url, title, text, word_count, links (si include_links=true), status_code."
    ),
)
def tool_extract_text(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    include_links: bool = False,
    include_title: bool = True,
) -> dict[str, Any]:
    logger.info("extract_text llamado", url=url)
    try:
        result = extract_text(
            url=url,
            headers=headers,
            timeout=timeout,
            include_links=include_links,
            include_title=include_title,
        )
        logger.info(
            "extract_text completado",
            url=url,
            word_count=result["word_count"],
        )
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en extract_text", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message=f"Error interno: {exc}")) from exc


# ---------------------------------------------------------------------------
# Tool: fetch_json
# ---------------------------------------------------------------------------


@mcp.tool(
    name="fetch_json",
    description=(
        "Descarga una URL y parsea la respuesta como JSON. "
        "Opcionalmente navega el resultado con un path tipo 'data.items[0].name'. "
        "Ideal para consultar APIs REST: GitHub API, Docker Hub API, Kubernetes API, "
        "Terraform Cloud API, Kafka REST Proxy, Spring Boot Actuator, etc. "
        "Parámetros: url (requerido), headers, timeout, "
        "jq_path (string opcional, notación punto+índice). "
        "Retorna: url, data (JSON completo o sub-valor), status_code, path_used."
    ),
)
def tool_fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    jq_path: str | None = None,
) -> dict[str, Any]:
    logger.info("fetch_json llamado", url=url, jq_path=jq_path)
    try:
        result = fetch_json(url=url, headers=headers, timeout=timeout, jq_path=jq_path)
        logger.info("fetch_json completado", url=url, status_code=result["status_code"])
        return result
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en fetch_json", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message=f"Error interno: {exc}")) from exc


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
