from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
import yaml
from mcp_shared.errors import ValidationError

_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def load_spec(source: str, allowed_root: Path, timeout_seconds: float = 30) -> dict[str, Any]:
    if source.startswith(("http://", "https://")):
        response = httpx.get(source, timeout=timeout_seconds, follow_redirects=False)
        response.raise_for_status()
        raw = response.text
    else:
        root = allowed_root.resolve()
        path = (
            (root / source).resolve() if not Path(source).is_absolute() else Path(source).resolve()
        )
        if not path.is_relative_to(root):
            raise ValidationError(
                field="spec", message="El spec está fuera de OPENAPI_ALLOWED_ROOT."
            )
        raw = path.read_text(encoding="utf-8")
    parsed = json.loads(raw) if raw.lstrip().startswith(("{", "[")) else yaml.safe_load(raw)
    if not isinstance(parsed, dict) or "paths" not in parsed:
        raise ValidationError(field="spec", message="El documento no contiene un OpenAPI válido.")
    return parsed


def list_operations(spec: dict[str, Any]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in _METHODS or not isinstance(operation, dict):
                continue
            operations.append(
                {
                    "operation_id": operation.get("operationId"),
                    "method": method.upper(),
                    "path": path,
                    "summary": operation.get("summary", ""),
                    "tags": operation.get("tags", []),
                }
            )
    return operations


def describe_operation(spec: dict[str, Any], operation_id: str) -> dict[str, Any]:
    for operation in list_operations(spec):
        if operation["operation_id"] == operation_id:
            detail = spec["paths"][operation["path"]][operation["method"].lower()]
            return {
                **operation,
                "parameters": detail.get("parameters", []),
                "request_body": detail.get("requestBody"),
            }
    raise ValidationError(field="operation_id", message=f"No existe la operación '{operation_id}'.")


def invoke_operation(
    spec: dict[str, Any],
    operation_id: str,
    allow_invoke: bool,
    allowed_hosts: list[str],
    path_parameters: dict[str, Any] | None = None,
    query_parameters: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json_body: Any = None,
    timeout_seconds: float = 30,
) -> dict[str, Any]:
    if not allow_invoke:
        raise ValidationError(field="invoke", message="OPENAPI_ALLOW_INVOKE está desactivado.")
    operation = describe_operation(spec, operation_id)
    servers = spec.get("servers", [])
    if not servers:
        raise ValidationError(field="servers", message="El spec no define un servidor base.")
    base_url = servers[0].get("url", "")
    host = urlparse(base_url).hostname or ""
    if not allowed_hosts or host not in allowed_hosts:
        raise ValidationError(field="host", message=f"El host '{host}' no está permitido.")
    path = operation["path"]
    for name, value in (path_parameters or {}).items():
        path = path.replace("{" + name + "}", str(value))
    response = httpx.request(
        operation["method"],
        urljoin(base_url.rstrip("/") + "/", path.lstrip("/")),
        params=query_parameters,
        headers=headers,
        json=json_body,
        timeout=timeout_seconds,
        follow_redirects=False,
    )
    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": response.text,
    }
