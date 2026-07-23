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
    backup_vault,
    clear_category,
    delete_entry,
    export_entries,
    get_audit_log,
    get_entry,
    get_entry_history,
    get_vault_status,
    import_entries,
    list_categories,
    list_entries,
    list_tags,
    rotate_encryption_key,
    search_entries,
    upsert_entry,
)
from mcp_personal_vault.tools.vault_tools import initialize_database, load_or_create_key
from mcp_personal_vault import resources as res

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


@mcp.tool(name="personal_export")
def tool_export(category: str | None = None, include_sensitive: bool = False) -> dict[str, Any]:
    """Export vault entries as JSON."""
    return _handle(export_entries, settings.database_path, _FERNET, category, include_sensitive, settings.allow_highly_sensitive)


@mcp.tool(name="personal_import")
def tool_import(entries_json: str) -> dict[str, Any]:
    """Import entries from JSON."""
    import json as _json
    try:
        entries = _json.loads(entries_json)
    except Exception as exc:
        raise SdkMcpError(ErrorData(code=-32602, message="Invalid JSON")) from exc
    return _handle(import_entries, settings.database_path, _FERNET, entries, settings.allow_write, settings.allow_secrets)


@mcp.tool(name="personal_audit_log")
def tool_audit_log(limit: int = 50, action: str | None = None) -> list[dict[str, Any]]:
    """View audit log entries."""
    return _handle(get_audit_log, settings.database_path, limit, action)


@mcp.tool(name="personal_list_categories")
def tool_list_categories() -> list[dict[str, Any]]:
    """List all categories with entry counts."""
    return _handle(list_categories, settings.database_path)


@mcp.tool(name="personal_list_tags")
def tool_list_tags() -> list[str]:
    """List all unique tags used in the vault."""
    return _handle(list_tags, settings.database_path)


@mcp.tool(name="personal_backup")
def tool_backup(backup_path: str) -> dict[str, Any]:
    """Create a backup of the vault database."""
    from pathlib import Path
    return _handle(backup_vault, settings.database_path, Path(backup_path))


@mcp.tool(name="personal_clear_category")
def tool_clear_category(category: str) -> dict[str, Any]:
    """Delete all entries in a category."""
    return _handle(clear_category, settings.database_path, category, settings.allow_write)


@mcp.tool(name="personal_entry_history")
def tool_entry_history(category: str, key: str, include_sensitive: bool = False) -> dict[str, Any]:
    """Get change history for an entry."""
    return _handle(get_entry_history, settings.database_path, _FERNET, category, key, include_sensitive, settings.allow_highly_sensitive)


@mcp.tool(name="personal_rotate_key")
def tool_rotate_key(new_key: str) -> dict[str, Any]:
    """Rotate the encryption key for all entries."""
    return _handle(rotate_encryption_key, settings.database_path, _FERNET, new_key.encode(), settings.allow_write)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("vault://configuration")
def res_config() -> str:
    return res.vault_configuration()


@mcp.resource("vault://basics")
def res_basics() -> str:
    return res.vault_basics()


@mcp.resource("vault://best-practices")
def res_best() -> str:
    return res.vault_best_practices()


@mcp.resource("vault://quick-reference")
def res_quick() -> str:
    return res.vault_quick_reference()


@mcp.resource("vault://error-codes")
def res_errors() -> str:
    return res.vault_error_codes()


@mcp.resource("vault://troubleshooting")
def res_trouble() -> str:
    return res.vault_troubleshooting()


@mcp.resource("vault://examples")
def res_examples() -> str:
    return res.vault_examples()


@mcp.resource("vault://encryption")
def res_encryption() -> str:
    return res.vault_encryption()


@mcp.resource("vault://categories")
def res_categories() -> str:
    return res.vault_categories()


@mcp.resource("vault://privacy")
def res_privacy() -> str:
    return res.vault_privacy()


@mcp.resource("vault://backup")
def res_backup() -> str:
    return res.vault_backup()


@mcp.resource("vault://api")
def res_api() -> str:
    return res.vault_api()


@mcp.resource("vault://integration")
def res_integration() -> str:
    return res.vault_integration()


@mcp.resource("vault://security")
def res_security() -> str:
    return res.vault_security()


@mcp.resource("vault://data-model")
def res_data_model() -> str:
    return res.vault_data_model()


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
