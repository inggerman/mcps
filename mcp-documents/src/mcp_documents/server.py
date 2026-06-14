from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_documents.config import settings
from mcp_documents.tools import extract_document, get_document_metadata

setup_logging(
    log_level=settings.log_level, log_format=settings.log_format, server_name="mcp-documents"
)
logger = get_logger(__name__)
mcp = FastMCP(name="mcp-documents", instructions="Extracción segura de PDF, DOCX y PPTX.")


def _handle(fn: Any, *args: Any) -> Any:
    try:
        return fn(*args)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="documents_extract")
def tool_extract(path: str) -> dict[str, Any]:
    return _handle(
        extract_document,
        settings.root,
        path,
        settings.max_file_size_mb,
        settings.max_pages,
    )


@mcp.tool(name="documents_metadata")
def tool_metadata(path: str) -> dict[str, Any]:
    return _handle(get_document_metadata, settings.root, path, settings.max_file_size_mb)


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
