"""FastMCP server for mcp-engineering-knowledge.

Exposes engineering standards, patterns, manuals and architecture docs
as tools and resources with semantic search (Qdrant + LM Studio embeddings).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import MCPError as SdkMcpError

from mcp_engineering_knowledge import __version__
from mcp_engineering_knowledge.config import settings
from mcp_engineering_knowledge.tools.query_tools import (
    compare_approaches,
    get_anti_patterns,
    get_checklist,
    get_decision_tree,
    get_manual_section,
    get_pattern,
    get_sources,
    get_standard,
    list_manuals,
    list_patterns,
    list_standards,
    search_knowledge,
)
from mcp_engineering_knowledge.tools.write_tools import (
    add_pattern,
    get_status,
    invalidate_files,
    reindex,
    update_standard,
)
from mcp_engineering_knowledge import resources as res
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-engineering-knowledge",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-engineering-knowledge")
    logger.info(
        "mcp-engineering-knowledge iniciando",
        version=__version__,
        docs_path=settings.docs_path,
        allow_write=settings.allow_write,
    )
    yield
    logger.info("mcp-engineering-knowledge detenido")
    structlog.contextvars.clear_contextvars()


# ---------------------------------------------------------------------------
# FastMCP instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-engineering-knowledge",
    instructions=(
        "Engineering knowledge base MCP. Exposes standards, patterns, manuals "
        "and architecture docs with semantic search. "
        "Query tools: search_knowledge, get_standard, get_pattern, get_manual_section, "
        "list_standards, list_patterns, list_manuals, compare_approaches, "
        "get_checklist, get_decision_tree, get_sources, get_anti_patterns. "
        "Write tools (gated by KB_ALLOW_WRITE): update_standard, add_pattern, "
        "reindex, invalidate_files. "
        "Status: get_index_status (always available)."
    ),
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=getattr(fn, "__name__", "?"), error=str(exc))
        raise SdkMcpError(code=-32603, message="Error interno del servidor.") from exc


# ---------------------------------------------------------------------------
# Query tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="search_knowledge",
    description="Semantic search across the engineering knowledge base. Parameters: query (str), domain (str, optional: governance, manuals, architecture, security, testing), limit (int, default 5).",
)
def tool_search_knowledge(query: str, domain: str = "", limit: int = 5) -> list[dict[str, Any]]:
    logger.info("search_knowledge", query=query[:50], domain=domain, limit=limit)
    return _handle(search_knowledge, query, domain, limit)


@mcp.tool(
    name="get_standard",
    description="Get a governance standard by name. Parameters: name (str, e.g. 'refactoring', 'code-review', 'migrations', 'open-banking').",
)
def tool_get_standard(name: str) -> dict[str, Any]:
    logger.info("get_standard", name=name)
    return _handle(get_standard, name)


@mcp.tool(
    name="get_pattern",
    description="Get an architecture pattern by name. Parameters: name (str, e.g. 'hexagonal', 'cqrs', 'saga', 'event-sourcing').",
)
def tool_get_pattern(name: str) -> dict[str, Any]:
    logger.info("get_pattern", name=name)
    return _handle(get_pattern, name)


@mcp.tool(
    name="get_manual_section",
    description="Get a manual section and optional topic. Parameters: section (str, e.g. '01-architecture'), topic (str, optional, e.g. '01-principles').",
)
def tool_get_manual_section(section: str, topic: str = "") -> dict[str, Any]:
    logger.info("get_manual_section", section=section, topic=topic)
    return _handle(get_manual_section, section, topic)


@mcp.tool(
    name="list_standards",
    description="List all governance standards available in the knowledge base.",
)
def tool_list_standards() -> list[dict[str, Any]]:
    logger.info("list_standards")
    return _handle(list_standards)


@mcp.tool(
    name="list_patterns",
    description="List all architecture patterns available in the knowledge base.",
)
def tool_list_patterns() -> list[dict[str, Any]]:
    logger.info("list_patterns")
    return _handle(list_patterns)


@mcp.tool(
    name="list_manuals",
    description="List all manual sections available in the knowledge base.",
)
def tool_list_manuals() -> list[dict[str, Any]]:
    logger.info("list_manuals")
    return _handle(list_manuals)


@mcp.tool(
    name="compare_approaches",
    description="Compare two approaches by searching for both. Parameters: a (str), b (str).",
)
def tool_compare_approaches(a: str, b: str) -> dict[str, Any]:
    logger.info("compare_approaches", a=a, b=b)
    return _handle(compare_approaches, a, b)


@mcp.tool(
    name="get_checklist",
    description="Get a checklist for a topic. Parameters: topic (str).",
)
def tool_get_checklist(topic: str) -> dict[str, Any]:
    logger.info("get_checklist", topic=topic)
    return _handle(get_checklist, topic)


@mcp.tool(
    name="get_decision_tree",
    description="Get a decision tree for a topic. Parameters: topic (str).",
)
def tool_get_decision_tree(topic: str) -> dict[str, Any]:
    logger.info("get_decision_tree", topic=topic)
    return _handle(get_decision_tree, topic)


@mcp.tool(
    name="get_sources",
    description="Get canonical sources for a topic. Parameters: topic (str).",
)
def tool_get_sources(topic: str) -> dict[str, Any]:
    logger.info("get_sources", topic=topic)
    return _handle(get_sources, topic)


@mcp.tool(
    name="get_anti_patterns",
    description="Get anti-patterns for a topic. Parameters: topic (str).",
)
def tool_get_anti_patterns(topic: str) -> dict[str, Any]:
    logger.info("get_anti_patterns", topic=topic)
    return _handle(get_anti_patterns, topic)


# ---------------------------------------------------------------------------
# Write tools (gated by KB_ALLOW_WRITE)
# ---------------------------------------------------------------------------


@mcp.tool(
    name="update_standard",
    description="Update a governance standard's README.md. Requires KB_ALLOW_WRITE=true. Parameters: name (str), content (str).",
)
def tool_update_standard(name: str, content: str) -> dict[str, Any]:
    logger.info("update_standard", name=name)
    return _handle(update_standard, name, content)


@mcp.tool(
    name="add_pattern",
    description="Add a new architecture pattern file. Requires KB_ALLOW_WRITE=true. Parameters: name (str), content (str).",
)
def tool_add_pattern(name: str, content: str) -> dict[str, Any]:
    logger.info("add_pattern", name=name)
    return _handle(add_pattern, name, content)


@mcp.tool(
    name="reindex",
    description="Reindex the knowledge base. Requires KB_ALLOW_WRITE=true. Parameters: full (bool, default false for incremental).",
)
def tool_reindex(full: bool = False) -> dict[str, Any]:
    logger.info("reindex", full=full)
    return _handle(reindex, full)


@mcp.tool(
    name="invalidate_files",
    description="Invalidate (delete from index) specific file paths. Requires KB_ALLOW_WRITE=true. Parameters: paths (list of str).",
)
def tool_invalidate_files(paths: list[str]) -> dict[str, Any]:
    logger.info("invalidate_files", count=len(paths))
    return _handle(invalidate_files, paths)


@mcp.tool(
    name="get_index_status",
    description="Get current index status: total docs, indexed docs, stale docs, last_indexed_at. Always available (read-only).",
)
def tool_get_index_status() -> dict[str, Any]:
    logger.info("get_index_status")
    return _handle(get_status)


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


@mcp.resource("kb://configuration")
def res_config() -> str:
    return res.kb_configuration()


@mcp.resource("kb://trusted-sources")
def res_sources() -> str:
    return res.kb_trusted_sources()


@mcp.resource("kb://index-status")
def res_status() -> str:
    return res.kb_index_status()


@mcp.resource("kb://standards")
def res_standards() -> str:
    return res.kb_standards_list()


@mcp.resource("kb://manuals")
def res_manuals() -> str:
    return res.kb_manuals_list()


@mcp.resource("kb://patterns")
def res_patterns() -> str:
    return res.kb_patterns_list()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
