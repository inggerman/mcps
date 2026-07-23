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


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def presign_upload(
    client: Any,
    bucket: str,
    key: str,
    expires_seconds: int = 900,
) -> str:
    """Genera una URL pre-firmada para subir un objeto."""
    if not 60 <= expires_seconds <= 604_800:
        raise ValidationError(field="expires_seconds", message="Debe estar entre 60 y 604800.")
    return client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": _require_name(bucket, "bucket"),
            "Key": _require_name(key, "key"),
        },
        ExpiresIn=expires_seconds,
    )


def copy_object(
    client: Any,
    source_bucket: str,
    source_key: str,
    dest_bucket: str,
    dest_key: str,
    allow_write: bool,
) -> dict[str, Any]:
    """Copia un objeto entre buckets."""
    if not allow_write:
        raise ValidationError(field="write", message="OBJECT_STORAGE_ALLOW_WRITE esta desactivado.")
    response = client.copy_object(
        Bucket=_require_name(dest_bucket, "dest_bucket"),
        Key=_require_name(dest_key, "dest_key"),
        CopySource={"Bucket": _require_name(source_bucket, "source_bucket"), "Key": _require_name(source_key, "source_key")},
    )
    return {
        "source": f"{source_bucket}/{source_key}",
        "destination": f"{dest_bucket}/{dest_key}",
        "etag": response.get("CopyObjectResult", {}).get("ETag"),
    }


def get_bucket_size(
    client: Any,
    bucket: str,
    prefix: str = "",
) -> dict[str, Any]:
    """Calcula el tamano total de un bucket o prefijo."""
    total_size = 0
    object_count = 0
    continuation_token = None

    while True:
        kwargs: dict[str, Any] = {
            "Bucket": _require_name(bucket, "bucket"),
            "Prefix": prefix,
            "MaxKeys": 1000,
        }
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        response = client.list_objects_v2(**kwargs)

        for item in response.get("Contents", []):
            total_size += item.get("Size", 0)
            object_count += 1

        if not response.get("IsTruncated", False):
            break
        continuation_token = response.get("NextContinuationToken")

    return {
        "bucket": bucket,
        "prefix": prefix,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "object_count": object_count,
    }


def list_object_versions(
    client: Any,
    bucket: str,
    prefix: str = "",
) -> dict[str, Any]:
    """Lista versiones de objetos en un bucket con versioning."""
    response = client.list_object_versions(
        Bucket=_require_name(bucket, "bucket"),
        Prefix=prefix,
    )

    versions = [
        {
            "key": v.get("Key"),
            "version_id": v.get("VersionId"),
            "is_latest": v.get("IsLatest"),
            "size": v.get("Size"),
            "last_modified": v.get("LastModified"),
        }
        for v in response.get("Versions", [])
    ]

    return {
        "bucket": bucket,
        "prefix": prefix,
        "versions_count": len(versions),
        "versions": versions[:100],
    }


def get_bucket_policy(
    client: Any,
    bucket: str,
) -> dict[str, Any]:
    """Obtiene la politica de un bucket."""
    try:
        response = client.get_bucket_policy(Bucket=_require_name(bucket, "bucket"))
        import json
        policy = json.loads(response.get("Policy", "{}"))
        return {"bucket": bucket, "policy": policy}
    except Exception as exc:
        if "NoSuchBucketPolicy" in str(exc):
            return {"bucket": bucket, "policy": None, "message": "No policy set on bucket."}
        raise


def get_bucket_lifecycle(
    client: Any,
    bucket: str,
) -> dict[str, Any]:
    """Obtiene la configuracion de lifecycle de un bucket."""
    try:
        response = client.get_bucket_lifecycle_configuration(Bucket=_require_name(bucket, "bucket"))
        rules = [
            {
                "id": r.get("ID"),
                "status": r.get("Status"),
                "prefix": r.get("Filter", {}).get("Prefix", ""),
                "transitions": r.get("Transitions", []),
                "expiration": r.get("Expiration"),
            }
            for r in response.get("Rules", [])
        ]
        return {"bucket": bucket, "rules": rules}
    except Exception as exc:
        if "NoSuchLifecycleConfiguration" in str(exc):
            return {"bucket": bucket, "rules": [], "message": "No lifecycle configuration set."}
        raise


def check_bucket_exists(
    client: Any,
    bucket: str,
) -> dict[str, Any]:
    """Verifica si un bucket existe y es accesible."""
    try:
        client.head_bucket(Bucket=_require_name(bucket, "bucket"))
        return {"bucket": bucket, "exists": True, "accessible": True}
    except Exception as exc:
        error_str = str(exc)
        if "404" in error_str or "NoSuchBucket" in error_str:
            return {"bucket": bucket, "exists": False, "accessible": False}
        return {"bucket": bucket, "exists": True, "accessible": False, "error": error_str[:200]}


def get_storage_metrics(
    client: Any,
) -> dict[str, Any]:
    """Retorna metricas de almacenamiento de todos los buckets."""
    buckets_response = client.list_buckets()
    buckets = buckets_response.get("Buckets", [])

    metrics: list[dict[str, Any]] = []
    total_objects = 0
    total_size = 0

    for b in buckets:
        bucket_name = b["Name"]
        try:
            size_info = get_bucket_size(client, bucket_name)
            metrics.append({
                "bucket": bucket_name,
                "object_count": size_info["object_count"],
                "size_bytes": size_info["total_size_bytes"],
                "size_mb": size_info["total_size_mb"],
            })
            total_objects += size_info["object_count"]
            total_size += size_info["total_size_bytes"]
        except Exception:
            metrics.append({
                "bucket": bucket_name,
                "object_count": 0,
                "size_bytes": 0,
                "size_mb": 0,
                "error": "Could not access bucket",
            })

    return {
        "total_buckets": len(buckets),
        "total_objects": total_objects,
        "total_size_bytes": total_size,
        "total_size_gb": round(total_size / (1024 * 1024 * 1024), 4),
        "buckets": metrics[:50],
    }


def generate_storage_report(
    client: Any,
) -> dict[str, Any]:
    """Genera un reporte completo de almacenamiento."""
    metrics = get_storage_metrics(client)

    large_buckets = [b for b in metrics["buckets"] if b.get("size_mb", 0) > 100]
    empty_buckets = [b for b in metrics["buckets"] if b.get("object_count", 0) == 0]

    return {
        "summary": {
            "total_buckets": metrics["total_buckets"],
            "total_objects": metrics["total_objects"],
            "total_size_gb": metrics["total_size_gb"],
        },
        "large_buckets": large_buckets,
        "empty_buckets": empty_buckets,
        "recommendations": [
            f"Consider lifecycle rules for {len(large_buckets)} large buckets" if large_buckets else "No large buckets detected",
            f"Consider removing {len(empty_buckets)} empty buckets" if empty_buckets else "No empty buckets detected",
            "Enable versioning for critical buckets",
            "Set up replication for disaster recovery",
        ],
        "buckets": metrics["buckets"],
    }
