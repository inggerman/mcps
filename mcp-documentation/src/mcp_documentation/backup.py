"""Backup, restore y export del document store."""

from __future__ import annotations

import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp_shared.errors import NotFoundError, ValidationError


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _backup_dir(root_path: Path) -> Path:
    return root_path / ".backups"


def backup_documents(root_path: Path, include_versions: bool = True, include_audit: bool = True) -> dict[str, Any]:
    """Crea un backup ZIP del document store completo."""
    if not root_path.exists():
        raise NotFoundError(resource="root_path", identifier=str(root_path))

    backups_dir = _backup_dir(root_path)
    backups_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    zip_name = f"mcp-doc-backup-{timestamp}.zip"
    zip_path = backups_dir / zip_name

    allowed_exts = {".md", ".yaml", ".yml", ".xml", ".txt", ".json", ".docx", ".pdf", ".mmd", ".puml"}
    file_count = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in root_path.rglob("*"):
            if f.is_file():
                rel = f.relative_to(root_path)
                rel_str = str(rel)

                # Skip internal dirs unless explicitly requested
                if rel_str.startswith(".versions") and not include_versions:
                    continue
                if rel_str.startswith(".audit") and not include_audit:
                    continue
                if rel_str.startswith(".backups"):
                    continue  # Never include backups inside backups

                # Include allowed docs + internal metadata
                if f.suffix.lower() in allowed_exts or rel_str.startswith("."):
                    zf.write(f, rel_str)
                    file_count += 1

    stat = zip_path.stat()
    return {
        "backup_file": str(zip_path),
        "backup_name": zip_name,
        "files_included": file_count,
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "timestamp": _now_iso(),
        "include_versions": include_versions,
        "include_audit": include_audit,
    }


def restore_backup(root_path: Path, backup_file: str) -> dict[str, Any]:
    """Restaura documentos desde un archivo ZIP de backup."""
    bp = Path(backup_file)
    if not bp.is_absolute():
        bp = _backup_dir(root_path) / backup_file

    if not bp.exists():
        raise NotFoundError(resource="backup", identifier=str(bp))

    if not zipfile.is_zipfile(bp):
        raise ValidationError("El archivo no es un ZIP válido")

    restored_count = 0
    with zipfile.ZipFile(bp, "r") as zf:
        for member in zf.namelist():
            if member.startswith(".backups"):
                continue
            target = root_path / member
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(member))
            restored_count += 1

    return {
        "backup_file": str(bp),
        "files_restored": restored_count,
        "timestamp": _now_iso(),
    }


def export_documents(
    root_path: Path,
    output_path: str = "",
    category: str = "",
    directory: str = "",
) -> dict[str, Any]:
    """Exporta documentos a un ZIP. Opcionalmente filtra por categoría o directorio."""
    if not root_path.exists():
        raise NotFoundError(resource="root_path", identifier=str(root_path))

    if not output_path:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        suffix = f"-{category}" if category else ""
        output_path = str(root_path / f"mcp-doc-export{suffix}-{timestamp}.zip")

    op = Path(output_path)
    allowed_exts = {".md", ".yaml", ".yml", ".xml", ".txt", ".json", ".docx", ".pdf", ".mmd", ".puml"}

    search_dir = root_path
    if directory:
        search_dir = root_path / directory
        if not search_dir.exists():
            raise NotFoundError(resource="directory", identifier=directory)

    file_count = 0
    with zipfile.ZipFile(op, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in search_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in allowed_exts:
                # Skip internal dirs
                rel = f.relative_to(root_path)
                rel_str = str(rel)
                if rel_str.startswith("."):
                    continue

                # Category filter: check frontmatter type
                if category and f.suffix.lower() == ".md":
                    try:
                        import frontmatter
                        post = frontmatter.load(f)
                        if post.metadata.get("type", "").lower() != category.lower():
                            continue
                    except Exception:
                        continue

                zf.write(f, rel_str)
                file_count += 1

    stat = op.stat()
    return {
        "export_file": str(op),
        "files_exported": file_count,
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "category_filter": category or None,
        "directory_filter": directory or None,
        "timestamp": _now_iso(),
    }


def list_backups(root_path: Path) -> list[dict[str, Any]]:
    """Lista los backups disponibles."""
    backups_dir = _backup_dir(root_path)
    if not backups_dir.exists():
        return []

    backups: list[dict[str, Any]] = []
    for f in sorted(backups_dir.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True):
        stat = f.stat()
        backups.append({
            "name": f.name,
            "path": str(f),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
        })
    return backups
