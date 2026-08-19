"""Clasificador automático de documentación.

Heurísticas de keywords para clasificar documentos en las categorías
predefinidas (core + extended) y categorías custom del usuario.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CLASSIFICATION_KEYWORDS: dict[str, list[str]] = {
    "feature": ["nueva funcionalidad", "feature", "implementación", "nuevo módulo", "nueva feature"],
    "fix": ["bug", "fix", "corrección", "parche", "error solucionado", "bugfix"],
    "hotfix": ["hotfix", "urgente", "producción", "crítico", "inmediato", "parche urgente"],
    "spike": ["spike", "proof of concept", "poc", "exploración", "viabilidad"],
    "bitacora": ["bitácora", "bitacora", "log", "sesión", "trabajo del día", "progreso"],
    "investigation": ["investigación", "investigacion", "análisis", "root cause", "research"],
    "information": ["información", "informacion", "referencia", "notas", "contexto"],
    "insumos": ["insumos", "requisitos", "entradas", "materiales"],
    "architecture": ["arquitectura", "diseño", "componentes", "sistema", "estructura"],
    "runbook": ["runbook", "procedimiento", "operación", "pasos", "operacional"],
    "guide": ["guía", "guia", "instructivo", "cómo", "manual"],
    "tutorial": ["tutorial", "paso a paso", "ejemplo", "aprender"],
    "inventory": ["inventario", "catálogo", "catalogo", "listado", "recursos"],
    "analysis": ["análisis", "analisis", "evaluación", "métricas", "estadísticas"],
    "forensic": ["forense", "post-mortem", "postmortem", "autopsia", "incidente"],
    "reference": ["referencia", "api", "comandos", "configuración", "reference"],
    "troubleshooting": ["troubleshooting", "solución de problemas", "debug", "diagnóstico"],
    "deployment": ["despliegue", "deployment", "instalación", "release", "deploy"],
    "decision": ["decisión", "decision", "adr", "alternativas", "justificación"],
}

CATEGORY_DIRECTORIES: dict[str, str] = {
    "feature": "feature",
    "fix": "fix",
    "hotfix": "hotfix",
    "spike": "spike",
    "bitacora": "bitacoras",
    "investigation": "investigations",
    "information": "information",
    "insumos": "insumos",
    "architecture": "architecture",
    "runbook": "runbooks",
    "guide": "guides",
    "tutorial": "tutorials",
    "inventory": "inventories",
    "analysis": "analysis",
    "forensic": "forensic",
    "reference": "reference",
    "troubleshooting": "troubleshooting",
    "deployment": "deployments",
    "decision": "decisions",
}


def load_custom_categories(path: Path) -> dict[str, list[str]]:
    """Carga categorías custom desde archivo JSON.

    Formato esperado:
        {
            "categoria_nueva": ["keyword1", "keyword2"],
            "otra_cat": ["palabra"]
        }
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {k: list(v) for k, v in data.items() if isinstance(v, list)}
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def get_all_categories(custom_path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Retorna todas las categorías disponibles (core + extended + custom).

    Returns:
        Dict con nombre → {keywords, directory, is_custom}
    """
    result: dict[str, dict[str, Any]] = {}
    for name, keywords in CLASSIFICATION_KEYWORDS.items():
        result[name] = {
            "keywords": keywords,
            "directory": CATEGORY_DIRECTORIES.get(name, name),
            "is_custom": False,
        }
    if custom_path is not None:
        custom = load_custom_categories(custom_path)
        for name, keywords in custom.items():
            result[name] = {
                "keywords": keywords,
                "directory": name.lower().replace(" ", "_"),
                "is_custom": True,
            }
    return result


def classify_text(text: str, custom_path: Path | None = None) -> str:
    """Analiza texto y retorna la clasificación más probable.

    Usa scoring simple: cuenta matches de keywords (case-insensitive).
    Retorna la categoría con mayor score. Empate → primera alfabética.
    Si no hay matches, retorna 'information'.
    """
    text_lower = text.lower()
    all_cats = get_all_categories(custom_path)

    scores: dict[str, int] = {}
    for cat_name, cat_data in all_cats.items():
        score = 0
        for kw in cat_data["keywords"]:
            count = text_lower.count(kw.lower())
            score += count
        if score > 0:
            scores[cat_name] = score

    if not scores:
        return "information"

    return max(scores, key=lambda k: (scores[k], k))


def classify_from_frontmatter(frontmatter: dict[str, Any]) -> str | None:
 """Extrae clasificación desde el frontmatter si existe."""
    if not frontmatter:
        return None
    type_val = frontmatter.get("type")
    if isinstance(type_val, str) and type_val.lower() in CLASSIFICATION_KEYWORDS:
        return type_val.lower()
    return None


def classify_document(
    content: str,
    frontmatter: dict[str, Any] | None = None,
    custom_path: Path | None = None,
) -> str:
    """Clasifica un documento completo.

    Prioridad:
    1. Frontmatter 'type' si es válido
    2. Heurísticas de keywords en el contenido
    3. Default: 'information'
    """
    if frontmatter:
        fm_type = classify_from_frontmatter(frontmatter)
        if fm_type:
            return fm_type
    return classify_text(content, custom_path)


def get_directory_for_category(category: str, custom_path: Path | None = None) -> str:
    """Retorna el nombre del directorio para una categoría."""
    all_cats = get_all_categories(custom_path)
    if category in all_cats:
        return all_cats[category]["directory"]
    return category.lower().replace(" ", "_")


def validate_classification(
    file_path: Path,
    category: str,
    root_path: Path,
    custom_path: Path | None = None,
) -> dict[str, Any]:
    """Valida que un documento esté en el directorio correcto según su tipo.

    Returns:
        Dict con: valid (bool), expected_dir, actual_dir, message
    """
    expected_dir = get_directory_for_category(category, custom_path)
    try:
        rel = file_path.relative_to(root_path)
        actual_dir = rel.parts[0] if len(rel.parts) > 1 else ""
    except ValueError:
        actual_dir = ""

    is_valid = actual_dir == expected_dir
    return {
        "valid": is_valid,
        "expected_dir": expected_dir,
        "actual_dir": actual_dir,
        "message": (
            "Clasificación correcta."
            if is_valid
            else f"Documento en '{actual_dir}' pero debería estar en '{expected_dir}'."
        ),
    }


def add_custom_category(
    path: Path,
    name: str,
    keywords: list[str],
) -> dict[str, Any]:
    """Añade una categoría custom al archivo JSON.

    Crea el archivo si no existe. Si la categoría ya existe, actualiza los keywords.
    """
    existing = load_custom_categories(path)
    existing[name] = keywords
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"name": name, "keywords": keywords, "total_custom": len(existing)}
