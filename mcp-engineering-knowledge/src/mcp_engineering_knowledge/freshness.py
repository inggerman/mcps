"""Freshness tracker — hash-based staleness detection for indexed docs."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from mcp_engineering_knowledge.config import settings


def compute_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    p = Path(file_path)
    if not p.is_file():
        return ""
    return hashlib.sha256(p.read_bytes()).hexdigest()


def get_staleness_threshold_days(doc_type: str) -> int:
    """Get staleness threshold in days by document type."""
    type_lower = (doc_type or "").lower()
    if "standard" in type_lower:
        return settings.freshness_standards_days
    if "pattern" in type_lower:
        return settings.freshness_patterns_days
    if "manual" in type_lower or "guide" in type_lower or "reference" in type_lower:
        return settings.freshness_manuals_days
    return settings.freshness_manuals_days


def is_stale(last_verified_at: str | None, doc_type: str = "") -> bool:
    """Check if a document is stale based on its last_verified_at timestamp."""
    if not last_verified_at:
        return True
    try:
        # Parse ISO 8601 timestamp
        ts = datetime.fromisoformat(last_verified_at.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        age_days = (datetime.now(UTC) - ts).days
        return age_days > get_staleness_threshold_days(doc_type)
    except (ValueError, TypeError):
        return True


def detect_changed_docs(
    docs_path: str,
    indexed_hashes: dict[str, str],
) -> dict[str, list[str]]:
    """Compare filesystem hashes with indexed hashes.

    Returns: {"changed": [...], "new": [...], "deleted": [...]}
    """
    root = Path(docs_path)
    current_files: dict[str, str] = {}

    for p in root.rglob("*.md"):
        rel = str(p.relative_to(root)).replace("\\", "/")
        current_files[rel] = compute_hash(str(p))

    indexed_set = set(indexed_hashes.keys())
    current_set = set(current_files.keys())

    new_files = sorted(current_set - indexed_set)
    deleted_files = sorted(indexed_set - current_set)
    changed_files = sorted(
        rel for rel in (current_set & indexed_set)
        if current_files[rel] != indexed_hashes.get(rel)
    )

    return {
        "changed": changed_files,
        "new": new_files,
        "deleted": deleted_files,
    }


def build_hash_index(payloads: list[dict]) -> dict[str, str]:
    """Build a {file_path: hash} map from Qdrant payloads."""
    result: dict[str, str] = {}
    for p in payloads:
        payload = p.get("payload", {})
        file_path = payload.get("file_path", "")
        file_hash = payload.get("file_hash", "")
        if file_path and file_hash:
            # Keep first occurrence (deduplicate by file_path)
            if file_path not in result:
                result[file_path] = file_hash
    return result
