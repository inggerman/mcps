"""Tests for the freshness tracker."""

from datetime import UTC, datetime, timedelta

from mcp_engineering_knowledge.freshness import (
    build_hash_index,
    detect_changed_docs,
    is_stale,
)


def test_is_stale_old_timestamp():
    """A timestamp older than threshold is stale."""
    old_ts = (datetime.now(UTC) - timedelta(days=100)).isoformat()
    assert is_stale(old_ts, "standard") is True


def test_is_stale_recent_timestamp():
    """A recent timestamp is not stale."""
    recent_ts = datetime.now(UTC).isoformat()
    assert is_stale(recent_ts, "standard") is False


def test_is_stale_no_timestamp():
    """No timestamp is always stale."""
    assert is_stale(None, "standard") is True
    assert is_stale("", "standard") is True


def test_is_stale_by_type():
    """Staleness threshold varies by document type."""
    ts = (datetime.now(UTC) - timedelta(days=100)).isoformat()
    # Standards: 90 days → stale
    assert is_stale(ts, "standard") is True
    # Patterns: 180 days → not stale
    assert is_stale(ts, "pattern") is False


def test_build_hash_index():
    """build_hash_index extracts file_path → hash mapping from payloads."""
    payloads = [
        {"id": 1, "payload": {"file_path": "a.md", "file_hash": "abc"}},
        {"id": 2, "payload": {"file_path": "b.md", "file_hash": "def"}},
        {"id": 3, "payload": {"file_path": "a.md", "file_hash": "abc"}},  # duplicate
    ]
    result = build_hash_index(payloads)
    assert result == {"a.md": "abc", "b.md": "def"}


def test_detect_changed_docs(tmp_path):
    """detect_changed_docs identifies new, changed and deleted files."""
    # Create test files
    (tmp_path / "existing.md").write_text("existing")
    (tmp_path / "changed.md").write_text("new content")

    indexed_hashes = {
        "existing.md": __import__("hashlib").sha256(b"existing").hexdigest(),
        "changed.md": __import__("hashlib").sha256(b"old content").hexdigest(),
        "deleted.md": "somehash",
    }

    result = detect_changed_docs(str(tmp_path), indexed_hashes)
    assert "changed.md" in result["changed"]
    assert "deleted.md" in result["deleted"]
    # existing.md should not be in changed (same content)
    assert "existing.md" not in result["changed"]
