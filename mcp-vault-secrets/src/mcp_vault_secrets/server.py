"""Servidor FastMCP para mcp-vault-secrets."""

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

from mcp_vault_secrets.config import settings
from mcp_vault_secrets.tools import (
    get_secret_metadata,
    list_mounts,
    list_secrets,
    read_secret,
    vault_status,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-vault-secrets",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-vault-secrets")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-vault-secrets",
    instructions=(
        "Servidor MCP para HashiCorp Vault. "
        "Herramientas: vault_status (seal status), list_mounts, "
        "list_secrets (lista claves en path KV-v2), "
        "read_secret (lee secreto KV-v2, respeta VAULT_ALLOWED_PATHS), "
        "get_secret_metadata (versiones y timestamps)."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="vault_status", description="Obtiene el estado del seal de Vault. Retorna: sealed, total_shares, threshold, version, cluster_name.")
def tool_vault_status() -> dict[str, Any]:
    logger.info("vault_status llamado")
    try:
        return vault_status()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en vault_status", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_mounts", description="Lista los secret mounts de Vault. Retorna: dict de mount_path → {type, version}.")
def tool_list_mounts() -> dict[str, Any]:
    logger.info("list_mounts llamado")
    try:
        return list_mounts()
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_mounts", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="list_secrets", description="Lista claves en un path KV-v2. Parámetros: path (str). Respeta VAULT_ALLOWED_PATHS. Retorna: lista de keys.")
def tool_list_secrets(path: str) -> list[str]:
    logger.info("list_secrets llamado", path=path)
    try:
        return list_secrets(path=path)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_secrets", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="read_secret", description="Lee un secreto KV-v2. Parámetros: path (str), version (int opcional). Respeta VAULT_ALLOWED_PATHS. Retorna: {path, data, metadata, version}.")
def tool_read_secret(path: str, version: int | None = None) -> dict[str, Any]:
    logger.info("read_secret llamado", path=path, version=version)
    try:
        return read_secret(path=path, version=version)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en read_secret", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_secret_metadata", description="Obtiene metadatos de un secreto KV-v2. Parámetros: path (str). Retorna: versiones, timestamps, current_version.")
def tool_get_secret_metadata(path: str) -> dict[str, Any]:
    logger.info("get_secret_metadata llamado", path=path)
    try:
        return get_secret_metadata(path=path)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_secret_metadata", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
