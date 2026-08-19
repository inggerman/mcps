"""Doc Write Tools — 8 herramientas para escritura de documentación."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import frontmatter

from mcp_documentation.classifiers import (
    classify_document,
    get_directory_for_category,
)
from mcp_documentation.config import settings


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    return (settings.root_path / path).resolve()


def _ensure_allowed(path: Path) -> None:
    if not settings.is_allowed_extension(path):
        raise ValueError(
            f"Extensión '{path.suffix}' no permitida. "
            f"Extensiones válidas: {settings.extensions_list}"
        )


def _build_frontmatter(
    title: str,
    doc_type: str,
    project: str,
    tags: list[str],
    author: str,
    status: str = "draft",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fm: dict[str, Any] = {
        "title": title,
        "type": doc_type,
        "project": project,
        "tags": tags,
        "timestamp": _now_iso(),
        "status": status,
        "author": author,
    }
    if extra:
        fm.update(extra)
    return fm


def _serialize_frontmatter(fm: dict[str, Any], body: str) -> str:
    post = frontmatter.Post(body, **fm)
    return frontmatter.dumps(post)


def create_document(
    title: str,
    content: str,
    doc_type: str = "",
    project: str = "",
    tags: list[str] | None = None,
    author: str = "unknown",
    status: str = "draft",
    filename: str = "",
    directory: str = "",
) -> dict[str, Any]:
    """Crea documento nuevo con frontmatter obligatorio y timestamp automático.

    Auto-clasifica en directorio correcto si auto_classify está activo.
    """
    if not title or len(title.strip()) < 3:
        raise ValueError("El título debe tener al menos 3 caracteres.")

    tags = tags or []
    doc_type = doc_type or "information"

    if settings.auto_classify and not directory:
        directory = get_directory_for_category(doc_type, settings.resolved_custom_categories_path)

    if not filename:
        safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in title.lower())
        filename = f"{safe_title}.md"

    if directory:
        dir_path = settings.root_path / directory
    else:
        dir_path = settings.root_path

    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / filename

    if file_path.exists():
        raise ValueError(f"El archivo ya existe: {file_path}")

    fm = _build_frontmatter(title, doc_type, project, tags, author, status)
    file_content = _serialize_frontmatter(fm, content)

    file_path.write_text(file_content, encoding="utf-8")

    return {
        "path": str(file_path),
        "filename": file_path.name,
        "title": title,
        "type": doc_type,
        "timestamp": fm["timestamp"],
        "created": True,
    }


def update_document(path: str, content: str, update_timestamp: bool = True) -> dict[str, Any]:
    """Actualiza contenido de documento existente, actualiza timestamp automáticamente."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)

    if not resolved.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {resolved}")

    raw = resolved.read_text(encoding="utf-8", errors="replace")
    post = frontmatter.loads(raw)

    post.content = content
    if update_timestamp:
        post.metadata["timestamp"] = _now_iso()

    resolved.write_text(frontmatter.dumps(post), encoding="utf-8")

    return {
        "path": str(resolved),
        "updated": True,
        "timestamp": post.metadata.get("timestamp"),
    }


def append_to_document(path: str, content: str, separator: str = "\n\n") -> dict[str, Any]:
    """Añade contenido al final de un documento existente."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)

    if not resolved.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {resolved}")

    raw = resolved.read_text(encoding="utf-8", errors="replace")
    post = frontmatter.loads(raw)

    post.content = post.content.rstrip() + separator + content
    post.metadata["timestamp"] = _now_iso()

    resolved.write_text(frontmatter.dumps(post), encoding="utf-8")

    return {
        "path": str(resolved),
        "appended": True,
        "timestamp": post.metadata.get("timestamp"),
    }


def update_frontmatter(path: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Actualiza campos específicos del frontmatter sin tocar el body."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)

    if not resolved.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {resolved}")

    raw = resolved.read_text(encoding="utf-8", errors="replace")
    post = frontmatter.loads(raw)

    post.metadata.update(updates)
    post.metadata["timestamp"] = _now_iso()

    resolved.write_text(frontmatter.dumps(post), encoding="utf-8")

    return {
        "path": str(resolved),
        "frontmatter": dict(post.metadata),
        "updated": True,
    }


def add_tags(path: str, tags: list[str]) -> dict[str, Any]:
    """Añade tags al frontmatter de un documento."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)

    if not resolved.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {resolved}")

    raw = resolved.read_text(encoding="utf-8", errors="replace")
    post = frontmatter.loads(raw)

    existing: list[str] = post.metadata.get("tags", [])
    if not isinstance(existing, list):
        existing = [str(existing)]

    for tag in tags:
        if tag not in existing:
            existing.append(tag)

    post.metadata["tags"] = existing
    post.metadata["timestamp"] = _now_iso()

    resolved.write_text(frontmatter.dumps(post), encoding="utf-8")

    return {
        "path": str(resolved),
        "tags": existing,
        "added": tags,
    }


def delete_document(path: str) -> dict[str, Any]:
    """Elimina un documento."""
    resolved = _resolve_path(path)

    if not resolved.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {resolved}")

    resolved.unlink()

    return {
        "path": str(resolved),
        "deleted": True,
    }


def create_from_template(
    template_type: str,
    title: str,
    project: str = "",
    tags: list[str] | None = None,
    author: str = "unknown",
    filename: str = "",
) -> dict[str, Any]:
    """Crea documento desde plantilla predefinida."""

    templates: dict[str, str] = {
        "feature": (
            "# {title}\n\n"
            "## Descripción\n\n[Descripción de la feature]\n\n"
            "## Contexto\n\n[Contexto y motivación]\n\n"
            "## Detalles técnicos\n\n"
            "**[SPEC]**\n- [Hecho técnico 1]\n- [Hecho técnico 2]\n\n"
            "## Pasos\n\n1. [Paso 1]\n2. [Paso 2]\n\n"
            "## Verificación\n\n```bash\n[comando de verificación]\n```\n\n"
            "## Problemas conocidos\n\n**[BUG]** [Bug conocido si aplica]\n"
        ),
        "fix": (
            "# Fix: {title}\n\n"
            "## Problema\n\n[Descripción del bug]\n\n"
            "## Root Cause\n\n[Causa raíz identificada]\n\n"
            "## Solución\n\n[Descripción de la solución aplicada]\n\n"
            "## Verificación\n\n```bash\n[comando de verificación]\n```\n"
        ),
        "hotfix": (
            "# Hotfix: {title}\n\n"
            "## Incidente\n\n[Descripción del incidente crítico]\n\n"
            "## Acción Inmediata\n\n[Acción tomada]\n\n"
            "## Impacto\n\n[Servicios/sistemas afectados]\n\n"
            "## Post-Fix\n\n[Acciones de seguimiento necesarias]\n"
        ),
        "spike": (
            "# Spike: {title}\n\n"
            "## Hipótesis\n\n[Hipótesis a validar]\n\n"
            "## Metodología\n\n[Enfoque de exploración]\n\n"
            "## Resultados\n\n[Hallazgos]\n\n"
            "## Conclusión\n\n[Viabilidad: sí/no/condicional]\n"
        ),
        "bitacora": (
            "# Bitácora: {title}\n\n"
            "## Trabajo Realizado\n\n- [Item 1]\n- [Item 2]\n\n"
            "## Problemas Encontrados\n\n- [Problema 1]\n\n"
            "## Próximos Pasos\n\n- [Paso 1]\n"
        ),
        "investigation": (
            "# Investigación: {title}\n\n"
            "## Hipótesis\n\n[Hipótesis inicial]\n\n"
            "## Evidencia\n\n[Evidencia recopilada]\n\n"
            "## Análisis\n\n[Análisis de evidencia]\n\n"
            "## Conclusiones\n\n[Conclusiones]\n\n"
            "## Lecciones Aprendidas\n\n[Lecciones]\n"
        ),
        "decision": (
            "# ADR: {title}\n\n"
            "## Contexto\n\n[Situación que motiva la decisión]\n\n"
            "## Decisión\n\n[Decisión tomada]\n\n"
            "## Alternativas Consideradas\n\n1. [Alternativa 1] — [Por qué se descartó]\n2. [Alternativa 2]\n\n"
            "## Justificación\n\n[Por qué esta decisión]\n\n"
            "## Consecuencias\n\n[Impacto esperado]\n"
        ),
        "runbook": (
            "# Runbook: {title}\n\n"
            "## Objetivo\n\n[Objetivo del procedimiento]\n\n"
            "## Prerrequisitos\n\n- [Req 1]\n- [Req 2]\n\n"
            "## Procedimiento\n\n1. [Paso 1]\n2. [Paso 2]\n\n"
            "## Verificación\n\n```bash\n[comando]\n```\n\n"
            "## Rollback\n\n[Procedimiento de rollback]\n"
        ),
    }

    template_body = templates.get(template_type, "# {title}\n\n[Contenido]\n")
    content = template_body.replace("{title}", title)

    return create_document(
        title=title,
        content=content,
        doc_type=template_type,
        project=project,
        tags=tags or [template_type],
        author=author,
        filename=filename,
    )


def move_document(path: str, new_category: str, new_filename: str = "") -> dict[str, Any]:
    """Mueve documento a otra clasificación/directorio, actualiza frontmatter."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)

    if not resolved.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {resolved}")

    raw = resolved.read_text(encoding="utf-8", errors="replace")
    post = frontmatter.loads(raw)

    new_dir = get_directory_for_category(new_category, settings.resolved_custom_categories_path)
    target_dir = settings.root_path / new_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = new_filename or resolved.name
    target_path = target_dir / filename

    post.metadata["type"] = new_category
    post.metadata["timestamp"] = _now_iso()

    target_path.write_text(frontmatter.dumps(post), encoding="utf-8")
    resolved.unlink()

    return {
        "old_path": str(resolved),
        "new_path": str(target_path),
        "new_category": new_category,
        "moved": True,
        "timestamp": post.metadata.get("timestamp"),
    }
