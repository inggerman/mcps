"""Backup Tools — 3 herramientas para backup, restore y export."""

from __future__ import annotations

from typing import Any

from mcp_documentation.backup import (
    backup_documents as _backup_documents,
    export_documents as _export_documents,
    list_backups as _list_backups,
    restore_backup as _restore_backup,
)
from mcp_documentation.config import settings


def backup_documents_tool(include_versions: bool = True, include_audit: bool = True) -> dict[str, Any]:
    """Crea backup ZIP completo del document store. Incluye versiones y audit log por defecto."""
    return _backup_documents(settings.root_path, include_versions, include_audit)


def restore_backup_tool(backup_file: str) -> dict[str, Any]:
    """Restaura documentos desde un backup ZIP. Acepta path absoluto o nombre relativo a .backups/."""
    return _restore_backup(settings.root_path, backup_file)


def export_documents_tool(
    output_path: str = "",
    category: str = "",
    directory: str = "",
) -> dict[str, Any]:
    """Exporta documentos a ZIP con filtros opcionales por categoría o directorio."""
    return _export_documents(settings.root_path, output_path, category, directory)


def list_backups_tool() -> list[dict[str, Any]]:
    """Lista los backups disponibles en .backups/ ordenados por fecha (más reciente primero)."""
    return _list_backups(settings.root_path)
