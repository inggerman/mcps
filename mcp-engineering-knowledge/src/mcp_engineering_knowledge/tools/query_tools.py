"""Query tools — search and retrieve engineering knowledge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp_engineering_knowledge.config import settings
from mcp_engineering_knowledge.embedding import embed_text
from mcp_engineering_knowledge.qdrant_store import search
from mcp_shared.errors import McpError, NotFoundError


def search_knowledge(query: str, domain: str = "", limit: int = 5) -> list[dict[str, Any]]:
    """Semantic search across the engineering knowledge base.

    Args:
        query: Natural language query.
        domain: Optional domain filter (governance, manuals, architecture, security, testing).
        limit: Max results (default 5).
    """
    query_vector = embed_text(query)
    results = search(
        query_vector=query_vector,
        limit=limit,
        domain_filter=domain or None,
    )
    return [
        {
            "score": r["score"],
            "title": r["payload"].get("title", ""),
            "section": r["payload"].get("section", ""),
            "file_path": r["payload"].get("file_path", ""),
            "domain": r["payload"].get("domain", ""),
            "type": r["payload"].get("type", ""),
            "text": r["payload"].get("text", "")[:500],
        }
        for r in results
    ]


def get_standard(name: str) -> dict[str, Any]:
    """Get a governance standard by name (e.g., 'refactoring', 'code-review', 'migrations')."""
    root = Path(settings.docs_path) / "governance" / "standards" / name
    if not root.is_dir():
        raise NotFoundError("standard", name)
    readme = root / "README.md"
    if not readme.is_file():
        raise NotFoundError("standard", f"{name}/README.md")
    content = readme.read_text(encoding="utf-8")
    files: list[str] = []
    for p in root.rglob("*.md"):
        if p.name != "README.md":
            files.append(str(p.relative_to(root)).replace("\\", "/"))
    return {
        "name": name,
        "path": str(root.relative_to(Path(settings.docs_path))).replace("\\", "/"),
        "content": content,
        "additional_files": files,
    }


def get_pattern(name: str) -> dict[str, Any]:
    """Get an architecture pattern by name (e.g., 'hexagonal', 'cqrs', 'saga')."""
    # Search in manuals/engineering-practices/13-architecture-patterns/
    root = Path(settings.docs_path) / "manuals" / "engineering-practices" / "13-architecture-patterns"
    if not root.is_dir():
        raise NotFoundError("patterns_dir", str(root))
    # Find file matching name
    for p in root.glob("*.md"):
        if name.lower() in p.stem.lower():
            content = p.read_text(encoding="utf-8")
            return {
                "name": p.stem,
                "file_path": str(p.relative_to(Path(settings.docs_path))).replace("\\", "/"),
                "content": content,
            }
    raise NotFoundError("pattern", name)


def get_manual_section(section: str, topic: str = "") -> dict[str, Any]:
    """Get a manual section (e.g., '01-architecture', '04-security') and optional topic.

    Args:
        section: Section directory name (e.g., '01-architecture', '13-architecture-patterns').
        topic: Optional specific topic file (e.g., '01-principles').
    """
    root = Path(settings.docs_path) / "manuals" / "engineering-practices" / section
    if not root.is_dir():
        raise NotFoundError("section", section)
    if topic:
        # Try exact match or prefix match
        for p in root.glob("*.md"):
            if topic.lower() in p.stem.lower():
                content = p.read_text(encoding="utf-8")
                return {
                    "section": section,
                    "topic": p.stem,
                    "file_path": str(p.relative_to(Path(settings.docs_path))).replace("\\", "/"),
                    "content": content,
                }
        raise NotFoundError("topic", f"{section}/{topic}")
    # Return README or all files
    readme = root / "README.md"
    if readme.is_file():
        content = readme.read_text(encoding="utf-8")
        files = [p.stem for p in root.glob("*.md") if p.name != "README.md"]
        return {
            "section": section,
            "content": content,
            "topics": files,
        }
    files: list[str] = []
    for p in root.glob("*.md"):
        files.append(p.stem)
    return {"section": section, "topics": files}


def list_standards() -> list[dict[str, Any]]:
    """List all governance standards."""
    root = Path(settings.docs_path) / "governance" / "standards"
    if not root.is_dir():
        return []
    result: list[dict[str, Any]] = []
    for p in root.iterdir():
        if p.is_dir() and not p.name.startswith("."):
            readme = p / "README.md"
            title = ""
            if readme.is_file():
                content = readme.read_text(encoding="utf-8")
                # Extract title from frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        for line in parts[1].splitlines():
                            if line.strip().startswith("title:"):
                                title = line.split(":", 1)[1].strip().strip('"').strip("'")
                                break
            result.append({"name": p.name, "title": title})
    return result


def list_patterns() -> list[dict[str, Any]]:
    """List all architecture patterns."""
    root = Path(settings.docs_path) / "manuals" / "engineering-practices" / "13-architecture-patterns"
    if not root.is_dir():
        return []
    result: list[dict[str, Any]] = []
    for p in sorted(root.glob("*.md")):
        if p.name == "README.md":
            continue
        result.append({"name": p.stem, "file": p.name})
    return result


def list_manuals() -> list[dict[str, Any]]:
    """List all manual sections."""
    root = Path(settings.docs_path) / "manuals" / "engineering-practices"
    if not root.is_dir():
        return []
    result: list[dict[str, Any]] = []
    for p in sorted(root.iterdir()):
        if p.is_dir() and not p.name.startswith("."):
            file_count = sum(1 for _ in p.rglob("*.md"))
            result.append({"section": p.name, "files": file_count})
    return result


def compare_approaches(a: str, b: str) -> dict[str, Any]:
    """Compare two approaches by searching for both in the knowledge base."""
    results_a = search_knowledge(a, limit=3)
    results_b = search_knowledge(b, limit=3)
    return {
        "approach_a": {"query": a, "results": results_a},
        "approach_b": {"query": b, "results": results_b},
        "note": "Compare the rules, anti-patterns and sources from both sets of results.",
    }


def get_checklist(topic: str) -> dict[str, Any]:
    """Get a checklist for a topic by searching the knowledge base."""
    results = search_knowledge(f"checklist {topic}", limit=3)
    return {"topic": topic, "results": results}


def get_decision_tree(topic: str) -> dict[str, Any]:
    """Get a decision tree for a topic by searching the knowledge base."""
    results = search_knowledge(f"decision tree {topic}", limit=3)
    return {"topic": topic, "results": results}


def get_sources(topic: str) -> dict[str, Any]:
    """Get canonical sources for a topic by searching the knowledge base."""
    results = search_knowledge(f"sources references {topic}", limit=5)
    return {"topic": topic, "sources": results}


def get_anti_patterns(topic: str) -> dict[str, Any]:
    """Get anti-patterns for a topic by searching the knowledge base."""
    results = search_knowledge(f"anti-patterns {topic}", limit=5)
    return {"topic": topic, "anti_patterns": results}
