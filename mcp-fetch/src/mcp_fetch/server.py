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
from mcp_fetch.tools import (
    batch_fetch_json,
    check_url,
    convert_html_to_markdown,
    download_file,
    extract_links,
    extract_metadata,
    extract_tables,
    extract_text,
    fetch_head,
    fetch_json,
    fetch_post,
    fetch_url,
    fetch_with_auth,
    fetch_with_retry,
)
from mcp_fetch import resources as res

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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(name="fetch_head")
def tool_fetch_head(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    try:
        return fetch_head(url=url, headers=headers, timeout=timeout)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en fetch_head", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="check_url")
def tool_check_url(url: str, timeout: float | None = None) -> dict[str, Any]:
    try:
        return check_url(url=url, timeout=timeout)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en check_url", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="fetch_with_auth")
def tool_fetch_with_auth(
    url: str,
    auth_type: str = "bearer",
    token: str = "",
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    try:
        return fetch_with_auth(url=url, auth_type=auth_type, token=token, headers=headers, timeout=timeout)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en fetch_with_auth", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="extract_links")
def tool_extract_links(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    filter_pattern: str | None = None,
) -> dict[str, Any]:
    try:
        return extract_links(url=url, headers=headers, timeout=timeout, filter_pattern=filter_pattern)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en extract_links", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="extract_metadata")
def tool_extract_metadata(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    try:
        return extract_metadata(url=url, headers=headers, timeout=timeout)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en extract_metadata", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="extract_tables")
def tool_extract_tables(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    try:
        return extract_tables(url=url, headers=headers, timeout=timeout)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en extract_tables", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="fetch_with_retry")
def tool_fetch_with_retry(
    url: str,
    max_retries: int = 3,
    delay_seconds: float = 1.0,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    try:
        return fetch_with_retry(url=url, max_retries=max_retries, delay_seconds=delay_seconds, headers=headers, timeout=timeout)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en fetch_with_retry", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="batch_fetch_json")
def tool_batch_fetch_json(
    urls: list[str],
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> list[dict[str, Any]]:
    try:
        return batch_fetch_json(urls=urls, headers=headers, timeout=timeout)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en batch_fetch_json", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="convert_html_to_markdown")
def tool_convert_html_to_markdown(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    try:
        return convert_html_to_markdown(url=url, headers=headers, timeout=timeout)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en convert_html_to_markdown", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="download_file")
def tool_download_file(
    url: str,
    output_path: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    try:
        return download_file(url=url, output_path=output_path, headers=headers, timeout=timeout, max_bytes=max_bytes)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en download_file", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Resources estáticos
# ---------------------------------------------------------------------------


@mcp.resource("fetch://http-status-codes")
def res_http_status_codes() -> str:
    return res.http_status_codes()


@mcp.resource("fetch://http-methods")
def res_http_methods() -> str:
    return res.http_methods_guide()


@mcp.resource("fetch://content-types")
def res_content_types() -> str:
    return res.content_types_guide()


@mcp.resource("fetch://security-best-practices")
def res_security() -> str:
    return res.security_best_practices()


@mcp.resource("fetch://api-auth-guide")
def res_api_auth() -> str:
    return res.api_authentication_guide()


@mcp.resource("fetch://rest-conventions")
def res_rest() -> str:
    return res.rest_api_conventions()


@mcp.resource("fetch://json-path-guide")
def res_json_path() -> str:
    return res.json_path_guide()


@mcp.resource("fetch://html-extraction-tips")
def res_html_tips() -> str:
    return res.html_extraction_tips()


@mcp.resource("fetch://common-api-examples")
def res_api_examples() -> str:
    return res.common_api_examples()


@mcp.resource("fetch://configuration")
def res_config() -> str:
    return res.fetch_configuration()


@mcp.resource("fetch://rate-limiting-tips")
def res_rate_limit() -> str:
    return res.rate_limiting_tips()


@mcp.resource("fetch://error-handling")
def res_error_handling() -> str:
    return res.error_handling_guide()


@mcp.resource("fetch://url-validation-rules")
def res_url_rules() -> str:
    return res.url_validation_rules()


@mcp.resource("fetch://examples/fetch-url")
def res_example_fetch() -> str:
    return res.example_fetch_url()


@mcp.resource("fetch://examples/fetch-json")
def res_example_json() -> str:
    return res.example_fetch_json()


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
