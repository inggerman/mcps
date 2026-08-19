"""Diagram Tools — 4 herramientas para generación de diagramas."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp_documentation.config import settings


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _diagrams_dir() -> Path:
    d = settings.root_path / "diagrams"
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_mermaid_diagram(
    title: str,
    definition: str,
    filename: str = "",
) -> dict[str, Any]:
    """Crea diagrama Mermaid desde texto (.mmd).

    Soporta flowchart, sequence, class, state, ER, etc.
    """
    if not definition or len(definition.strip()) < 10:
        raise ValueError("La definición del diagrama debe tener al menos 10 caracteres.")

    if not filename:
        safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in title.lower())
        filename = f"{safe_title}.mmd"

    file_path = _diagrams_dir() / filename

    content = f"%% {title}\n%% Generated: {_now_iso()}\n{definition}\n"
    file_path.write_text(content, encoding="utf-8")

    return {
        "path": str(file_path),
        "title": title,
        "format": "mmd",
        "created": True,
        "timestamp": _now_iso(),
    }


def create_plantuml_diagram(
    title: str,
    definition: str,
    filename: str = "",
) -> dict[str, Any]:
    """Crea diagrama PlantUML desde texto (.puml)."""
    if not definition or len(definition.strip()) < 10:
        raise ValueError("La definición del diagrama debe tener al menos 10 caracteres.")

    if not filename:
        safe_title = "".join(c if c.isalnum() or c in "-_" else "-" for c in title.lower())
        filename = f"{safe_title}.puml"

    file_path = _diagrams_dir() / filename

    if not definition.strip().startswith("@start"):
        definition = f"@startuml\n' {title}\n{definition}\n@enduml"

    content = f"' {title}\n' Generated: {_now_iso()}\n{definition}\n"
    file_path.write_text(content, encoding="utf-8")

    return {
        "path": str(file_path),
        "title": title,
        "format": "puml",
        "created": True,
        "timestamp": _now_iso(),
    }


def embed_diagram_in_md(
    md_path: str,
    diagram_path: str,
    caption: str = "",
    position: str = "end",
) -> dict[str, Any]:
    """Embebe diagrama en archivo Markdown con code block apropiado."""
    md_resolved = Path(md_path)
    if not md_resolved.is_absolute():
        md_resolved = (settings.root_path / md_path).resolve()

    diagram_resolved = Path(diagram_path)
    if not diagram_resolved.is_absolute():
        diagram_resolved = (settings.root_path / diagram_path).resolve()

    if not md_resolved.exists():
        raise FileNotFoundError(f"Archivo Markdown no encontrado: {md_resolved}")
    if not diagram_resolved.exists():
        raise FileNotFoundError(f"Diagrama no encontrado: {diagram_resolved}")

    diagram_content = diagram_resolved.read_text(encoding="utf-8").strip()
    suffix = diagram_resolved.suffix.lower()

    if suffix == ".mmd":
        lang = "mermaid"
    elif suffix == ".puml":
        lang = "plantuml"
    else:
        lang = ""

    embed_block = f"```{lang}\n{diagram_content}\n```"
    if caption:
        embed_block = f"**{caption}**\n\n{embed_block}"

    raw = md_resolved.read_text(encoding="utf-8")
    if position == "end":
        new_content = raw.rstrip() + "\n\n" + embed_block + "\n"
    else:
        lines = raw.splitlines()
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("# "):
                insert_idx = i + 1
                break
        lines.insert(insert_idx, "")
        lines.insert(insert_idx, embed_block)
        new_content = "\n".join(lines)

    md_resolved.write_text(new_content, encoding="utf-8")

    return {
        "md_path": str(md_resolved),
        "diagram_path": str(diagram_resolved),
        "embedded": True,
        "language": lang,
    }


def list_diagrams() -> list[dict[str, Any]]:
    """Lista todos los diagramas en el directorio de diagrams con metadata."""
    d = _diagrams_dir()
    results: list[dict[str, Any]] = []

    for f in sorted(d.glob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() not in (".mmd", ".puml", ".svg", ".png", ".pdf"):
            continue
        stat = f.stat()
        results.append({
            "path": str(f),
            "filename": f.name,
            "format": f.suffix.lower().lstrip("."),
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=None).isoformat(),
        })

    return results
