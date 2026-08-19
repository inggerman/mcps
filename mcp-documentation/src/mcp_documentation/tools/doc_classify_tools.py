"""Doc Classify Tools — 5 herramientas para clasificación de documentación."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import frontmatter

from mcp_documentation.classifiers import (
    add_custom_category,
    classify_document,
    get_all_categories,
    get_directory_for_category,
    validate_classification,
)
from mcp_documentation.config import settings
from mcp_documentation.tools.doc_read_tools import _resolve_path, _ensure_allowed, _read_file_text, _parse_frontmatter
from mcp_documentation.tools.doc_write_tools import move_document


def classify_document_tool(path: str) -> dict[str, Any]:
    """Analiza contenido y sugiere/auto-asigna clasificación."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)
    content = _read_file_text(resolved)
    fm_data, body = _parse_frontmatter(content)

    custom_path = settings.resolved_custom_categories_path
    suggested = classify_document(body, fm_data, custom_path)
    current = fm_data.get("type", "unknown")

    return {
        "path": str(resolved),
        "current_category": current,
        "suggested_category": suggested,
        "matches": current.lower() == suggested.lower(),
        "all_categories": list(get_all_categories(custom_path).keys()),
    }


def get_categories() -> dict[str, Any]:
    """Lista todas las categorías disponibles (core + extended + custom)."""
    custom_path = settings.resolved_custom_categories_path
    cats = get_all_categories(custom_path)
    return {
        "total": len(cats),
        "categories": {
            name: {
                "directory": data["directory"],
                "is_custom": data["is_custom"],
                "keywords_count": len(data["keywords"]),
            }
            for name, data in cats.items()
        },
    }


def add_custom_category_tool(name: str, keywords: list[str]) -> dict[str, Any]:
    """Añade categoría custom al archivo .categories.json."""
    if not name or len(name.strip()) < 2:
        raise ValueError("El nombre debe tener al menos 2 caracteres.")
    if not keywords:
        raise ValueError("Debe proporcionar al menos un keyword.")

    custom_path = settings.resolved_custom_categories_path
    return add_custom_category(custom_path, name.strip(), keywords)


def validate_classification_tool(path: str) -> dict[str, Any]:
    """Valida que un documento esté en el directorio correcto según su tipo."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)
    content = _read_file_text(resolved)
    fm_data, _ = _parse_frontmatter(content)

    category = fm_data.get("type", "information")
    custom_path = settings.resolved_custom_categories_path

    return validate_classification(resolved, category, settings.root_path, custom_path)


def reclassify_document(path: str, new_category: str) -> dict[str, Any]:
    """Reclassifica un documento: mueve archivo, actualiza frontmatter y directorio."""
    custom_path = settings.resolved_custom_categories_path
    all_cats = get_all_categories(custom_path)

    if new_category not in all_cats:
        raise ValueError(
            f"Categoría '{new_category}' no válida. "
            f"Categorías disponibles: {', '.join(all_cats.keys())}"
        )

    return move_document(path, new_category)
