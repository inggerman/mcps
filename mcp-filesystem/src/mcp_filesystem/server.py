"""FastMCP server for sandboxed filesystem access."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_filesystem.config import settings
from mcp_filesystem.tools import (
    append_text_file,
    copy_path,
    count_lines,
    create_directory,
    delete_path,
    directory_tree,
    get_directory_size,
    get_file_hash,
    get_file_info,
    head_lines,
    list_directory,
    move_path,
    read_text_file,
    search_files,
    tail_lines,
    write_text_file,
)
from mcp_filesystem import resources as res

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-filesystem",
)
logger = get_logger(__name__)
mcp = FastMCP(
    name="mcp-filesystem",
    instructions=(
        "Acceso al filesystem confinado a FILESYSTEM_ROOT. "
        "Escritura desactivada por defecto. "
        "Tools: list, read, search, write, head, tail, file_info, tree, "
        "directory_size, file_hash, count_lines, append, create_dir, delete, copy, move."
    ),
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Tools originales
# ---------------------------------------------------------------------------


@mcp.tool(name="filesystem_list")
def tool_list(path: str = ".", recursive: bool = False) -> list[dict[str, Any]]:
    return _handle(list_directory, settings.root, path, recursive, settings.max_results)


@mcp.tool(name="filesystem_read_text")
def tool_read(path: str) -> dict[str, Any]:
    return _handle(read_text_file, settings.root, path, settings.max_read_bytes)


@mcp.tool(name="filesystem_search")
def tool_search(pattern: str = "*", text_query: str | None = None) -> list[dict[str, Any]]:
    return _handle(
        search_files,
        settings.root,
        pattern,
        text_query,
        settings.max_results,
        settings.max_read_bytes,
    )


@mcp.tool(name="filesystem_write_text")
def tool_write(path: str, content: str, overwrite: bool = False) -> dict[str, Any]:
    return _handle(write_text_file, settings.root, path, content, settings.allow_write, overwrite)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(name="filesystem_head")
def tool_head(path: str, n: int = 20) -> dict[str, Any]:
    return _handle(head_lines, settings.root, path, n, settings.max_read_bytes)


@mcp.tool(name="filesystem_tail")
def tool_tail(path: str, n: int = 20) -> dict[str, Any]:
    return _handle(tail_lines, settings.root, path, n, settings.max_read_bytes)


@mcp.tool(name="filesystem_file_info")
def tool_file_info(path: str) -> dict[str, Any]:
    return _handle(get_file_info, settings.root, path)


@mcp.tool(name="filesystem_tree")
def tool_tree(path: str = ".", max_depth: int = 3) -> str:
    return _handle(directory_tree, settings.root, path, max_depth)


@mcp.tool(name="filesystem_directory_size")
def tool_directory_size(path: str = ".") -> dict[str, Any]:
    return _handle(get_directory_size, settings.root, path)


@mcp.tool(name="filesystem_file_hash")
def tool_file_hash(path: str, algorithm: str = "sha256") -> dict[str, Any]:
    return _handle(get_file_hash, settings.root, path, algorithm)


@mcp.tool(name="filesystem_count_lines")
def tool_count_lines(path: str) -> dict[str, Any]:
    return _handle(count_lines, settings.root, path)


@mcp.tool(name="filesystem_append_text")
def tool_append(path: str, content: str) -> dict[str, Any]:
    return _handle(append_text_file, settings.root, path, content, settings.allow_write)


@mcp.tool(name="filesystem_create_directory")
def tool_create_dir(path: str) -> dict[str, Any]:
    return _handle(create_directory, settings.root, path, settings.allow_write)


@mcp.tool(name="filesystem_delete")
def tool_delete(path: str, recursive: bool = False) -> dict[str, Any]:
    return _handle(delete_path, settings.root, path, settings.allow_write, recursive)


@mcp.tool(name="filesystem_copy")
def tool_copy(src: str, dst: str) -> dict[str, Any]:
    return _handle(copy_path, settings.root, src, dst, settings.allow_write)


@mcp.tool(name="filesystem_move")
def tool_move(src: str, dst: str) -> dict[str, Any]:
    return _handle(move_path, settings.root, src, dst, settings.allow_write)


# ---------------------------------------------------------------------------
# Resources estáticos
# ---------------------------------------------------------------------------


@mcp.resource("fs://supported-operations")
def res_supported_operations() -> str:
    return res.supported_operations()


@mcp.resource("fs://path-conventions")
def res_path_conventions() -> str:
    return res.path_conventions()


@mcp.resource("fs://security-tips")
def res_security_tips() -> str:
    return res.security_tips()


@mcp.resource("fs://common-file-types")
def res_common_file_types() -> str:
    return res.common_file_types()


@mcp.resource("fs://encoding-tips")
def res_encoding_tips() -> str:
    return res.encoding_tips()


@mcp.resource("fs://search-patterns")
def res_search_patterns() -> str:
    return res.search_patterns_guide()


@mcp.resource("fs://best-practices/naming")
def res_best_practices_naming() -> str:
    return res.best_practices_naming()


@mcp.resource("fs://examples/tree")
def res_example_tree() -> str:
    return res.example_tree()


@mcp.resource("fs://examples/listing")
def res_example_listing() -> str:
    return res.example_file_listing()


@mcp.resource("fs://permissions-guide")
def res_permissions_guide() -> str:
    return res.permissions_guide()


@mcp.resource("fs://disk-usage-tips")
def res_disk_usage_tips() -> str:
    return res.disk_usage_tips()


@mcp.resource("fs://symlink-tips")
def res_symlink_tips() -> str:
    return res.symlink_tips()


# ---------------------------------------------------------------------------
# Resources dinámicos
# ---------------------------------------------------------------------------


@mcp.resource("fs://file/{path}/info")
def res_file_info(path: str) -> str:
    return res.file_info(settings.root, path)


@mcp.resource("fs://file/{path}/head")
def res_file_head(path: str) -> str:
    return res.file_head(settings.root, path)


@mcp.resource("fs://file/{path}/tail")
def res_file_tail(path: str) -> str:
    return res.file_tail(settings.root, path)


@mcp.resource("fs://dir/{path}/tree")
def res_dir_tree(path: str) -> str:
    return res.directory_tree(settings.root, path)


@mcp.resource("fs://dir/{path}/size")
def res_dir_size(path: str) -> str:
    return res.directory_size(settings.root, path)


@mcp.resource("fs://file/{path}/hash")
def res_file_hash(path: str) -> str:
    return res.file_hash(settings.root, path)


@mcp.resource("fs://file/{path}/line-count")
def res_file_line_count(path: str) -> str:
    return res.file_line_count(settings.root, path)


@mcp.resource("fs://dir/{path}/listing")
def res_dir_listing(path: str) -> str:
    return res.directory_listing(settings.root, path)


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
