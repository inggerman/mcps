"""Write tools — gated by ALLOW_WRITE. Update standards, add patterns, reindex."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp_engineering_knowledge.config import settings
from mcp_engineering_knowledge.indexing import get_index_status, index_full, index_incremental, invalidate
from mcp_shared.errors import McpError


def _check_write() -> None:
    """Raise if write is not allowed."""
    if not settings.allow_write:
        raise McpError(
            "Write not permitted. Set KB_ALLOW_WRITE=true to enable write operations."
        )


def update_standard(name: str, content: str) -> dict[str, Any]:
    """Update a governance standard's README.md content.

    Args:
        name: Standard name (e.g., 'refactoring', 'code-review').
        content: New markdown content for the README.md.
    """
    _check_write()
    root = Path(settings.docs_path) / "governance" / "standards" / name
    readme = root / "README.md"
    if not readme.parent.is_dir():
        raise McpError(f"Standard directory not found: {name}")
    readme.write_text(content, encoding="utf-8")
    return {
        "standard": name,
        "file": str(readme.relative_to(Path(settings.docs_path))).replace("\\", "/"),
        "updated_at": datetime.now(UTC).isoformat(),
        "bytes": len(content.encode("utf-8")),
    }


def add_pattern(name: str, content: str) -> dict[str, Any]:
    """Add a new architecture pattern file.

    Args:
        name: Pattern file name (without extension, e.g., '28-event-sourcing-v2').
        content: Markdown content for the pattern.
    """
    _check_write()
    root = Path(settings.docs_path) / "manuals" / "engineering-practices" / "13-architecture-patterns"
    if not root.is_dir():
        raise McpError("Architecture patterns directory not found")
    file_path = root / f"{name}.md"
    if file_path.exists():
        raise McpError(f"Pattern already exists: {name}. Use update_pattern instead.")
    file_path.write_text(content, encoding="utf-8")
    return {
        "pattern": name,
        "file": str(file_path.relative_to(Path(settings.docs_path))).replace("\\", "/"),
        "created_at": datetime.now(UTC).isoformat(),
        "bytes": len(content.encode("utf-8")),
    }


def reindex(full: bool = False) -> dict[str, Any]:
    """Reindex the knowledge base.

    Args:
        full: If True, force full re-index. If False, incremental only.
    """
    _check_write()
    if full:
        return index_full()
    return index_incremental()


def invalidate_files(paths: list[str]) -> dict[str, Any]:
    """Invalidate (delete from index) specific file paths.

    Args:
        paths: List of file paths to invalidate.
    """
    _check_write()
    return invalidate(paths)


def get_status() -> dict[str, Any]:
    """Get current index status (read-only, always available)."""
    return get_index_status()
