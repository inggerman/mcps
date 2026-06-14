"""S3-compatible object storage operations."""

from __future__ import annotations

from typing import Any

from mcp_shared.errors import ValidationError


def _require_name(value: str, field: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(field=field, message=f"{field} no puede estar vacío.")
    return cleaned


def list_buckets(client: Any) -> list[dict[str, Any]]:
    response = client.list_buckets()
    return [
        {"name": bucket["Name"], "created": bucket.get("CreationDate")}
        for bucket in response.get("Buckets", [])
    ]


def list_objects(
    client: Any,
    bucket: str,
    prefix: str = "",
    max_keys: int = 500,
) -> dict[str, Any]:
    response = client.list_objects_v2(
        Bucket=_require_name(bucket, "bucket"),
        Prefix=prefix,
        MaxKeys=max_keys,
    )
    return {
        "bucket": bucket,
        "prefix": prefix,
        "objects": [
            {
                "key": item["Key"],
                "size": item["Size"],
                "etag": item.get("ETag"),
                "last_modified": item.get("LastModified"),
            }
            for item in response.get("Contents", [])
        ],
        "truncated": response.get("IsTruncated", False),
    }


def get_object_metadata(client: Any, bucket: str, key: str) -> dict[str, Any]:
    response = client.head_object(
        Bucket=_require_name(bucket, "bucket"),
        Key=_require_name(key, "key"),
    )
    return {
        "content_length": response.get("ContentLength"),
        "content_type": response.get("ContentType"),
        "etag": response.get("ETag"),
        "last_modified": response.get("LastModified"),
        "metadata": response.get("Metadata", {}),
    }


def presign_download(
    client: Any,
    bucket: str,
    key: str,
    expires_seconds: int = 900,
) -> str:
    if not 60 <= expires_seconds <= 604_800:
        raise ValidationError(field="expires_seconds", message="Debe estar entre 60 y 604800.")
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": _require_name(bucket, "bucket"),
            "Key": _require_name(key, "key"),
        },
        ExpiresIn=expires_seconds,
    )


def upload_text(
    client: Any,
    bucket: str,
    key: str,
    content: str,
    allow_write: bool,
    content_type: str = "text/plain; charset=utf-8",
) -> dict[str, Any]:
    if not allow_write:
        raise ValidationError(field="write", message="OBJECT_STORAGE_ALLOW_WRITE está desactivado.")
    raw = content.encode("utf-8")
    response = client.put_object(
        Bucket=_require_name(bucket, "bucket"),
        Key=_require_name(key, "key"),
        Body=raw,
        ContentType=content_type,
    )
    return {"bucket": bucket, "key": key, "bytes_written": len(raw), "etag": response.get("ETag")}


def delete_object(client: Any, bucket: str, key: str, allow_write: bool) -> dict[str, str]:
    if not allow_write:
        raise ValidationError(field="write", message="OBJECT_STORAGE_ALLOW_WRITE está desactivado.")
    client.delete_object(
        Bucket=_require_name(bucket, "bucket"),
        Key=_require_name(key, "key"),
    )
    return {"bucket": bucket, "key": key, "status": "deleted"}
