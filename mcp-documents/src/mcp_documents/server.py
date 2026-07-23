from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_documents.config import settings
from mcp_documents.tools import (
    batch_extract,
    compare_documents,
    convert_to_markdown,
    count_pages,
    export_document_text,
    extract_document,
    extract_images_info,
    extract_tables,
    extract_text_only,
    get_document_metadata,
    get_document_stats,
    get_document_summary,
    list_documents,
    search_in_document,
    validate_document,
)
from mcp_documents import resources as res

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


@mcp.tool(name="documents_list")
def tool_list(directory: str = "") -> list[dict[str, Any]]:
    return _handle(list_documents, settings.root, directory)


@mcp.tool(name="documents_search")
def tool_search(path: str, query: str) -> dict[str, Any]:
    return _handle(search_in_document, settings.root, path, query, settings.max_file_size_mb)


@mcp.tool(name="documents_count_pages")
def tool_count(path: str) -> dict[str, Any]:
    return _handle(count_pages, settings.root, path, settings.max_file_size_mb)


@mcp.tool(name="documents_extract_text")
def tool_extract_text(path: str) -> str:
    return _handle(extract_text_only, settings.root, path, settings.max_file_size_mb, settings.max_pages)


@mcp.tool(name="documents_summary")
def tool_summary(path: str) -> dict[str, Any]:
    return _handle(get_document_summary, settings.root, path, settings.max_file_size_mb, settings.max_pages)


@mcp.tool(name="documents_to_markdown")
def tool_markdown(path: str) -> str:
    return _handle(convert_to_markdown, settings.root, path, settings.max_file_size_mb, settings.max_pages)


@mcp.tool(name="documents_batch_extract")
def tool_batch(directory: str) -> dict[str, Any]:
    return _handle(batch_extract, settings.root, directory, settings.max_file_size_mb, settings.max_pages)


@mcp.tool(name="documents_stats")
def tool_stats(directory: str = "") -> dict[str, Any]:
    return _handle(get_document_stats, settings.root, directory)


@mcp.tool(name="documents_validate")
def tool_validate(path: str) -> dict[str, Any]:
    return _handle(validate_document, settings.root, path, settings.max_file_size_mb)


@mcp.tool(name="documents_extract_tables")
def tool_tables(path: str) -> dict[str, Any]:
    return _handle(extract_tables, settings.root, path, settings.max_file_size_mb)


@mcp.tool(name="documents_images_info")
def tool_images(path: str) -> dict[str, Any]:
    return _handle(extract_images_info, settings.root, path, settings.max_file_size_mb)


@mcp.tool(name="documents_compare")
def tool_compare(path_a: str, path_b: str) -> dict[str, Any]:
    return _handle(compare_documents, settings.root, path_a, path_b, settings.max_file_size_mb, settings.max_pages)


@mcp.tool(name="documents_export_text")
def tool_export(path: str) -> dict[str, Any]:
    return _handle(export_document_text, settings.root, path, settings.max_file_size_mb, settings.max_pages)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("documents://configuration")
def res_config() -> str:
    return res.documents_configuration()


@mcp.resource("documents://supported-formats")
def res_formats() -> str:
    return res.documents_supported_formats()


@mcp.resource("documents://best-practices")
def res_best() -> str:
    return res.documents_best_practices()


@mcp.resource("documents://quick-reference")
def res_quick() -> str:
    return res.documents_quick_reference()


@mcp.resource("documents://error-codes")
def res_errors() -> str:
    return res.documents_error_codes()


@mcp.resource("documents://troubleshooting")
def res_trouble() -> str:
    return res.documents_troubleshooting()


@mcp.resource("documents://examples")
def res_examples() -> str:
    return res.documents_examples()


@mcp.resource("documents://pdf-guide")
def res_pdf() -> str:
    return res.documents_pdf_guide()


@mcp.resource("documents://docx-guide")
def res_docx() -> str:
    return res.documents_docx_guide()


@mcp.resource("documents://pptx-guide")
def res_pptx() -> str:
    return res.documents_pptx_guide()


@mcp.resource("documents://ocr-guide")
def res_ocr() -> str:
    return res.documents_ocr_guide()


@mcp.resource("documents://security")
def res_security() -> str:
    return res.documents_security()


@mcp.resource("documents://batch-processing")
def res_batch() -> str:
    return res.documents_batch_processing()


@mcp.resource("documents://text-analysis")
def res_analysis() -> str:
    return res.documents_text_analysis()


@mcp.resource("documents://conversion")
def res_conversion() -> str:
    return res.documents_conversion()


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
