"""FastMCP server for encrypted personal context."""

from __future__ import annotations

from typing import Any

from cryptography.fernet import Fernet
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_personal_vault.config import settings
from mcp_personal_vault.tools import (
    delete_entry,
    get_entry,
    get_vault_status,
    list_entries,
    search_entries,
    upsert_entry,
)
from mcp_personal_vault.tools.vault_tools import initialize_database, load_or_create_key

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-personal-vault",
)
logger = get_logger(__name__)
_KEY = load_or_create_key(settings.key_file, settings.encryption_key)
_FERNET = Fernet(_KEY)
initialize_database(settings.database_path)

mcp = FastMCP(
    name="mcp-personal-vault",
    instructions=(
        "Bóveda local cifrada para contexto personal. Consulta search_personal_context "
        "solo cuando la petición se beneficie de preferencias, identidad, trayectoria, "
        "contactos o contexto personal del usuario. No almacenes contraseñas, tokens, PIN, "
        "CVV, frases semilla ni llaves privadas. Los datos highly_sensitive se ocultan "
        "salvo que el servidor y la llamada autoricen su revelación explícitamente."
    ),
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="personal_vault_status")
def tool_status() -> dict[str, Any]:
    """Return vault metadata without exposing personal values."""
    return _handle(get_vault_status, settings.database_path, settings.key_file)


@mcp.tool(name="personal_upsert")
def tool_upsert(
    category: str,
    key: str,
    value: Any,
    sensitivity: str = "private",
    tags: list[str] | None = None,
    source: str = "user",
) -> dict[str, Any]:
    """Create or update one encrypted personal fact."""
    return _handle(
        upsert_entry,
        settings.database_path,
        _FERNET,
        category,
        key,
        value,
        sensitivity,
        tags,
        source,
        settings.allow_write,
        settings.allow_secrets,
    )


@mcp.tool(name="personal_get")
def tool_get(category: str, key: str, include_sensitive: bool = False) -> dict[str, Any]:
    """Read one personal fact; highly sensitive values require explicit authorization."""
    return _handle(
        get_entry,
        settings.database_path,
        _FERNET,
        category,
        key,
        include_sensitive,
        settings.allow_highly_sensitive,
    )


@mcp.tool(name="personal_list")
def tool_list(category: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """List metadata for personal entries without exposing their values."""
    return _handle(
        list_entries,
        settings.database_path,
        category,
        min(max(limit, 1), settings.max_results),
    )


@mcp.tool(name="search_personal_context")
def tool_search(
    query: str,
    categories: list[str] | None = None,
    include_sensitive: bool = False,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Find relevant personal context for the current user request."""
    return _handle(
        search_entries,
        settings.database_path,
        _FERNET,
        query,
        categories,
        include_sensitive,
        settings.allow_highly_sensitive,
        min(max(limit, 1), settings.max_results),
    )


@mcp.tool(name="personal_delete")
def tool_delete(category: str, key: str) -> dict[str, str]:
    """Delete one personal fact when local writes are enabled."""
    return _handle(delete_entry, settings.database_path, category, key, settings.allow_write)


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
