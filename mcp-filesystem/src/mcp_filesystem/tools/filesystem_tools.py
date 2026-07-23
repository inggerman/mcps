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


def head_lines(
    root: Path, path: str, n: int = 20, max_bytes: int = 2 * 1024 * 1024,
) -> dict[str, Any]:
    """Primeras n líneas de un archivo de texto."""
    data = read_text_file(root, path, max_bytes)
    lines = data["content"].split("\n")[:n]
    return {
        "path": data["path"],
        "lines": lines,
        "returned_lines": len(lines),
        "truncated": data["truncated"],
    }


def tail_lines(
    root: Path, path: str, n: int = 20, max_bytes: int = 2 * 1024 * 1024,
) -> dict[str, Any]:
    """Últimas n líneas de un archivo de texto."""
    data = read_text_file(root, path, max_bytes)
    lines = data["content"].split("\n")[-n:]
    return {
        "path": data["path"],
        "lines": lines,
        "returned_lines": len(lines),
        "truncated": data["truncated"],
    }


def get_file_info(root: Path, path: str) -> dict[str, Any]:
    """Información detallada de un archivo o directorio."""
    import mimetypes
    import stat as stat_module
    from datetime import datetime

    file_path = resolve_path(root, path)
    stat = file_path.stat()
    is_dir = file_path.is_dir()
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return {
        "path": str(file_path.relative_to(root.resolve())),
        "type": "directory" if is_dir else "file",
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "permissions": stat_module.filemode(stat.st_mode),
        "is_symlink": file_path.is_symlink(),
        "mime_type": mime_type if not is_dir else None,
        "extension": file_path.suffix if not is_dir else None,
    }


def directory_tree(
    root: Path, path: str = ".", max_depth: int = 3,
) -> str:
    """Estructura de árbol de un directorio."""
    dir_path = resolve_path(root, path)
    if not dir_path.is_dir():
        raise ValidationError(field="path", message="La ruta no es un directorio.")
    lines: list[str] = []

    def _walk(current: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            items = sorted(current.iterdir())
        except PermissionError:
            return
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{item.name}")
            if item.is_dir():
                extension = "    " if is_last else "│   "
                _walk(item, prefix + extension, depth + 1)

    lines.append(dir_path.name + "/")
    _walk(dir_path, "", 1)
    return "\n".join(lines)


def get_directory_size(root: Path, path: str = ".") -> dict[str, Any]:
    """Tamaño total de un directorio recursivamente."""
    dir_path = resolve_path(root, path)
    if not dir_path.is_dir():
        raise ValidationError(field="path", message="La ruta no es un directorio.")
    total_bytes = 0
    file_count = 0
    dir_count = 0
    for item in dir_path.rglob("*"):
        if item.is_file():
            total_bytes += item.stat().st_size
            file_count += 1
        elif item.is_dir():
            dir_count += 1
    return {
        "path": str(dir_path.relative_to(root.resolve())),
        "total_size_bytes": total_bytes,
        "file_count": file_count,
        "directory_count": dir_count,
    }


def get_file_hash(
    root: Path, path: str, algorithm: str = "sha256",
) -> dict[str, Any]:
    """Hash de un archivo (sha256, sha1, md5)."""
    import hashlib

    file_path = resolve_path(root, path)
    if not file_path.is_file():
        raise ValidationError(field="path", message="La ruta no es un archivo.")
    valid_algos = {"sha256", "sha1", "md5"}
    if algorithm not in valid_algos:
        raise ValidationError(
            field="algorithm",
            message=f"Algoritmo no válido. Soportados: {sorted(valid_algos)}",
        )
    hasher = hashlib.new(algorithm)
    hasher.update(file_path.read_bytes())
    return {
        "path": str(file_path.relative_to(root.resolve())),
        "algorithm": algorithm,
        "hash": hasher.hexdigest(),
    }


def count_lines(root: Path, path: str) -> dict[str, Any]:
    """Número de líneas, palabras y caracteres de un archivo de texto."""
    file_path = resolve_path(root, path)
    if not file_path.is_file():
        raise ValidationError(field="path", message="La ruta no es un archivo.")
    content = file_path.read_text(encoding="utf-8", errors="replace")
    return {
        "path": str(file_path.relative_to(root.resolve())),
        "lines": len(content.split("\n")),
        "words": len(content.split()),
        "characters": len(content),
        "bytes": len(content.encode("utf-8")),
    }


def append_text_file(
    root: Path, path: str, content: str, allow_write: bool,
) -> dict[str, Any]:
    """Anexa texto al final de un archivo."""
    if not allow_write:
        raise ValidationError(
            field="write",
            message="La escritura está deshabilitada. Configura FILESYSTEM_ALLOW_WRITE=true.",
        )
    file_path = resolve_path(root, path, must_exist=False)
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
    else:
        with file_path.open("a", encoding="utf-8") as f:
            f.write(content)
    return {
        "path": str(file_path.relative_to(root.resolve())),
        "bytes_appended": len(content.encode()),
    }


def create_directory(
    root: Path, path: str, allow_write: bool,
) -> dict[str, Any]:
    """Crea un directorio (y subdirectorios) dentro del sandbox."""
    if not allow_write:
        raise ValidationError(
            field="write",
            message="La escritura está deshabilitada. Configura FILESYSTEM_ALLOW_WRITE=true.",
        )
    dir_path = resolve_path(root, path, must_exist=False)
    if dir_path.exists():
        raise ValidationError(field="path", message="El directorio ya existe.")
    dir_path.mkdir(parents=True, exist_ok=False)
    return {"path": str(dir_path.relative_to(root.resolve())), "created": True}


def delete_path(
    root: Path, path: str, allow_write: bool, recursive: bool = False,
) -> dict[str, Any]:
    """Elimina un archivo o directorio del sandbox."""
    if not allow_write:
        raise ValidationError(
            field="write",
            message="La escritura está deshabilitada. Configura FILESYSTEM_ALLOW_WRITE=true.",
        )
    target = resolve_path(root, path)
    if target.is_dir():
        if not recursive:
            try:
                target.rmdir()
            except OSError as exc:
                raise ValidationError(
                    field="recursive",
                    message=f"El directorio no está vacío. Use recursive=true. {exc}",
                ) from exc
        else:
            import shutil
            shutil.rmtree(target)
    else:
        target.unlink()
    return {"path": str(target.relative_to(root.resolve())), "deleted": True}


def copy_path(
    root: Path, src: str, dst: str, allow_write: bool,
) -> dict[str, Any]:
    """Copia un archivo dentro del sandbox."""
    if not allow_write:
        raise ValidationError(
            field="write",
            message="La escritura está deshabilitada. Configura FILESYSTEM_ALLOW_WRITE=true.",
        )
    import shutil

    src_path = resolve_path(root, src)
    dst_path = resolve_path(root, dst, must_exist=False)
    if src_path.is_dir():
        shutil.copytree(src_path, dst_path)
    else:
        shutil.copy2(src_path, dst_path)
    return {
        "src": str(src_path.relative_to(root.resolve())),
        "dst": str(dst_path.relative_to(root.resolve())),
        "copied": True,
    }


def move_path(
    root: Path, src: str, dst: str, allow_write: bool,
) -> dict[str, Any]:
    """Mueve/renombra un archivo o directorio dentro del sandbox."""
    if not allow_write:
        raise ValidationError(
            field="write",
            message="La escritura está deshabilitada. Configura FILESYSTEM_ALLOW_WRITE=true.",
        )
    import shutil

    src_path = resolve_path(root, src)
    dst_path = resolve_path(root, dst, must_exist=False)
    shutil.move(str(src_path), str(dst_path))
    return {
        "src": str(src_path.relative_to(root.resolve())),
        "dst": str(dst_path.relative_to(root.resolve())),
        "moved": True,
    }
