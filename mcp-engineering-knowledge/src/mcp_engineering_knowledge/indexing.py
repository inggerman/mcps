"""Indexer — incremental index pipeline: scan → hash → diff → chunk → embed → upsert."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp_engineering_knowledge.chunking import chunk_markdown
from mcp_engineering_knowledge.config import settings
from mcp_engineering_knowledge.embedding import embed_batch
from mcp_engineering_knowledge.freshness import build_hash_index, compute_hash, detect_changed_docs
from mcp_engineering_knowledge.qdrant_store import (
    delete_by_file_path,
    ensure_collection,
    get_all_payloads,
    upsert_chunks,
)
from mcp_shared.errors import McpError


def _classify_domain(file_path: str) -> str:
    """Classify a file path into a domain based on its location."""
    parts = file_path.replace("\\", "/").split("/")
    if "governance" in parts:
        return "governance"
    if "manuals" in parts:
        return "manuals"
    if "architecture" in parts:
        return "architecture"
    if "security" in parts:
        return "security"
    if "testing" in parts:
        return "testing"
    return "general"


def _classify_subdomain(file_path: str) -> str:
    """Classify a file path into a subdomain based on its section directory."""
    parts = file_path.replace("\\", "/").split("/")
    # Find the section directory (e.g., "01-architecture", "04-security")
    for part in parts:
        if part and part[0:2].isdigit() and "-" in part:
            return part
    return ""


def _classify_type(frontmatter_type: str, file_path: str) -> str:
    """Classify document type from frontmatter or path."""
    if frontmatter_type:
        return frontmatter_type
    parts = file_path.replace("\\", "/").split("/")
    if "standards" in parts:
        return "standard"
    if "patterns" in parts:
        return "pattern"
    if "manuals" in parts:
        return "manual"
    return "reference"


def _read_frontmatter_field(content: str, field: str) -> str:
    """Extract a field from YAML frontmatter."""
    if not content.startswith("---"):
        return ""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return ""
    for line in parts[1].splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            if key.strip() == field:
                return val.strip().strip('"').strip("'")
    return ""


def index_incremental() -> dict[str, Any]:
    """Run incremental indexing: only re-index changed/new files.

    Returns summary: {total_files, indexed_files, changed, new, deleted, skipped, errors}
    """
    # Ensure collection exists
    ensure_collection()

    # Get current indexed state
    payloads = get_all_payloads()
    indexed_hashes = build_hash_index(payloads)

    # Detect changes
    changes = detect_changed_docs(settings.docs_path, indexed_hashes)

    changed = changes["changed"]
    new_files = changes["new"]
    deleted = changes["deleted"]

    # Delete removed files from Qdrant
    for f in deleted:
        delete_by_file_path(f)

    # Index changed + new files
    to_index = changed + new_files
    total_chunks = 0
    errors: list[str] = []

    root = Path(settings.docs_path)

    # Process in batches of 10 files
    batch_size = 10
    for i in range(0, len(to_index), batch_size):
        batch = to_index[i : i + batch_size]
        all_chunks: list[dict[str, Any]] = []

        for rel_path in batch:
            abs_path = root / rel_path
            try:
                content = abs_path.read_text(encoding="utf-8")
                file_hash = compute_hash(str(abs_path))
                fm_title = _read_frontmatter_field(content, "title")
                fm_type = _read_frontmatter_field(content, "type")
                fm_timestamp = _read_frontmatter_field(content, "timestamp")
                fm_verification = _read_frontmatter_field(content, "verification_status")

                domain = _classify_domain(rel_path)
                subdomain = _classify_subdomain(rel_path)
                doc_type = _classify_type(fm_type, rel_path)

                chunks = chunk_markdown(
                    content,
                    file_path=rel_path,
                    chunk_size=settings.chunk_size,
                    overlap=settings.chunk_overlap,
                )

                # Generate embeddings for this file's chunks
                texts = [c.text for c in chunks]
                if not texts:
                    continue

                vectors = embed_batch(texts)

                for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False)):
                    # Generate a stable ID from file_path + chunk index
                    point_id = abs(hash(f"{rel_path}:{idx}")) % (2**63)
                    all_chunks.append(
                        {
                            "id": point_id,
                            "vector": vector,
                            "payload": {
                                **chunk.metadata,
                                "domain": domain,
                                "subdomain": subdomain,
                                "doc_type": doc_type,
                                "file_hash": file_hash,
                                "title": fm_title or chunk.metadata.get("title", ""),
                                "type": doc_type,
                                "timestamp": fm_timestamp,
                                "verification_status": fm_verification,
                                "last_indexed_at": datetime.now(UTC).isoformat(),
                                "chunk_index": idx,
                            },
                        }
                    )
                total_chunks += len(chunks)
            except Exception as exc:
                errors.append(f"{rel_path}: {exc}")

        if all_chunks:
            upsert_chunks(all_chunks)

    return {
        "total_files_scanned": len(indexed_hashes) + len(new_files),
        "files_indexed": len(to_index),
        "chunks_upserted": total_chunks,
        "changed": changed,
        "new": new_files,
        "deleted": deleted,
        "skipped": len(indexed_hashes) - len(changed),
        "errors": errors,
        "indexed_at": datetime.now(UTC).isoformat(),
    }


def index_full() -> dict[str, Any]:
    """Force full re-index of all documents."""
    # Delete all existing points by clearing the collection
    payloads = get_all_payloads()
    indexed_hashes = build_hash_index(payloads)

    # Delete all files from Qdrant
    for file_path in list(indexed_hashes.keys()):
        delete_by_file_path(file_path)

    # Now index everything as "new"
    changes = detect_changed_docs(settings.docs_path, {})
    # Override: treat all as new
    root = Path(settings.docs_path)
    all_files: list[str] = []
    for p in root.rglob("*.md"):
        rel = str(p.relative_to(root)).replace("\\", "/")
        all_files.append(rel)

    # Temporarily set indexed_hashes to empty so detect_changed_docs returns all as new
    changes = {"changed": [], "new": all_files, "deleted": []}

    # Reuse incremental logic with all files
    to_index = all_files
    total_chunks = 0
    errors: list[str] = []

    batch_size = 10
    for i in range(0, len(to_index), batch_size):
        batch = to_index[i : i + batch_size]
        all_chunks: list[dict[str, Any]] = []

        for rel_path in batch:
            abs_path = root / rel_path
            try:
                content = abs_path.read_text(encoding="utf-8")
                file_hash = compute_hash(str(abs_path))
                fm_title = _read_frontmatter_field(content, "title")
                fm_type = _read_frontmatter_field(content, "type")
                fm_timestamp = _read_frontmatter_field(content, "timestamp")
                fm_verification = _read_frontmatter_field(content, "verification_status")

                domain = _classify_domain(rel_path)
                subdomain = _classify_subdomain(rel_path)
                doc_type = _classify_type(fm_type, rel_path)

                chunks = chunk_markdown(
                    content,
                    file_path=rel_path,
                    chunk_size=settings.chunk_size,
                    overlap=settings.chunk_overlap,
                )

                texts = [c.text for c in chunks]
                if not texts:
                    continue

                vectors = embed_batch(texts)

                for idx, (chunk, vector) in enumerate(zip(chunks, vectors, strict=False)):
                    point_id = abs(hash(f"{rel_path}:{idx}")) % (2**63)
                    all_chunks.append(
                        {
                            "id": point_id,
                            "vector": vector,
                            "payload": {
                                **chunk.metadata,
                                "domain": domain,
                                "subdomain": subdomain,
                                "doc_type": doc_type,
                                "file_hash": file_hash,
                                "title": fm_title or chunk.metadata.get("title", ""),
                                "type": doc_type,
                                "timestamp": fm_timestamp,
                                "verification_status": fm_verification,
                                "last_indexed_at": datetime.now(UTC).isoformat(),
                                "chunk_index": idx,
                            },
                        }
                    )
                total_chunks += len(chunks)
            except Exception as exc:
                errors.append(f"{rel_path}: {exc}")

        if all_chunks:
            upsert_chunks(all_chunks)

    return {
        "total_files_scanned": len(all_files),
        "files_indexed": len(all_files),
        "chunks_upserted": total_chunks,
        "changed": [],
        "new": all_files,
        "deleted": [],
        "skipped": 0,
        "errors": errors,
        "indexed_at": datetime.now(UTC).isoformat(),
    }


def get_index_status() -> dict[str, Any]:
    """Get current index status: total docs, indexed, stale, last_indexed_at."""
    from mcp_engineering_knowledge.qdrant_store import count_points

    root = Path(settings.docs_path)
    total_docs = sum(1 for _ in root.rglob("*.md"))

    payloads = get_all_payloads()
    indexed_hashes = build_hash_index(payloads)
    indexed_count = len(indexed_hashes)

    changes = detect_changed_docs(settings.docs_path, indexed_hashes)
    stale_count = len(changes["changed"]) + len(changes["new"])

    # Find last_indexed_at
    last_indexed = ""
    for p in payloads:
        payload = p.get("payload", {})
        ts = payload.get("last_indexed_at", "")
        if ts and ts > last_indexed:
            last_indexed = ts

    return {
        "total_docs": total_docs,
        "indexed_docs": indexed_count,
        "stale_docs": stale_count,
        "changed_docs": changes["changed"],
        "new_docs": changes["new"],
        "deleted_docs": changes["deleted"],
        "total_chunks": count_points(),
        "last_indexed_at": last_indexed,
        "collection": settings.collection_name,
    }


def invalidate(file_paths: list[str]) -> dict[str, Any]:
    """Invalidate (delete) specific files from the index."""
    deleted: list[str] = []
    for f in file_paths:
        try:
            delete_by_file_path(f)
            deleted.append(f)
        except McpError:
            pass
    return {"invalidated": deleted, "count": len(deleted)}
