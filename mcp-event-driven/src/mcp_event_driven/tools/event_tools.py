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
