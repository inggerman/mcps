"""Sandboxed filesystem operations."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

from mcp_shared.errors import ValidationError


def resolve_path(root: Path, requested: str, must_exist: bool = True) -> Path:
    base = root.expanduser().resolve()
    candidate = (
        (base / requested).resolve()
        if not Path(requested).is_absolute()
        else Path(requested).resolve()
    )
    if not candidate.is_relative_to(base):
        raise ValidationError(field="path", message="La ruta está fuera de FILESYSTEM_ROOT.")
    if must_exist and not candidate.exists():
        raise ValidationError(field="path", message=f"La ruta no existe: {requested}")
    return candidate


def list_directory(
    root: Path,
    path: str = ".",
    recursive: bool = False,
    max_results: int = 500,
) -> list[dict[str, Any]]:
    directory = resolve_path(root, path)
    if not directory.is_dir():
        raise ValidationError(field="path", message="La ruta no es un directorio.")
    iterator = directory.rglob("*") if recursive else directory.iterdir()
    results: list[dict[str, Any]] = []
    for item in sorted(iterator):
        stat = item.stat()
        results.append(
            {
                "path": str(item.relative_to(root.resolve())),
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size,
                "modified": stat.st_mtime,
            }
        )
        if len(results) >= max_results:
            break
    return results


def read_text_file(root: Path, path: str, max_bytes: int) -> dict[str, Any]:
    file_path = resolve_path(root, path)
    if not file_path.is_file():
        raise ValidationError(field="path", message="La ruta no es un archivo.")
    raw = file_path.read_bytes()
    truncated = len(raw) > max_bytes
    selected = raw[:max_bytes]
    return {
        "path": str(file_path.relative_to(root.resolve())),
        "content": selected.decode("utf-8", errors="replace"),
        "size": len(raw),
        "truncated": truncated,
    }


def search_files(
    root: Path,
    pattern: str = "*",
    text_query: str | None = None,
    max_results: int = 500,
    max_read_bytes: int = 2 * 1024 * 1024,
) -> list[dict[str, Any]]:
    if not pattern:
        raise ValidationError(field="pattern", message="El patrón no puede estar vacío.")
    results: list[dict[str, Any]] = []
    for item in root.resolve().rglob("*"):
        if not item.is_file() or not fnmatch.fnmatch(item.name, pattern):
            continue
        if text_query is not None:
            raw = item.read_bytes()[:max_read_bytes]
            if text_query.casefold() not in raw.decode("utf-8", errors="ignore").casefold():
                continue
        results.append({"path": str(item.relative_to(root.resolve())), "size": item.stat().st_size})
        if len(results) >= max_results:
            break
    return results


def write_text_file(
    root: Path,
    path: str,
    content: str,
    allow_write: bool,
    overwrite: bool = False,
) -> dict[str, Any]:
    if not allow_write:
        raise ValidationError(
            field="write",
            message="La escritura está deshabilitada. Configura FILESYSTEM_ALLOW_WRITE=true.",
        )
    file_path = resolve_path(root, path, must_exist=False)
    if file_path.exists() and not overwrite:
        raise ValidationError(field="overwrite", message="El archivo ya existe.")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return {
        "path": str(file_path.relative_to(root.resolve())),
        "bytes_written": len(content.encode()),
    }
