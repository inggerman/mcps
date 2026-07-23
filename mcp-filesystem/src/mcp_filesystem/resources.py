"""Resources de solo lectura para mcp-filesystem.

Expone metadatos, consejos y vistas de archivos/directorios como URIs
accesibles para el modelo a través de `@mcp.resource`.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import stat as stat_module
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp_shared.errors import ValidationError

from mcp_filesystem.tools.filesystem_tools import resolve_path


# ---------------------------------------------------------------------------
# Resources estáticos
# ---------------------------------------------------------------------------


def supported_operations() -> str:
    """Lista de operaciones soportadas por el servidor."""
    return json.dumps(
        {
            "read": ["list", "read_text", "search", "head", "tail", "file_info", "tree"],
            "write": ["write_text", "append_text", "create_directory", "delete", "copy", "move"],
            "settings": {
                "allow_write_env": "FILESYSTEM_ALLOW_WRITE",
                "max_read_bytes_env": "FILESYSTEM_MAX_READ_BYTES",
                "max_results_env": "FILESYSTEM_MAX_RESULTS",
            },
        },
        indent=2,
        ensure_ascii=False,
    )


def path_conventions() -> str:
    """Convenciones de rutas soportadas."""
    return (
        "# Convenciones de rutas\n\n"
        "- Las rutas son relativas a FILESYSTEM_ROOT.\n"
        "- Use `/` como separador (también en Windows).\n"
        "- `.` se refiere a la raíz del sandbox.\n"
        "- `..` está prohibido: no se puede escapar del sandbox.\n"
        "- Las rutas absolutas se resuelven dentro del root.\n"
        "- Los symlinks fuera del root son bloqueados."
    )


def security_tips() -> str:
    """Consejos de seguridad para filesystem sandbox."""
    return (
        "# Seguridad del sandbox\n\n"
        "- FILESYSTEM_ROOT define el directorio raíz del sandbox.\n"
        "- FILESYSTEM_ALLOW_WRITE=false por defecto (solo lectura).\n"
        "- Las rutas se validan contra path traversal (../).\n"
        "- FILESYSTEM_MAX_READ_BYTES limita el tamaño de lectura (default 2 MB).\n"
        "- FILESYSTEM_MAX_RESULTS limita resultados de list/search (default 500).\n"
        "- Habilita escritura solo si confías en el modelo."
    )


def common_file_types() -> str:
    """Tipos de archivo comunes y sus extensiones."""
    types = {
        "text": [".txt", ".md", ".rst", ".log", ".csv", ".tsv", ".ini", ".cfg", ".yaml", ".yml", ".json", ".xml", ".toml"],
        "code": [".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".sh", ".ps1", ".bat"],
        "web": [".html", ".css", ".scss", ".vue", ".jsx", ".tsx"],
        "data": [".csv", ".json", ".xml", ".parquet", ".xlsx", ".xls", ".ods"],
        "config": [".env", ".ini", ".cfg", ".toml", ".yaml", ".yml", ".conf"],
        "binary": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico", ".pdf", ".zip", ".tar", ".gz"],
    }
    return json.dumps({"file_types": types}, indent=2, ensure_ascii=False)


def encoding_tips() -> str:
    """Consejos sobre encoding de archivos."""
    return (
        "# Encoding de archivos\n\n"
        "- Los archivos se leen como UTF-8 por defecto.\n"
        "- Si hay caracteres extraños, el servidor usa `errors='replace'`.\n"
        "- Para archivos binarios, usa `file_info` para ver el tipo MIME.\n"
        "- Guarda archivos siempre en UTF-8 para máxima compatibilidad.\n"
        "- El BOM (Byte Order Mark) se preserva al leer."
    )


def search_patterns_guide() -> str:
    """Guía de patrones de búsqueda soportados."""
    return (
        "# Patrones de búsqueda\n\n"
        "- Se usan patrones glob estilo fnmatch (como shell).\n"
        "- `*.py` — todos los archivos Python.\n"
        "- `*.json` — todos los JSON.\n"
        "- `test_*` — archivos que empiezan con test_.\n"
        "- `*.{py,js}` no soportado; usa llamadas separadas.\n"
        "- `text_query` busca texto dentro de los archivos (case-insensitive).\n"
        "- Los resultados se limitan a FILESYSTEM_MAX_RESULTS."
    )


def best_practices_naming() -> str:
    """Buenas prácticas para nombrado de archivos."""
    return (
        "# Nombrado de archivos\n\n"
        "- Usa minúsculas y guiones para directorios: `my-project/`.\n"
        "- Evita espacios y caracteres especiales en nombres.\n"
        "- Usa extensiones estándar: `.py`, `.json`, `.md`.\n"
        "- Prefiere `kebab-case` para archivos de configuración.\n"
        "- Usa `snake_case` para scripts Python.\n"
        "- Incluye la fecha en logs: `app-2024-01-15.log`."
    )


def example_tree() -> str:
    """Ejemplo de salida del comando tree."""
    return (
        "project/\n"
        "  src/\n"
        "    main.py\n"
        "    utils.py\n"
        "  tests/\n"
        "    test_main.py\n"
        "  README.md\n"
        "  pyproject.toml\n"
        "  .env"
    )


def example_file_listing() -> str:
    """Ejemplo de salida de list_directory en JSON."""
    return json.dumps(
        [
            {"path": "src/main.py", "type": "file", "size": 2048, "modified": 1705312200.0},
            {"path": "src/utils.py", "type": "file", "size": 1024, "modified": 1705312200.0},
            {"path": "tests", "type": "directory", "size": 0, "modified": 1705312200.0},
        ],
        indent=2,
        ensure_ascii=False,
    )


def permissions_guide() -> str:
    """Guía de permisos de archivos."""
    return (
        "# Permisos de archivos\n\n"
        "- `r` — lectura (4)\n"
        "- `w` — escritura (2)\n"
        "- `x` — ejecución (1)\n"
        "- Formato octal: `rwxr-xr--` = 754\n"
        "- El servidor respeta los permisos del SO.\n"
        "- Si FILESYSTEM_ALLOW_WRITE=false, la escritura está bloqueada a nivel MCP."
    )


def disk_usage_tips() -> str:
    """Consejos sobre uso de disco."""
    return (
        "# Uso de disco\n\n"
        "- Usa `directory_size` para ver el tamaño total de un directorio.\n"
        "- `file_info` muestra el tamaño individual de cada archivo.\n"
        "- `list_directory` incluye el tamaño de cada item.\n"
        "- Para encontrar archivos grandes, usa `search_files` con patrón `*`.\n"
        "- Los tamaños se reportan en bytes."
    )


def symlink_tips() -> str:
    """Consejos sobre symlinks."""
    return (
        "# Symlinks\n\n"
        "- Los symlinks dentro del sandbox son seguidos.\n"
        "- Los symlinks que apuntan fuera del sandbox son bloqueados.\n"
        "- `is_symlink` en `file_info` indica si es un link simbólico.\n"
        "- El servidor resuelve la ruta real antes de validar el sandbox.\n"
        "- No se pueden crear symlinks desde el MCP."
    )


# ---------------------------------------------------------------------------
# Resources dinámicos sobre archivos/directorios
# ---------------------------------------------------------------------------


def _safe_resolve(root: Path, path: str) -> Path:
    return resolve_path(root, path)


def file_info(root: Path, path: str) -> str:
    """Información detallada de un archivo o directorio."""
    file_path = _safe_resolve(root, path)
    stat = file_path.stat()
    is_dir = file_path.is_dir()
    mime_type, _ = mimetypes.guess_type(str(file_path))
    info = {
        "path": str(file_path.relative_to(root.resolve())),
        "absolute_path": str(file_path),
        "type": "directory" if is_dir else "file",
        "size": stat.st_size,
        "size_human": _human_size(stat.st_size),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "permissions": stat_module.filemode(stat.st_mode),
        "is_symlink": file_path.is_symlink(),
        "mime_type": mime_type if not is_dir else None,
        "extension": file_path.suffix if not is_dir else None,
    }
    return json.dumps(info, indent=2, ensure_ascii=False)


def file_head(root: Path, path: str, n: int = 20) -> str:
    """Primeras n líneas de un archivo de texto."""
    file_path = _safe_resolve(root, path)
    if not file_path.is_file():
        raise ValidationError(field="path", message="La ruta no es un archivo.")
    content = file_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")[:n]
    return "\n".join(lines)


def file_tail(root: Path, path: str, n: int = 20) -> str:
    """Últimas n líneas de un archivo de texto."""
    file_path = _safe_resolve(root, path)
    if not file_path.is_file():
        raise ValidationError(field="path", message="La ruta no es un archivo.")
    content = file_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")[-n:]
    return "\n".join(lines)


def directory_tree(root: Path, path: str = ".", max_depth: int = 3) -> str:
    """Estructura de árbol de un directorio."""
    dir_path = _safe_resolve(root, path)
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


def directory_size(root: Path, path: str = ".") -> str:
    """Tamaño total de un directorio recursivamente."""
    dir_path = _safe_resolve(root, path)
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
    return json.dumps(
        {
            "path": str(dir_path.relative_to(root.resolve())),
            "total_size_bytes": total_bytes,
            "total_size_human": _human_size(total_bytes),
            "file_count": file_count,
            "directory_count": dir_count,
        },
        indent=2,
        ensure_ascii=False,
    )


def file_hash(root: Path, path: str, algorithm: str = "sha256") -> str:
    """Hash de un archivo (sha256, sha1, md5)."""
    file_path = _safe_resolve(root, path)
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
    return json.dumps(
        {
            "path": str(file_path.relative_to(root.resolve())),
            "algorithm": algorithm,
            "hash": hasher.hexdigest(),
        },
        indent=2,
        ensure_ascii=False,
    )


def file_line_count(root: Path, path: str) -> str:
    """Número de líneas, palabras y caracteres de un archivo de texto."""
    file_path = _safe_resolve(root, path)
    if not file_path.is_file():
        raise ValidationError(field="path", message="La ruta no es un archivo.")
    content = file_path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")
    words = content.split()
    return json.dumps(
        {
            "path": str(file_path.relative_to(root.resolve())),
            "lines": len(lines),
            "words": len(words),
            "characters": len(content),
            "bytes": len(content.encode("utf-8")),
        },
        indent=2,
        ensure_ascii=False,
    )


def directory_listing(root: Path, path: str = ".") -> str:
    """Listado de directorio en formato JSON detallado."""
    from mcp_filesystem.tools.filesystem_tools import list_directory

    result = list_directory(root, path, recursive=False)
    return json.dumps(
        {"path": path, "items": result, "count": len(result)},
        indent=2,
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"
