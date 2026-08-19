"""Doc Read Tools — 10 herramientas para lectura de documentación."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter

from mcp_documentation.config import settings


def _resolve_path(path: str) -> Path:
    """Resuelve una ruta relativa al root_path o absoluta."""
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    return (settings.root_path / path).resolve()


def _ensure_allowed(path: Path) -> None:
    """Verifica que el archivo tenga una extensión permitida."""
    if not settings.is_allowed_extension(path):
        raise ValueError(
            f"Extensión '{path.suffix}' no permitida. "
            f"Extensiones válidas: {settings.extensions_list}"
        )


def _read_file_text(path: Path) -> str:
    """Lee el contenido de un archivo de texto."""
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    if not path.is_file():
        raise ValueError(f"La ruta no es un archivo: {path}")
    size = path.stat().st_size
    if size > settings.max_file_size_mb * 1024 * 1024:
        raise ValueError(
            f"Archivo demasiado grande: {size / 1_048_576:.1f} MB "
            f"(máximo: {settings.max_file_size_mb} MB)"
        )
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Separa frontmatter del body."""
    post = frontmatter.loads(content)
    return dict(post.metadata), post.content


def _extract_title(body: str) -> str | None:
    """Extrae el primer H1 del body."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def read_document(path: str) -> dict[str, Any]:
    """Lee cualquier documento soportado y retorna contenido + metadata + frontmatter."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)
    content = _read_file_text(resolved)

    fm_data, body = _parse_frontmatter(content)
    title = _extract_title(body) or fm_data.get("title") or resolved.stem

    return {
        "path": str(resolved),
        "filename": resolved.name,
        "content": content,
        "frontmatter": fm_data,
        "title": title,
        "body": body,
        "format": resolved.suffix.lower().lstrip("."),
        "size_bytes": resolved.stat().st_size,
    }


def read_document_section(path: str, heading: str, case_sensitive: bool = False) -> dict[str, Any] | None:
    """Lee una sección específica de un documento por heading."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)
    content = _read_file_text(resolved)
    _, body = _parse_frontmatter(content)

    lines = body.splitlines()
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

    start_line: int | None = None
    target_level: int | None = None
    for i, line in enumerate(lines):
        m = heading_pattern.match(line)
        if m:
            h_text = m.group(2).strip()
            match = (h_text == heading) if case_sensitive else (h_text.lower() == heading.lower())
            if match:
                start_line = i
                target_level = len(m.group(1))
                break

    if start_line is None:
        return None

    end_line = len(lines)
    for j in range(start_line + 1, len(lines)):
        m = heading_pattern.match(lines[j])
        if m and len(m.group(1)) <= target_level:
            end_line = j
            break

    section_text = "\n".join(lines[start_line:end_line])
    return {
        "heading": heading,
        "level": target_level,
        "content": section_text,
        "line_start": start_line + 1,
        "line_end": end_line,
    }


def list_documents(directory: str = "", recursive: bool = True) -> list[dict[str, Any]]:
    """Lista documentos en un directorio con metadata."""
    base = _resolve_path(directory) if directory else settings.root_path
    if not base.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {base}")
    if not base.is_dir():
        raise ValueError(f"La ruta no es un directorio: {base}")

    results: list[dict[str, Any]] = []
    pattern = "**/*" if recursive else "*"

    for file_path in sorted(base.glob(pattern)):
        if not file_path.is_file():
            continue
        if not settings.is_allowed_extension(file_path):
            continue
        if ".index" in file_path.parts:
            continue
        stat = file_path.stat()
        if stat.st_size > settings.max_file_size_mb * 1024 * 1024:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            fm_data, body = _parse_frontmatter(content)
            title = fm_data.get("title") or _extract_title(body) or file_path.stem
        except Exception:
            fm_data = {}
            title = file_path.stem

        results.append({
            "path": str(file_path),
            "relative_path": str(file_path.relative_to(settings.root_path)) if file_path.is_relative_to(settings.root_path) else str(file_path),
            "filename": file_path.name,
            "title": title,
            "format": file_path.suffix.lower().lstrip("."),
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=None).isoformat(),
            "frontmatter": fm_data,
            "category": fm_data.get("type", "unknown"),
            "tags": fm_data.get("tags", []),
        })

    return results


def get_document_metadata(path: str) -> dict[str, Any]:
    """Extrae metadata completa: frontmatter, timestamp, tamaño, clasificación, tags."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)
    content = _read_file_text(resolved)
    fm_data, body = _parse_frontmatter(content)
    stat = resolved.stat()

    return {
        "path": str(resolved),
        "filename": resolved.name,
        "title": fm_data.get("title") or _extract_title(body) or resolved.stem,
        "frontmatter": fm_data,
        "format": resolved.suffix.lower().lstrip("."),
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=None).isoformat(),
        "category": fm_data.get("type", "unknown"),
        "tags": fm_data.get("tags", []),
        "timestamp": fm_data.get("timestamp"),
        "status": fm_data.get("status"),
        "author": fm_data.get("author"),
        "project": fm_data.get("project"),
    }


def search_in_document(path: str, query: str, case_sensitive: bool = False) -> list[dict[str, Any]]:
    """Búsqueda texto dentro de un documento con contexto y número de línea."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)
    content = _read_file_text(resolved)
    _, body = _parse_frontmatter(content)

    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(query), flags)

    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
    current_heading: str | None = None
    results: list[dict[str, Any]] = []

    for i, line in enumerate(body.splitlines(), start=1):
        m = heading_pattern.match(line)
        if m:
            current_heading = m.group(2).strip()
        if pattern.search(line):
            results.append({
                "line_number": i,
                "context": line.strip()[:200],
                "heading_context": current_heading,
            })

    return results


def get_document_summary(path: str, max_words: int = 100) -> dict[str, Any]:
    """Resumen automático: título, word count, headings count, primer párrafo."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)
    content = _read_file_text(resolved)
    fm_data, body = _parse_frontmatter(content)

    plain = re.sub(r"```[\s\S]*?```", "", body)
    plain = re.sub(r"`[^`]+`", "", plain)
    plain = re.sub(r"[#*_~`>|]", "", plain)
    words = plain.split()

    heading_pattern = re.compile(r"^#{1,6}\s+(.+)$")
    headings = [m.group(1).strip() for line in body.splitlines() if (m := heading_pattern.match(line))]

    first_para = ""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            first_para = stripped
            break

    summary = " ".join(words[:max_words])
    if len(words) > max_words:
        summary += "..."

    return {
        "path": str(resolved),
        "title": fm_data.get("title") or _extract_title(body) or resolved.stem,
        "summary": summary,
        "first_paragraph": first_para,
        "word_count": len(words),
        "heading_count": len(headings),
        "headings": headings,
        "frontmatter": fm_data,
    }


def get_document_toc(path: str, max_depth: int = 3) -> str:
    """Genera tabla de contenidos desde headings."""
    resolved = _resolve_path(path)
    _ensure_allowed(resolved)
    content = _read_file_text(resolved)
    _, body = _parse_frontmatter(content)

    depth = max(1, min(6, max_depth))
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
    lines: list[str] = []

    for line in body.splitlines():
        m = heading_pattern.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level > depth:
                continue
            indent = "  " * (level - 1)
            anchor = re.sub(r"[^\w\s-]", "", text.lower()).replace(" ", "-").strip("-")
            lines.append(f"{indent}- [{text}](#{anchor})")

    return "\n".join(lines) if lines else "_No se encontraron encabezados._"


def get_recent_documents(limit: int = 20, directory: str = "") -> list[dict[str, Any]]:
    """Lista documentos ordenados por timestamp (más recientes primero)."""
    docs = list_documents(directory=directory, recursive=True)

    def _get_ts(doc: dict[str, Any]) -> str:
        ts = doc.get("frontmatter", {}).get("timestamp")
        if ts:
            return str(ts)
        return doc.get("modified", "")

    docs.sort(key=_get_ts, reverse=True)
    return docs[:limit]


def get_documents_by_category(category: str) -> list[dict[str, Any]]:
    """Filtra documentos por clasificación."""
    docs = list_documents(recursive=True)
    return [d for d in docs if d.get("category", "").lower() == category.lower()]


def get_documents_by_tag(tag: str) -> list[dict[str, Any]]:
    """Filtra documentos por tag específico en frontmatter."""
    docs = list_documents(recursive=True)
    tag_lower = tag.lower()
    return [
        d for d in docs
        if any(
            str(t).lower() == tag_lower
            for t in d.get("tags", [])
        )
    ]
