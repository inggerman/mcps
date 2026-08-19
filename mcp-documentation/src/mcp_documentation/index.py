"""Índice de búsqueda full-text usando SQLite FTS5.

Indexa documentos .md, .yaml, .xml, .txt, .json con metadata
extraída del frontmatter. Búsqueda con ranking BM25.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import frontmatter


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _get_db_path(index_path: Path) -> Path:
    """Retorna la ruta del archivo SQLite del índice."""
    index_path.mkdir(parents=True, exist_ok=True)
    return index_path / "docs.db"


def _connect(index_path: Path) -> sqlite3.Connection:
    """Crea/conecta la base de datos del índice."""
    db_path = _get_db_path(index_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Inicializa el esquema FTS5 si no existe."""
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
            path UNINDEXED,
            title,
            content,
            category UNINDEXED,
            tags UNINDEXED,
            timestamp UNINDEXED,
            file_type UNINDEXED,
            tokenize='porter unicode61'
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS docs_meta (
            path TEXT PRIMARY KEY,
            title TEXT,
            category TEXT,
            tags TEXT,
            timestamp TEXT,
            file_type TEXT,
            size_bytes INTEGER,
            indexed_at TEXT
        )
        """
    )
    conn.commit()


def _extract_text_from_file(path: Path) -> tuple[str, dict[str, Any]]:
    """Extrae texto plano y frontmatter de un archivo.

    Returns:
        (texto_plano, frontmatter_dict)
    """
    suffix = path.suffix.lower()
    raw = path.read_text(encoding="utf-8", errors="replace")

    fm_data: dict[str, Any] = {}
    text = raw

    if suffix == ".md":
        post = frontmatter.loads(raw)
        fm_data = dict(post.metadata)
        text = post.content
    elif suffix in (".yaml", ".yml"):
        text = raw
    elif suffix == ".json":
        try:
            data = json.loads(raw)
            text = json.dumps(data, ensure_ascii=False)
        except json.JSONDecodeError:
            text = raw
    elif suffix == ".xml":
        text = re.sub(r"<[^>]+>", " ", raw)
    elif suffix == ".txt":
        text = raw

    return text, fm_data


def index_document(
    file_path: Path,
    root_path: Path,
    index_path: Path,
) -> dict[str, Any]:
    """Indexa un documento individual en el FTS.

    Returns:
        Dict con metadata del documento indexado.
    """
    try:
        rel_path = str(file_path.relative_to(root_path))
    except ValueError:
        rel_path = str(file_path)

    text, fm_data = _extract_text_from_file(file_path)
    title = fm_data.get("title") or file_path.stem
    category = fm_data.get("type", "information")
    tags = ",".join(fm_data.get("tags", [])) if isinstance(fm_data.get("tags"), list) else str(fm_data.get("tags", ""))
    timestamp = fm_data.get("timestamp", _now_iso())
    file_type = file_path.suffix.lower().lstrip(".")
    size = file_path.stat().st_size

    conn = _connect(index_path)
    try:
        conn.execute("DELETE FROM docs_fts WHERE path = ?", (rel_path,))
        conn.execute("DELETE FROM docs_meta WHERE path = ?", (rel_path,))
        conn.execute(
            "INSERT INTO docs_fts (path, title, content, category, tags, timestamp, file_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (rel_path, str(title), text, str(category), tags, str(timestamp), file_type),
        )
        conn.execute(
            "INSERT INTO docs_meta (path, title, category, tags, timestamp, file_type, size_bytes, indexed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (rel_path, str(title), str(category), tags, str(timestamp), file_type, size, _now_iso()),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "path": rel_path,
        "title": title,
        "category": category,
        "indexed": True,
    }


def index_all(
    root_path: Path,
    index_path: Path,
    allowed_extensions: list[str],
) -> dict[str, Any]:
    """Indexa todos los documentos en root_path.

    Returns:
        Dict con: total_indexed, errors, skipped, duration_ms
    """
    start = datetime.now(UTC)
    indexed = 0
    errors: list[dict[str, str]] = []
    skipped = 0

    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in allowed_extensions:
            continue
        if ".index" in file_path.parts:
            skipped += 1
            continue
        try:
            index_document(file_path, root_path, index_path)
            indexed += 1
        except Exception as exc:
            errors.append({"path": str(file_path), "error": str(exc)[:200]})

    duration = (datetime.now(UTC) - start).total_seconds() * 1000
    return {
        "total_indexed": indexed,
        "errors": errors,
        "skipped": skipped,
        "duration_ms": round(duration, 2),
    }


def search_documents(
    query: str,
    index_path: Path,
    limit: int = 20,
    category_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Busca documentos con FTS5 y ranking BM25.

    Returns:
        Lista de dicts con: path, title, category, score, snippet
    """
    if not query or len(query) < 2:
        return []

    limit = max(1, min(limit, 100))

    conn = _connect(index_path)
    try:
        if category_filter:
            sql = """
                SELECT f.path, f.title, f.category, f.tags, f.timestamp,
                       bm25(docs_fts) as score,
                       snippet(docs_fts, 2, '<<', '>>', '...', 20) as snippet
                FROM docs_fts f
                WHERE docs_fts MATCH ? AND f.category = ?
                ORDER BY score
                LIMIT ?
            """
            rows = conn.execute(sql, (query, category_filter, limit)).fetchall()
        else:
            sql = """
                SELECT f.path, f.title, f.category, f.tags, f.timestamp,
                       bm25(docs_fts) as score,
                       snippet(docs_fts, 2, '<<', '>>', '...', 20) as snippet
                FROM docs_fts f
                WHERE docs_fts MATCH ?
                ORDER BY score
                LIMIT ?
            """
            rows = conn.execute(sql, (query, limit)).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "path": row[0],
                    "title": row[1],
                    "category": row[2],
                    "tags": row[3],
                    "timestamp": row[4],
                    "score": round(row[5], 4),
                    "snippet": row[6],
                }
            )
        return results
    finally:
        conn.close()


def get_index_stats(index_path: Path) -> dict[str, Any]:
    """Retorna estadísticas del índice."""
    conn = _connect(index_path)
    try:
        total = conn.execute("SELECT COUNT(*) FROM docs_meta").fetchone()[0]
        by_category: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for row in conn.execute("SELECT category, COUNT(*) FROM docs_meta GROUP BY category").fetchall():
            by_category[row[0]] = row[1]
        for row in conn.execute("SELECT file_type, COUNT(*) FROM docs_meta GROUP BY file_type").fetchall():
            by_type[row[0]] = row[1]
        last_indexed = conn.execute("SELECT MAX(indexed_at) FROM docs_meta").fetchone()[0]
        db_size = _get_db_path(index_path).stat().st_size if _get_db_path(index_path).exists() else 0
        return {
            "total_documents": total,
            "by_category": by_category,
            "by_file_type": by_type,
            "last_indexed": last_indexed,
            "index_size_bytes": db_size,
        }
    finally:
        conn.close()


def rebuild_index(
    root_path: Path,
    index_path: Path,
    allowed_extensions: list[str],
) -> dict[str, Any]:
    """Reconstruye el índice desde cero."""
    db_path = _get_db_path(index_path)
    if db_path.exists():
        db_path.unlink()
    # Also remove WAL/SHM files
    for suffix in ("-wal", "-shm"):
        wal = Path(str(db_path) + suffix)
        if wal.exists():
            wal.unlink()
    return index_all(root_path, index_path, allowed_extensions)


def suggest_similar_documents(
    file_path: Path,
    root_path: Path,
    index_path: Path,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Encuentra documentos similares basado en contenido y tags."""
    try:
        rel_path = str(file_path.relative_to(root_path))
    except ValueError:
        rel_path = str(file_path)

    text, fm_data = _extract_text_from_file(file_path)
    tags = fm_data.get("tags", [])
    if isinstance(tags, list):
        tag_str = " ".join(str(t) for t in tags)
    else:
        tag_str = str(tags)

    query_words = text.split()[:30]
    query = " ".join(query_words)
    if tag_str:
        query = f"{query} {tag_str}"

    results = search_documents(query, index_path, limit=limit + 1)
    return [r for r in results if r["path"] != rel_path][:limit]
