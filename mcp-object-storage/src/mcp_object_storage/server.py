"""FastMCP server for S3-compatible storage."""

from __future__ import annotations

from typing import Any

import boto3
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_object_storage.config import settings
from mcp_object_storage.tools import (
    delete_object,
    get_object_metadata,
    list_buckets,
    list_objects,
    presign_download,
    upload_text,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-object-storage",
)
logger = get_logger(__name__)
session = boto3.Session(profile_name=settings.profile, region_name=settings.region)
client = session.client("s3", endpoint_url=settings.endpoint_url)
mcp = FastMCP(
    name="mcp-object-storage",
    instructions="S3/MinIO con escritura desactivada por defecto.",
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="storage_list_buckets")
def tool_list_buckets() -> list[dict[str, Any]]:
    return _handle(list_buckets, client)


@mcp.tool(name="storage_list_objects")
def tool_list_objects(bucket: str, prefix: str = "") -> dict[str, Any]:
    return _handle(list_objects, client, bucket, prefix, settings.max_keys)


@mcp.tool(name="storage_object_metadata")
def tool_metadata(bucket: str, key: str) -> dict[str, Any]:
    return _handle(get_object_metadata, client, bucket, key)


@mcp.tool(name="storage_presign_download")
def tool_presign(bucket: str, key: str, expires_seconds: int = 900) -> str:
    return _handle(presign_download, client, bucket, key, expires_seconds)


@mcp.tool(name="storage_upload_text")
def tool_upload(
    bucket: str, key: str, content: str, content_type: str = "text/plain"
) -> dict[str, Any]:
    return _handle(upload_text, client, bucket, key, content, settings.allow_write, content_type)


@mcp.tool(name="storage_delete_object")
def tool_delete(bucket: str, key: str) -> dict[str, str]:
    return _handle(delete_object, client, bucket, key, settings.allow_write)


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
