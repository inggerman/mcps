"""Static resources for mcp-engineering-knowledge."""

from __future__ import annotations

from pathlib import Path

from mcp_engineering_knowledge.config import settings
from mcp_engineering_knowledge.whitelist import list_by_category, list_whitelist


def _read_file(rel_path: str) -> str:
    """Read a file from docs/ as text."""
    p = Path(settings.docs_path) / rel_path
    if not p.is_file():
        return f"File not found: {rel_path}"
    return p.read_text(encoding="utf-8")


def kb_configuration() -> str:
    """Return the MCP configuration as a readable string."""
    from mcp_engineering_knowledge.config import settings as s
    return (
        f"# mcp-engineering-knowledge Configuration\n\n"
        f"- docs_path: {s.docs_path}\n"
        f"- qdrant_url: {s.qdrant_url}\n"
        f"- embedding_model: {s.embedding_model}\n"
        f"- embedding_dim: {s.embedding_dim}\n"
        f"- allow_write: {s.allow_write}\n"
        f"- trust_threshold: {s.trust_threshold}\n"
        f"- chunk_size: {s.chunk_size}\n"
        f"- chunk_overlap: {s.chunk_overlap}\n"
        f"- collection_name: {s.collection_name}\n"
        f"- freshness_standards_days: {s.freshness_standards_days}\n"
        f"- freshness_patterns_days: {s.freshness_patterns_days}\n"
        f"- freshness_manuals_days: {s.freshness_manuals_days}\n"
    )


def kb_trusted_sources() -> str:
    """Return the trusted sources whitelist."""
    categories = list_by_category()
    lines = ["# Trusted Sources Whitelist\n"]
    for cat, domains in categories.items():
        lines.append(f"\n## {cat.replace('_', ' ').title()}\n")
        for d in domains:
            lines.append(f"- {d['domain']} (trust: {d['trust']})")
    return "\n".join(lines)


def kb_index_status() -> str:
    """Return current index status as readable text."""
    from mcp_engineering_knowledge.indexing import get_index_status
    status = get_index_status()
    lines = ["# Index Status\n"]
    for k, v in status.items():
        if isinstance(v, list):
            lines.append(f"\n{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def kb_standards_list() -> str:
    """Return a list of all governance standards."""
    from mcp_engineering_knowledge.tools.query_tools import list_standards
    standards = list_standards()
    lines = ["# Governance Standards\n"]
    for s in standards:
        lines.append(f"- **{s['name']}**: {s.get('title', '')}")
    return "\n".join(lines)


def kb_manuals_list() -> str:
    """Return a list of all manual sections."""
    from mcp_engineering_knowledge.tools.query_tools import list_manuals
    manuals = list_manuals()
    lines = ["# Manual Sections\n"]
    for m in manuals:
        lines.append(f"- **{m['section']}** ({m['files']} files)")
    return "\n".join(lines)


def kb_patterns_list() -> str:
    """Return a list of all architecture patterns."""
    from mcp_engineering_knowledge.tools.query_tools import list_patterns
    patterns = list_patterns()
    lines = ["# Architecture Patterns\n"]
    for p in patterns:
        lines.append(f"- **{p['name']}** ({p['file']})")
    return "\n".join(lines)
