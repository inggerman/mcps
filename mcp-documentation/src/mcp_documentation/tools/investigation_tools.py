"""Investigation Tools — 3 herramientas para gestión de investigaciones."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import frontmatter

from mcp_documentation.config import settings
from mcp_documentation.tools.doc_write_tools import create_document, update_frontmatter, append_to_document


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _investigations_dir() -> Path:
    d = settings.root_path / "investigations"
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_investigation(
    title: str,
    hypothesis: str,
    project: str = "",
    tags: list[str] | None = None,
    author: str = "unknown",
) -> dict[str, Any]:
    """Crea documento de investigación con estructura: hipótesis, evidencia, conclusiones."""
    if not hypothesis or len(hypothesis.strip()) < 10:
        raise ValueError("La hipótesis debe tener al menos 10 caracteres.")

    content = (
        f"## Hipótesis\n\n{hypothesis}\n\n"
        "## Evidencia\n\n_Evidencia pendiente de recopilación._\n\n"
        "## Análisis\n\n_Análisis pendiente._\n\n"
        "## Conclusiones\n\n_Conclusiones pendientes._\n\n"
        "## Lecciones Aprendidas\n\n_Pendiente._\n"
    )

    return create_document(
        title=title,
        content=content,
        doc_type="investigation",
        project=project,
        tags=tags or ["investigation"],
        author=author,
    )


def add_evidence(
    path: str,
    evidence_type: str,
    description: str,
    reference: str = "",
) -> dict[str, Any]:
    """Añade evidencia a una investigación existente.

    Args:
        evidence_type: log, screenshot, code, reference, test, observation
    """
    valid_types = ("log", "screenshot", "code", "reference", "test", "observation")
    if evidence_type not in valid_types:
        raise ValueError(f"Tipos válidos: {', '.join(valid_types)}")

    if not description or len(description.strip()) < 5:
        raise ValueError("La descripción debe tener al menos 5 caracteres.")

    evidence_entry = (
        f"\n### Evidencia [{evidence_type.upper()}] — {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}\n\n"
        f"{description}\n"
    )
    if reference:
        evidence_entry += f"\n**Referencia:** `{reference}`\n"

    return append_to_document(path, evidence_entry)


def close_investigation(
    path: str,
    status: str,
    conclusions: str,
    lessons: str = "",
) -> dict[str, Any]:
    """Cierra investigación: status=resolved/unresolved, conclusiones, lecciones aprendidas.

    Args:
        status: resolved, unresolved, partial
    """
    valid_statuses = ("resolved", "unresolved", "partial")
    if status not in valid_statuses:
        raise ValueError(f"Estados válidos: {', '.join(valid_statuses)}")

    if not conclusions or len(conclusions.strip()) < 10:
        raise ValueError("Las conclusiones deben tener al menos 10 caracteres.")

    closing_content = (
        f"\n---\n\n## Conclusiones (Cierre)\n\n{conclusions}\n"
    )
    if lessons:
        closing_content += f"\n## Lecciones Aprendidas (Cierre)\n\n{lessons}\n"

    append_to_document(path, closing_content)
    fm_update = update_frontmatter(path, {"status": status, "investigation_status": "closed"})

    return {
        "path": fm_update["path"],
        "status": status,
        "closed": True,
        "timestamp": fm_update.get("timestamp"),
    }
