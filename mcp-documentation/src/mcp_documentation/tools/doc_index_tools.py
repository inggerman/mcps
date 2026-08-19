"""Doc Index Tools — 5 herramientas para indexación y búsqueda FTS."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp_documentation.config import settings
from mcp_documentation.index import (
    get_index_stats,
    index_all,
    index_document,
    rebuild_index,
    search_documents,
    suggest_similar_documents,
)
from mcp_documentation.tools.doc_read_tools import _resolve_path, _ensure_allowed


def index_documents_tool(directory: str = "") -> dict[str, Any]:
    """Indexa todos los documentos en root_path usando SQLite FTS5."""
    root = _resolve_path(directory) if directory else settings.root_path
    return index_all(root, settings.resolved_index_path, settings.extensions_list)


def search_documents_tool(query: str, limit: int = 20, category: str | None = None) -> list[dict[str, Any]]:
    """Búsqueda full-text con ranking BM25 sobre el índice."""
    return search_documents(query, settings.resolved_index_path, limit, category)


def get_index_stats_tool() -> dict[str, Any]:
    """Estadísticas del índice: total documentos, por categoría, por tipo, tamaño."""
    return get_index_stats(settings.resolved_index_path)


def rebuild_index_tool() -> dict[str, Any]:
    """Reconstruye el índice desde cero."""
    return rebuild_index(settings.root_path, settings.resolved_index_path, settings.extensions_list)


def suggest_similar_documents_tool(path: str, limit: int = 5) -> list[dict[str, Any]]:
    """Dado un documento, encuentra similares por contenido y tags."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)
    return suggest_similar_documents(resolved, settings.root_path, settings.resolved_index_path, limit)
