"""
Lógica de negocio de mcp-event-driven.

Validación y generación de esquemas, detección de eventos y simulación de flujos coreografiados.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp_shared.errors import FileNotFoundError, ParseError


def parse_event_schema(file_path: Path) -> dict[str, Any]:
    """Parse y valida un esquema JSON/AsyncAPI de un evento."""
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    try:
        content = file_path.read_text(encoding="utf-8")
        schema = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=f"Lectura fallida: {exc}") from exc

    # Heurística simple para determinar tipo de esquema
    schema_type = "JSON_SCHEMA"
    if "asyncapi" in schema:
        schema_type = "ASYNC_API"
    elif "openapi" in schema:
        schema_type = "OPEN_API"

    return {
        "file": file_path.name,
        "type": schema_type,
        "title": schema.get("title", schema.get("info", {}).get("title", "Untitled")),
        "properties": list(schema.get("properties", {}).keys())
        if schema_type == "JSON_SCHEMA"
        else [],
    }


def analyze_choreography(schemas_path: Path) -> dict[str, Any]:
    """Lee un directorio de esquemas y devuelve un mapa de eventos y propiedades."""
    if not schemas_path.exists() or not schemas_path.is_dir():
        return {"events_found": 0, "events": []}

    events = []
    for file in schemas_path.glob("*.json"):
        try:
            parsed = parse_event_schema(file)
            events.append(parsed)
        except Exception:
            continue

    return {
        "events_found": len(events),
        "events": events,
    }


def generate_event_payload(schema_properties: list[str]) -> dict[str, Any]:
    """Genera un payload de ejemplo (mock) basado en la lista de propiedades."""
    payload: dict[str, Any] = {}
    for prop in schema_properties:
        # Valores simulados básicos
        if "id" in prop.lower():
            payload[prop] = "evt_123456"
        elif "time" in prop.lower() or "date" in prop.lower() or "_at" in prop.lower():
            payload[prop] = "2024-01-01T00:00:00Z"
        elif "amount" in prop.lower() or "price" in prop.lower():
            payload[prop] = 99.99
        else:
            payload[prop] = "sample_data"

    return payload


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def validate_event_payload(schemas_path: Path, schema_file: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Valida un payload contra un schema JSON."""
    file_path = schemas_path / schema_file
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    try:
        schema = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    errors: list[str] = []

    for req in required:
        if req not in payload:
            errors.append(f"Missing required field: {req}")

    for key, value in payload.items():
        if key in properties:
            expected_type = properties[key].get("type", "")
            type_map = {"string": str, "number": (int, float), "integer": int, "boolean": bool, "array": list, "object": dict}
            if expected_type in type_map and not isinstance(value, type_map[expected_type]):
                errors.append(f"Field '{key}' expected {expected_type}, got {type(value).__name__}")

    return {
        "schema_file": schema_file,
        "valid": len(errors) == 0,
        "errors": errors,
        "payload": payload,
    }


def list_event_schemas(schemas_path: Path) -> list[dict[str, Any]]:
    """Lista todos los schemas disponibles en el directorio."""
    if not schemas_path.exists() or not schemas_path.is_dir():
        return []

    results: list[dict[str, Any]] = []
    for f in schemas_path.glob("*.json"):
        try:
            parsed = parse_event_schema(f)
            results.append({
                "file": f.name,
                "type": parsed["type"],
                "title": parsed["title"],
                "size": f.stat().st_size,
            })
        except Exception:
            results.append({"file": f.name, "type": "UNKNOWN", "title": "Error", "size": f.stat().st_size})

    return results


def create_event_schema(schemas_path: Path, name: str, properties: list[str], required: list[str] | None = None) -> dict[str, Any]:
    """Crea un nuevo schema JSON basico."""
    if not name.endswith(".json"):
        name = name + ".json"

    schema = {
        "title": name.replace(".json", "").replace("_", " ").title(),
        "type": "object",
        "properties": {prop: {"type": "string"} for prop in properties},
        "required": required or [],
    }

    file_path = schemas_path / name
    try:
        schemas_path.mkdir(parents=True, exist_ok=True)
        file_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=f"No se pudo crear: {exc}") from exc

    return {
        "created": True,
        "file": name,
        "path": str(file_path),
        "schema": schema,
    }


def trace_event_flow(schemas_path: Path, event_name: str) -> dict[str, Any]:
    """Traza el flujo de un evento a traves de los schemas disponibles."""
    if not schemas_path.exists():
        raise FileNotFoundError(str(schemas_path))

    related: list[dict[str, Any]] = []
    for f in schemas_path.glob("*.json"):
        try:
            parsed = parse_event_schema(f)
            if event_name.lower() in parsed.get("title", "").lower() or event_name.lower() in f.name.lower():
                related.append(parsed)
        except Exception:
            continue

    return {
        "event_name": event_name,
        "schemas_found": len(related),
        "schemas": related,
    }


def compare_event_schemas(schemas_path: Path, file_a: str, file_b: str) -> dict[str, Any]:
    """Compara dos schemas de eventos."""
    path_a = schemas_path / file_a
    path_b = schemas_path / file_b
    if not path_a.exists():
        raise FileNotFoundError(str(path_a))
    if not path_b.exists():
        raise FileNotFoundError(str(path_b))

    schema_a = json.loads(path_a.read_text(encoding="utf-8"))
    schema_b = json.loads(path_b.read_text(encoding="utf-8"))

    props_a = set(schema_a.get("properties", {}).keys())
    props_b = set(schema_b.get("properties", {}).keys())

    return {
        "file_a": file_a,
        "file_b": file_b,
        "common_properties": sorted(props_a & props_b),
        "only_in_a": sorted(props_a - props_b),
        "only_in_b": sorted(props_b - props_a),
        "compatibility": "compatible" if props_a == props_b else "partial" if props_a & props_b else "incompatible",
    }


def generate_event_documentation(schemas_path: Path, filename: str) -> str:
    """Genera documentacion markdown para un schema de evento."""
    file_path = schemas_path / filename
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    try:
        schema = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    title = schema.get("title", "Untitled")
    schema_type = "ASYNC_API" if "asyncapi" in schema else "JSON_SCHEMA" if "type" in schema else "UNKNOWN"
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    lines = [f"# Event: {title}", "", f"**Type:** {schema_type}", "", "## Properties", ""]
    if properties:
        lines.append("| Name | Type | Required |")
        lines.append("|------|------|----------|")
        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type", "any")
            is_required = "Yes" if prop_name in required else "No"
            lines.append(f"| {prop_name} | {prop_type} | {is_required} |")
    else:
        lines.append("No properties defined.")

    lines.extend(["", "## Example Payload", "", "```json", json.dumps(generate_event_payload(list(properties.keys())), indent=2), "```"])

    return "\n".join(lines)


def analyze_event_dependencies(schemas_path: Path) -> dict[str, Any]:
    """Analiza dependencias entre eventos basado en nombres de propiedades compartidas."""
    if not schemas_path.exists() or not schemas_path.is_dir():
        return {"dependencies": [], "total": 0}

    schemas: dict[str, set[str]] = {}
    for f in schemas_path.glob("*.json"):
        try:
            schema = json.loads(f.read_text(encoding="utf-8"))
            props = set(schema.get("properties", {}).keys())
            if props:
                schemas[f.name] = props
        except Exception:
            continue

    deps: list[dict[str, Any]] = []
    for name_a, props_a in schemas.items():
        for name_b, props_b in schemas.items():
            if name_a >= name_b:
                continue
            shared = props_a & props_b
            if shared:
                deps.append({
                    "schema_a": name_a,
                    "schema_b": name_b,
                    "shared_properties": sorted(shared),
                    "shared_count": len(shared),
                })

    return {
        "dependencies": deps,
        "total": len(deps),
        "schemas_analyzed": len(schemas),
    }


def generate_saga_template(steps: list[str]) -> dict[str, Any]:
    """Genera una plantilla de Saga con los pasos proporcionados."""
    saga_steps: list[dict[str, Any]] = []
    for i, step in enumerate(steps):
        saga_steps.append({
            "step": i + 1,
            "action": step,
            "compensation": f"Undo {step.lower()}",
            "event": f"step_{i+1}_completed",
        })

    return {
        "saga_type": "choreographed" if len(steps) > 3 else "orchestrated",
        "total_steps": len(steps),
        "steps": saga_steps,
        "compensation_order": list(reversed(range(1, len(steps) + 1))),
    }


def validate_asyncapi_spec(schemas_path: Path, filename: str) -> dict[str, Any]:
    """Valida un spec AsyncAPI basico."""
    file_path = schemas_path / filename
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    try:
        spec = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    errors: list[str] = []
    if "asyncapi" not in spec:
        errors.append("Missing 'asyncapi' version field")
    if "info" not in spec:
        errors.append("Missing 'info' section")
    elif "title" not in spec.get("info", {}):
        errors.append("Missing 'info.title'")
    if "channels" not in spec:
        errors.append("Missing 'channels' section")

    channels = spec.get("channels", {})
    for ch_name, ch_def in channels.items():
        if "subscribe" not in ch_def and "publish" not in ch_def:
            errors.append(f"Channel '{ch_name}' has no subscribe or publish operation")

    return {
        "file": filename,
        "valid": len(errors) == 0,
        "errors": errors,
        "channels_count": len(channels),
        "version": spec.get("asyncapi", "unknown"),
    }


def generate_event_test_cases(schema_file: str, schemas_path: Path) -> list[dict[str, Any]]:
    """Genera casos de prueba para un schema de evento."""
    file_path = schemas_path / schema_file
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    try:
        schema = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    properties = list(schema.get("properties", {}).keys())
    required = schema.get("required", [])

    test_cases: list[dict[str, Any]] = []

    # Valid case
    valid_payload = generate_event_payload(properties)
    test_cases.append({"name": "valid_payload", "payload": valid_payload, "should_pass": True})

    # Missing required fields
    if required:
        invalid_payload = {k: v for k, v in valid_payload.items() if k not in required[:1]}
        test_cases.append({"name": "missing_required_field", "payload": invalid_payload, "should_pass": False})

    # Empty payload
    test_cases.append({"name": "empty_payload", "payload": {}, "should_pass": len(required) == 0})

    # Extra fields
    extra_payload = {**valid_payload, "extra_field": "unexpected"}
    test_cases.append({"name": "extra_fields", "payload": extra_payload, "should_pass": True})

    return test_cases


def export_event_catalog(schemas_path: Path) -> dict[str, Any]:
    """Exporta un catalogo completo de todos los eventos."""
    if not schemas_path.exists() or not schemas_path.is_dir():
        return {"catalog": [], "total_events": 0}

    catalog: list[dict[str, Any]] = []
    for f in sorted(schemas_path.glob("*.json")):
        try:
            parsed = parse_event_schema(f)
            schema = json.loads(f.read_text(encoding="utf-8"))
            catalog.append({
                "file": f.name,
                "title": parsed["title"],
                "type": parsed["type"],
                "properties": list(schema.get("properties", {}).keys()),
                "required": schema.get("required", []),
                "channels": list(schema.get("channels", {}).keys()) if isinstance(schema.get("channels"), dict) else [],
            })
        except Exception:
            catalog.append({"file": f.name, "title": "ERROR", "type": "UNKNOWN", "properties": [], "required": [], "channels": []})

    return {
        "catalog": catalog,
        "total_events": len(catalog),
        "schemas_path": str(schemas_path),
    }


def get_event_stats(schemas_path: Path) -> dict[str, Any]:
    """Genera estadisticas rapidas del catalogo de eventos."""
    catalog_result = export_event_catalog(schemas_path)
    deps_result = analyze_event_dependencies(schemas_path)

    type_counts: dict[str, int] = {}
    total_properties = 0
    total_required = 0

    for evt in catalog_result.get("catalog", []):
        t = evt.get("type", "UNKNOWN")
        type_counts[t] = type_counts.get(t, 0) + 1
        total_properties += len(evt.get("properties", []))
        total_required += len(evt.get("required", []))

    return {
        "total_events": catalog_result.get("total_events", 0),
        "by_type": type_counts,
        "total_properties": total_properties,
        "total_required_fields": total_required,
        "avg_properties_per_event": round(total_properties / max(catalog_result.get("total_events", 1), 1), 2),
        "dependencies_found": deps_result.get("total", 0),
        "schemas_analyzed": deps_result.get("schemas_analyzed", 0),
    }
