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
    check_bucket_exists,
    copy_object,
    delete_object,
    generate_storage_report,
    get_bucket_lifecycle,
    get_bucket_policy,
    get_bucket_size,
    get_object_metadata,
    get_storage_metrics,
    list_buckets,
    list_object_versions,
    list_objects,
    presign_download,
    presign_upload,
    upload_text,
)
from mcp_object_storage import resources as res

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


@mcp.tool(name="storage_presign_upload")
def tool_presign_upload(bucket: str, key: str, expires_seconds: int = 900) -> str:
    return _handle(presign_upload, client, bucket, key, expires_seconds)


@mcp.tool(name="storage_copy_object")
def tool_copy_object(source_bucket: str, source_key: str, dest_bucket: str, dest_key: str) -> dict[str, Any]:
    return _handle(copy_object, client, source_bucket, source_key, dest_bucket, dest_key, settings.allow_write)


@mcp.tool(name="storage_get_bucket_size")
def tool_bucket_size(bucket: str, prefix: str = "") -> dict[str, Any]:
    return _handle(get_bucket_size, client, bucket, prefix)


@mcp.tool(name="storage_list_object_versions")
def tool_list_versions(bucket: str, prefix: str = "") -> dict[str, Any]:
    return _handle(list_object_versions, client, bucket, prefix)


@mcp.tool(name="storage_get_bucket_policy")
def tool_bucket_policy(bucket: str) -> dict[str, Any]:
    return _handle(get_bucket_policy, client, bucket)


@mcp.tool(name="storage_get_bucket_lifecycle")
def tool_bucket_lifecycle(bucket: str) -> dict[str, Any]:
    return _handle(get_bucket_lifecycle, client, bucket)


@mcp.tool(name="storage_check_bucket_exists")
def tool_check_bucket(bucket: str) -> dict[str, Any]:
    return _handle(check_bucket_exists, client, bucket)


@mcp.tool(name="storage_get_metrics")
def tool_metrics() -> dict[str, Any]:
    return _handle(get_storage_metrics, client)


@mcp.tool(name="storage_generate_report")
def tool_report() -> dict[str, Any]:
    return _handle(generate_storage_report, client)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("storage://configuration")
def res_config() -> str:
    return res.storage_configuration()


@mcp.resource("storage://s3-basics")
def res_basics() -> str:
    return res.storage_s3_basics()


@mcp.resource("storage://best-practices")
def res_best() -> str:
    return res.storage_best_practices()


@mcp.resource("storage://quick-reference")
def res_quick() -> str:
    return res.storage_quick_reference()


@mcp.resource("storage://error-codes")
def res_errors() -> str:
    return res.storage_error_codes()


@mcp.resource("storage://troubleshooting")
def res_trouble() -> str:
    return res.storage_troubleshooting()


@mcp.resource("storage://examples")
def res_examples() -> str:
    return res.storage_examples()


@mcp.resource("storage://lifecycle")
def res_lifecycle() -> str:
    return res.storage_lifecycle()


@mcp.resource("storage://security")
def res_security() -> str:
    return res.storage_security()


@mcp.resource("storage://multipart")
def res_multipart() -> str:
    return res.storage_multipart()


@mcp.resource("storage://replication")
def res_replication() -> str:
    return res.storage_replication()


@mcp.resource("storage://cost-optimization")
def res_cost() -> str:
    return res.storage_cost_optimization()


@mcp.resource("storage://presigned-urls")
def res_presigned() -> str:
    return res.storage_presigned_urls()


@mcp.resource("storage://versioning")
def res_versioning() -> str:
    return res.storage_versioning()


@mcp.resource("storage://migration")
def res_migration() -> str:
    return res.storage_migration()


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
