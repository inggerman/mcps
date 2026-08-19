"""Versioning y audit log para documentos.

Mantiene historial de versiones en ``<root>/.versions/<doc_path>.<n>.md``
y un audit log JSONL en ``<root>/.audit.log``.
"""

from __future__ import annotations

import difflib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp_shared.errors import NotFoundError, ValidationError


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _versions_dir(root_path: Path) -> Path:
    return root_path / ".versions"


def _audit_log_path(root_path: Path) -> Path:
    return root_path / ".audit.log"


def _relative_path(root_path: Path, file_path: Path) -> str:
    try:
        return str(file_path.relative_to(root_path))
    except ValueError:
        return str(file_path)


def save_version(root_path: Path, file_path: Path, action: str = "update") -> dict[str, Any]:
    """Guarda una snapshot del archivo antes de ser modificado/eliminado."""
    if not file_path.exists():
        raise NotFoundError(resource="file", identifier=str(file_path))

    versions_dir = _versions_dir(root_path)
    rel = _relative_path(root_path, file_path)
    safe_name = rel.replace("/", "__").replace("\\", "__")
    versions_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(versions_dir.glob(f"{safe_name}.*.bak"))
    next_num = len(existing) + 1

    snapshot_path = versions_dir / f"{safe_name}.{next_num:04d}.bak"
    shutil.copy2(file_path, snapshot_path)

    version_entry = {
        "version": next_num,
        "timestamp": _now_iso(),
        "action": action,
        "file": rel,
        "snapshot": str(snapshot_path.name),
    }

    audit(root_path, "version_saved", rel, {"action": action, "version": next_num})
    return version_entry


def get_document_history(root_path: Path, file_path: str) -> list[dict[str, Any]]:
    """Retorna el historial de versiones de un documento."""
    fp = Path(file_path)
    if not fp.is_absolute():
        fp = (root_path / file_path).resolve()

    versions_dir = _versions_dir(root_path)
    rel = _relative_path(root_path, fp)
    safe_name = rel.replace("/", "__").replace("\\", "__")

    snapshots = sorted(versions_dir.glob(f"{safe_name}.*.bak"))
    history: list[dict[str, Any]] = []
    for snap in snapshots:
        parts = snap.stem.split(".")
        version_num = int(parts[-1]) if parts and parts[-1].isdigit() else 0
        stat = snap.stat()
        history.append({
            "version": version_num,
            "timestamp": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
            "snapshot_file": snap.name,
            "size_bytes": stat.st_size,
        })
    return history


def restore_version(root_path: Path, file_path: str, version: int) -> dict[str, Any]:
    """Restaura una versión específica de un documento."""
    fp = Path(file_path)
    if not fp.is_absolute():
        fp = (root_path / file_path).resolve()

    versions_dir = _versions_dir(root_path)
    rel = _relative_path(root_path, fp)
    safe_name = rel.replace("/", "__").replace("\\", "__")

    snapshot = versions_dir / f"{safe_name}.{version:04d}.bak"
    if not snapshot.exists():
        raise NotFoundError(
            resource="version",
            identifier=f"{rel} v{version}",
        )

    if fp.exists():
        save_version(root_path, fp, action="pre-restore")

    shutil.copy2(snapshot, fp)
    audit(root_path, "version_restored", rel, {"version": version})
    return {"restored": rel, "version": version, "timestamp": _now_iso()}


def compare_versions(
    root_path: Path, file_path: str, version_a: int, version_b: int
) -> dict[str, Any]:
    """Compara dos versiones de un documento y retorna un diff unificado."""
    fp = Path(file_path)
    if not fp.is_absolute():
        fp = (root_path / file_path).resolve()

    versions_dir = _versions_dir(root_path)
    rel = _relative_path(root_path, fp)
    safe_name = rel.replace("/", "__").replace("\\", "__")

    snap_a = versions_dir / f"{safe_name}.{version_a:04d}.bak"
    snap_b = versions_dir / f"{safe_name}.{version_b:04d}.bak"

    if not snap_a.exists():
        raise NotFoundError(resource="version", identifier=f"v{version_a}")
    if not snap_b.exists():
        raise NotFoundError(resource="version", identifier=f"v{version_b}")

    lines_a = snap_a.read_text(encoding="utf-8").splitlines(keepends=True)
    lines_b = snap_b.read_text(encoding="utf-8").splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        lines_a, lines_b,
        fromfile=f"{rel} v{version_a}",
        tofile=f"{rel} v{version_b}",
    ))

    return {
        "file": rel,
        "version_a": version_a,
        "version_b": version_b,
        "diff": "".join(diff),
        "lines_changed": len(diff),
    }


def audit(
    root_path: Path,
    action: str,
    target: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Registra un evento en el audit log (JSONL append)."""
    entry = {
        "timestamp": _now_iso(),
        "action": action,
        "target": target,
        "metadata": metadata or {},
    }
    log_path = _audit_log_path(root_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def get_audit_log(
    root_path: Path,
    limit: int = 50,
    action_filter: str | None = None,
    target_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Lee el audit log con filtros opcionales."""
    log_path = _audit_log_path(root_path)
    if not log_path.exists():
        return []

    entries: list[dict[str, Any]] = []
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if action_filter and entry.get("action") != action_filter:
            continue
        if target_filter and entry.get("target") != target_filter:
            continue
        entries.append(entry)
        if len(entries) >= limit:
            break
    return entries
