"""Health check y métricas Prometheus para mcp-documentation."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def health_check(root_path: Path, index_path: Path) -> dict[str, Any]:
    """Verifica salud del servidor: filesystem, índice FTS5, permisos."""
    checks: dict[str, Any] = {}

    # Filesystem check
    checks["filesystem"] = {
        "root_path": str(root_path),
        "exists": root_path.exists(),
        "writable": root_path.is_dir() and _is_writable(root_path),
    }

    # Index check
    checks["index"] = {
        "path": str(index_path),
        "exists": index_path.exists(),
        "healthy": _check_index_health(index_path),
    }

    # Document count
    allowed_exts = {".md", ".yaml", ".yml", ".xml", ".txt", ".json", ".docx", ".pdf", ".mmd", ".puml"}
    doc_count = 0
    total_size = 0
    if root_path.exists():
        for f in root_path.rglob("*"):
            if f.is_file() and f.suffix.lower() in allowed_exts:
                doc_count += 1
                total_size += f.stat().st_size

    checks["documents"] = {
        "count": doc_count,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
    }

    # Sessions count
    sessions_dir = root_path / "sessions"
    session_count = len(list(sessions_dir.glob("*.json"))) if sessions_dir.exists() else 0
    checks["sessions"] = {"count": session_count}

    # Versions count
    versions_dir = root_path / ".versions"
    version_count = len(list(versions_dir.glob("*.bak"))) if versions_dir.exists() else 0
    checks["versions"] = {"count": version_count}

    # Audit log
    audit_path = root_path / ".audit.log"
    audit_entries = 0
    if audit_path.exists():
        audit_entries = sum(1 for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip())
    checks["audit"] = {"entries": audit_entries}

    # Overall status
    all_healthy = (
        checks["filesystem"]["exists"]
        and checks["filesystem"]["writable"]
        and checks["index"]["healthy"]
    )
    checks["status"] = "healthy" if all_healthy else "degraded"
    checks["timestamp"] = _now_iso()

    return checks


def _is_writable(path: Path) -> bool:
    try:
        test_file = path / ".health_write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return True
    except Exception:
        return False


def _check_index_health(index_path: Path) -> bool:
    if not index_path.exists():
        return True  # No index yet is OK
    db_file = index_path / "docs.fts" if index_path.is_dir() else index_path
    if not db_file.exists():
        return True
    try:
        conn = sqlite3.connect(str(db_file))
        conn.execute("SELECT count(*) FROM docs_fts").fetchone()
        conn.close()
        return True
    except Exception:
        return False


def get_metrics(root_path: Path, index_path: Path) -> str:
    """Retorna métricas en formato Prometheus text exposition."""
    health = health_check(root_path, index_path)

    lines = [
        "# HELP mcp_documentation_docs_total Total number of documents",
        "# TYPE mcp_documentation_docs_total gauge",
        f"mcp_documentation_docs_total {health['documents']['count']}",
        "",
        "# HELP mcp_documentation_docs_size_mb Total document size in MB",
        "# TYPE mcp_documentation_docs_size_mb gauge",
        f"mcp_documentation_docs_size_mb {health['documents']['total_size_mb']}",
        "",
        "# HELP mcp_documentation_sessions_total Total active sessions",
        "# TYPE mcp_documentation_sessions_total gauge",
        f"mcp_documentation_sessions_total {health['sessions']['count']}",
        "",
        "# HELP mcp_documentation_versions_total Total versioned snapshots",
        "# TYPE mcp_documentation_versions_total gauge",
        f"mcp_documentation_versions_total {health['versions']['count']}",
        "",
        "# HELP mcp_documentation_audit_entries_total Total audit log entries",
        "# TYPE mcp_documentation_audit_entries_total gauge",
        f"mcp_documentation_audit_entries_total {health['audit']['entries']}",
        "",
        "# HELP mcp_documentation_health_status 1=healthy 0=degraded",
        "# TYPE mcp_documentation_health_status gauge",
        f"mcp_documentation_health_status {1 if health['status'] == 'healthy' else 0}",
        "",
    ]
    return "\n".join(lines)
