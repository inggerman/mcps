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


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def get_spec_info(spec: dict[str, Any]) -> dict[str, Any]:
    """Retorna informacion general del spec OpenAPI."""
    return {
        "openapi_version": spec.get("openapi", spec.get("swagger", "unknown")),
        "title": spec.get("info", {}).get("title", "unknown"),
        "version": spec.get("info", {}).get("version", "unknown"),
        "description": spec.get("info", {}).get("description", ""),
        "servers": spec.get("servers", []),
        "paths_count": len(spec.get("paths", {})),
        "tags": [t.get("name", "") for t in spec.get("tags", [])],
    }


def list_endpoints(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Lista todos los endpoints con su metodo y path."""
    endpoints: list[dict[str, Any]] = []
    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method in _METHODS:
            if method in path_item:
                op = path_item[method]
                endpoints.append({
                    "method": method.upper(),
                    "path": path,
                    "operation_id": op.get("operationId", ""),
                    "deprecated": op.get("deprecated", False),
                })
    return endpoints


def get_schemas(spec: dict[str, Any]) -> dict[str, Any]:
    """Retorna los schemas definidos en el spec."""
    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    return {
        "schemas_count": len(schemas),
        "schemas": list(schemas.keys()),
    }


def describe_schema(spec: dict[str, Any], schema_name: str) -> dict[str, Any]:
    """Describe un schema especifico del spec."""
    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    if schema_name not in schemas:
        raise ValidationError(field="schema_name", message=f"Schema '{schema_name}' not found.")
    schema = schemas[schema_name]
    return {
        "name": schema_name,
        "type": schema.get("type", "object"),
        "properties": list(schema.get("properties", {}).keys()),
        "required": schema.get("required", []),
        "description": schema.get("description", ""),
    }


def get_security_schemes(spec: dict[str, Any]) -> dict[str, Any]:
    """Retorna los esquemas de seguridad del spec."""
    components = spec.get("components", {})
    security = components.get("securitySchemes", {})
    return {
        "schemes_count": len(security),
        "schemes": {
            name: {"type": s.get("type", ""), "description": s.get("description", "")}
            for name, s in security.items()
        },
    }


def validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Valida un spec OpenAPI basicamente."""
    issues: list[dict[str, str]] = []

    if "openapi" not in spec and "swagger" not in spec:
        issues.append({"severity": "error", "message": "Missing openapi/swagger version field."})

    if "info" not in spec:
        issues.append({"severity": "error", "message": "Missing info section."})
    else:
        if "title" not in spec["info"]:
            issues.append({"severity": "error", "message": "Missing info.title."})
        if "version" not in spec["info"]:
            issues.append({"severity": "error", "message": "Missing info.version."})

    if "paths" not in spec or not spec["paths"]:
        issues.append({"severity": "error", "message": "No paths defined."})

    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            issues.append({"severity": "warning", "message": f"Path '{path}' has no valid item."})
            continue
        for method, op in path_item.items():
            if method.lower() in _METHODS and isinstance(op, dict):
                if "operationId" not in op:
                    issues.append({"severity": "warning", "message": f"{method.upper()} {path}: missing operationId."})
                if "responses" not in op:
                    issues.append({"severity": "error", "message": f"{method.upper()} {path}: missing responses."})

    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "total_issues": len(issues),
    }


def generate_client_code(spec: dict[str, Any], language: str = "python") -> str:
    """Genera codigo basico de cliente a partir del spec."""
    ops = list_operations(spec)
    servers = spec.get("servers", [])
    base_url = servers[0].get("url", "") if servers else ""

    if language.lower() == "python":
        lines = [
            "import httpx",
            "",
            f"BASE_URL = '{base_url}'",
            "client = httpx.Client(base_url=BASE_URL)",
            "",
        ]
        for op in ops:
            method = op["method"].lower()
            func_name = op["operation_id"] or f"{method}_{op['path'].replace('/', '_').strip('_')}"
            lines.append(f"def {func_name}(**kwargs):")
            lines.append(f"    return client.{method}('{op['path']}', **kwargs)")
            lines.append("")
        return "\n".join(lines)
    elif language.lower() == "curl":
        lines = []
        for op in ops:
            lines.append(f"# {op['operation_id']}")
            lines.append(f"curl -X {op['method']} '{base_url}{op['path']}'")
            lines.append("")
        return "\n".join(lines)
    else:
        return f"# Language '{language}' not supported. Try: python, curl"


def export_spec_summary(spec: dict[str, Any]) -> dict[str, Any]:
    """Exporta un resumen completo del spec."""
    info = get_spec_info(spec)
    ops = list_operations(spec)
    schemas = get_schemas(spec)
    security = get_security_schemes(spec)
    validation = validate_spec(spec)

    methods_count: dict[str, int] = {}
    for op in ops:
        methods_count[op["method"]] = methods_count.get(op["method"], 0) + 1

    return {
        "info": info,
        "operations_count": len(ops),
        "methods_distribution": methods_count,
        "schemas": schemas,
        "security": security,
        "validation": validation,
    }


def get_tags(spec: dict[str, Any]) -> list[dict[str, str]]:
    """Retorna los tags definidos en el spec."""
    tags = spec.get("tags", [])
    return [{"name": t.get("name", ""), "description": t.get("description", "")} for t in tags]


def list_operations_by_tag(spec: dict[str, Any], tag: str) -> list[dict[str, Any]]:
    """Lista operaciones filtradas por tag."""
    ops = list_operations(spec)
    return [op for op in ops if tag in op.get("tags", [])]


def get_response_codes(spec: dict[str, Any], operation_id: str) -> dict[str, Any]:
    """Retorna los codigos de respuesta de una operacion."""
    operation = describe_operation(spec, operation_id)
    detail = spec["paths"][operation["path"]][operation["method"].lower()]
    responses = detail.get("responses", {})
    return {
        "operation_id": operation_id,
        "responses": {
            code: {"description": r.get("description", "")}
            for code, r in responses.items()
        },
    }


def compare_specs(spec_a: dict[str, Any], spec_b: dict[str, Any]) -> dict[str, Any]:
    """Compara dos specs OpenAPI."""
    ops_a = {op["operation_id"] for op in list_operations(spec_a)}
    ops_b = {op["operation_id"] for op in list_operations(spec_b)}

    added = ops_b - ops_a
    removed = ops_a - ops_b
    common = ops_a & ops_b

    return {
        "added_operations": list(added),
        "removed_operations": list(removed),
        "common_operations": list(common),
        "added_count": len(added),
        "removed_count": len(removed),
        "common_count": len(common),
    }


def generate_markdown_docs(spec: dict[str, Any]) -> str:
    """Genera documentacion en Markdown a partir del spec."""
    info = get_spec_info(spec)
    ops = list_operations(spec)

    lines = [
        f"# {info['title']} API Documentation",
        "",
        f"**Version:** {info['version']}",
        "",
        f"**Description:** {info['description']}",
        "",
        "## Endpoints",
        "",
    ]

    for op in ops:
        lines.append(f"### {op['method']} {op['path']}")
        lines.append(f"- **Operation ID:** {op['operation_id']}")
        lines.append(f"- **Summary:** {op['summary']}")
        if op.get("tags"):
            lines.append(f"- **Tags:** {', '.join(op['tags'])}")
        lines.append("")

    return "\n".join(lines)
