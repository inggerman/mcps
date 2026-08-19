"""Versioning Tools — 4 herramientas para versionado y audit log."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp_documentation.config import settings
from mcp_documentation.versioning import (
    audit,
    compare_versions as _compare_versions,
    get_audit_log as _get_audit_log,
    get_document_history as _get_history,
    restore_version as _restore_version,
    save_version as _save_version,
)


def _resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    return (settings.root_path / path).resolve()


def get_document_history_tool(path: str) -> list[dict[str, Any]]:
    """Retorna historial completo de versiones de un documento: snapshots, fechas, tamaños."""
    return _get_history(settings.root_path, path)


def restore_document_version_tool(path: str, version: int) -> dict[str, Any]:
    """Restaura una versión específica de un documento (guarda snapshot actual antes)."""
    return _restore_version(settings.root_path, path, version)


def compare_versions_tool(path: str, version_a: int, version_b: int) -> dict[str, Any]:
    """Compara dos versiones de un documento y retorna diff unificado."""
    return _compare_versions(settings.root_path, path, version_a, version_b)


def get_audit_log_tool(
    limit: int = 50,
    action: str | None = None,
    target: str | None = None,
) -> list[dict[str, Any]]:
    """Consulta el audit log con filtros: action (create/update/delete/version_saved/...), target (file path)."""
    return _get_audit_log(settings.root_path, limit, action, target)
