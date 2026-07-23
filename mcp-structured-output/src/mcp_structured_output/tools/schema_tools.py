"""Herramientas locales de JSON Schema para Bedrock structured output.

Sin llamadas a APIs externas — 100% procesamiento local.
"""

from __future__ import annotations

import copy
from typing import Any

from mcp_shared.errors import ValidationError

# ---------------------------------------------------------------------------
# Constantes — features no soportadas por Bedrock Draft 2020-12
# ---------------------------------------------------------------------------

_UNSUPPORTED_NUMERIC: frozenset[str] = frozenset(
    {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"}
)
_UNSUPPORTED_STRING: frozenset[str] = frozenset({"minLength", "maxLength"})
_VALID_TYPES: frozenset[str] = frozenset(
    {"object", "array", "string", "integer", "number", "boolean", "null"}
)
_DEF_KEYS: tuple[str, ...] = ("$defs", "definitions")

# ---------------------------------------------------------------------------
# validate_schema
# ---------------------------------------------------------------------------


def validate_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Valida que un JSON Schema sea compatible con Bedrock structured output (Draft 2020-12).

    Analiza el schema localmente sin hacer ninguna llamada a AWS.

    Args:
        schema: JSON Schema a validar (dict Python).

    Returns:
        Dict con:
        - ``valid`` (bool): True si no hay issues de severidad "error".
        - ``issues`` (list): Lista de ``{"path": str, "message": str, "severity": "error"|"warning"}``.

    Raises:
        ValidationError: Si ``schema`` no es un dict.
    """
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un objeto JSON (dict).")

    issues: list[dict[str, str]] = []
    defs = _collect_defs(schema)

    # Detectar schemas recursivos
    recursive_names = _detect_recursive_defs(defs)
    for name in recursive_names:
        issues.append(
            {
                "path": f"$defs.{name}",
                "message": f"La definición '{name}' forma un ciclo recursivo (no soportado por Bedrock).",
                "severity": "error",
            }
        )

    _walk_validate(schema, "$", issues)
    valid = not any(i["severity"] == "error" for i in issues)
    return {"valid": valid, "issues": issues}


def _collect_defs(schema: dict[str, Any]) -> dict[str, Any]:
    """Recolecta definiciones de $defs y definitions."""
    defs: dict[str, Any] = {}
    for key in _DEF_KEYS:
        if key in schema and isinstance(schema[key], dict):
            defs.update(schema[key])
    return defs


def _refs_in(schema: Any) -> set[str]:
    """Extrae todos los nombres de definición referenciados via $ref interno."""
    if not isinstance(schema, dict):
        return set()
    refs: set[str] = set()
    if "$ref" in schema and isinstance(schema["$ref"], str):
        ref = schema["$ref"]
        parts = ref.lstrip("#/").split("/")
        if len(parts) >= 2 and parts[0] in _DEF_KEYS:
            refs.add(parts[1])
    for value in schema.values():
        if isinstance(value, dict):
            refs |= _refs_in(value)
        elif isinstance(value, list):
            for item in value:
                refs |= _refs_in(item)
    return refs


def _detect_recursive_defs(defs: dict[str, Any]) -> list[str]:
    """Devuelve nombres de definiciones que forman ciclos."""
    recursive: list[str] = []

    def _has_cycle(name: str, visited: set[str]) -> bool:
        if name in visited:
            return True
        if name not in defs:
            return False
        for ref_name in _refs_in(defs[name]):
            if _has_cycle(ref_name, visited | {name}):
                return True
        return False

    for name in defs:
        if _has_cycle(name, set()):
            recursive.append(name)
    return recursive


def _walk_validate(node: Any, path: str, issues: list[dict[str, str]]) -> None:
    """Recorre el schema recursivamente y acumula issues."""
    if not isinstance(node, dict):
        return

    # --- Constraints numéricas ---
    for kw in _UNSUPPORTED_NUMERIC:
        if kw in node:
            issues.append(
                {
                    "path": f"{path}.{kw}",
                    "message": f"'{kw}' no está soportado por Bedrock structured output.",
                    "severity": "error",
                }
            )

    # --- Constraints de string ---
    for kw in _UNSUPPORTED_STRING:
        if kw in node:
            issues.append(
                {
                    "path": f"{path}.{kw}",
                    "message": f"'{kw}' no está soportado por Bedrock structured output.",
                    "severity": "error",
                }
            )

    # --- additionalProperties ---
    if "additionalProperties" in node and node["additionalProperties"] is not False:
        issues.append(
            {
                "path": f"{path}.additionalProperties",
                "message": (
                    "'additionalProperties' debe ser false. "
                    "Bedrock no soporta otro valor (ni true ni un sub-schema)."
                ),
                "severity": "error",
            }
        )

    # --- minItems ---
    if "minItems" in node:
        v = node["minItems"]
        if v not in (0, 1):
            issues.append(
                {
                    "path": f"{path}.minItems",
                    "message": f"'minItems' solo puede ser 0 o 1 (valor actual: {v}).",
                    "severity": "error",
                }
            )

    # --- $ref externo ---
    if "$ref" in node and isinstance(node["$ref"], str):
        ref = node["$ref"]
        if not ref.startswith("#"):
            issues.append(
                {
                    "path": f"{path}.$ref",
                    "message": f"$ref externo '{ref}' no está soportado. Solo se permiten referencias internas (#/...).",
                    "severity": "error",
                }
            )

    # --- enum con tipos no soportados ---
    if "enum" in node and isinstance(node["enum"], list):
        for i, val in enumerate(node["enum"]):
            if isinstance(val, (dict, list)):
                issues.append(
                    {
                        "path": f"{path}.enum[{i}]",
                        "message": "Los valores de 'enum' deben ser string, number, boolean o null.",
                        "severity": "error",
                    }
                )

    # --- Tipos desconocidos ---
    if "type" in node and isinstance(node["type"], str):
        if node["type"] not in _VALID_TYPES:
            issues.append(
                {
                    "path": f"{path}.type",
                    "message": f"Tipo '{node['type']}' no es un tipo JSON Schema básico válido.",
                    "severity": "warning",
                }
            )

    # --- additionalProperties ausente en objeto → warning ---
    if node.get("type") == "object" and "additionalProperties" not in node:
        issues.append(
            {
                "path": path,
                "message": (
                    "Objeto sin 'additionalProperties: false'. "
                    "Bedrock lo requiere para garantizar el schema."
                ),
                "severity": "warning",
            }
        )

    # --- Descender en sub-schemas ---
    if "properties" in node and isinstance(node["properties"], dict):
        for prop_name, prop_schema in node["properties"].items():
            _walk_validate(prop_schema, f"{path}.properties.{prop_name}", issues)

    if "items" in node:
        _walk_validate(node["items"], f"{path}.items", issues)

    for kw in ("anyOf", "allOf", "oneOf"):
        if kw in node and isinstance(node[kw], list):
            for i, sub in enumerate(node[kw]):
                _walk_validate(sub, f"{path}.{kw}[{i}]", issues)

    if "not" in node:
        _walk_validate(node["not"], f"{path}.not", issues)

    for def_key in _DEF_KEYS:
        if def_key in node and isinstance(node[def_key], dict):
            for def_name, def_schema in node[def_key].items():
                _walk_validate(def_schema, f"{path}.{def_key}.{def_name}", issues)


# ---------------------------------------------------------------------------
# generate_schema
# ---------------------------------------------------------------------------


def generate_schema(
    example: dict[str, Any],
    name: str = "schema",
    description: str | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    """Genera un JSON Schema Bedrock-compatible a partir de un objeto JSON de ejemplo.

    Infiere los tipos de cada campo y aplica ``additionalProperties: false``
    en todos los objetos. Los campos ``null`` en el ejemplo se marcan como
    ``anyOf: [{type: string}, {type: null}]`` ya que el tipo real es desconocido.

    Args:
        example: Objeto JSON de ejemplo (dict Python).
        name: Nombre del schema (usado como ``$schema`` title).
        description: Descripción opcional del schema.
        strict: Si True, agrega ``additionalProperties: false`` en todos los objetos
                y marca todos los campos como ``required``.

    Returns:
        Dict con:
        - ``schema`` (dict): JSON Schema generado.
        - ``field_count`` (int): Número total de campos en el nivel raíz.
        - ``warnings`` (list[str]): Advertencias sobre campos ambiguos.

    Raises:
        ValidationError: Si ``example`` no es un dict.
    """
    if not isinstance(example, dict):
        raise ValidationError(field="example", message="El ejemplo debe ser un objeto JSON (dict).")

    warnings: list[str] = []
    schema = _infer_schema(example, warnings=warnings, strict=strict)

    if description:
        schema["description"] = description

    schema["title"] = name

    return {
        "schema": schema,
        "field_count": len(example),
        "warnings": warnings,
    }


def _infer_schema(value: Any, warnings: list[str], strict: bool) -> dict[str, Any]:
    """Infiere recursivamente el sub-schema para un valor Python."""
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if isinstance(value, str):
        return {"type": "string"}
    if isinstance(value, list):
        return _infer_array_schema(value, warnings, strict)
    if isinstance(value, dict):
        return _infer_object_schema(value, warnings, strict)
    # Tipo desconocido — fallback a string
    warnings.append(f"Tipo Python '{type(value).__name__}' no reconocido, inferido como string.")
    return {"type": "string"}


def _infer_array_schema(value: list[Any], warnings: list[str], strict: bool) -> dict[str, Any]:
    """Infiere schema de array a partir del primer elemento."""
    schema: dict[str, Any] = {"type": "array"}
    if value:
        schema["items"] = _infer_schema(value[0], warnings, strict)
    else:
        schema["items"] = {"type": "string"}
        warnings.append("Array vacío en el ejemplo; se asume items de tipo string.")
    return schema


def _infer_object_schema(
    value: dict[str, Any], warnings: list[str], strict: bool
) -> dict[str, Any]:
    """Infiere schema de objeto recursivamente."""
    properties: dict[str, Any] = {}
    null_fields: list[str] = []

    for key, val in value.items():
        if val is None:
            properties[key] = {"anyOf": [{"type": "string"}, {"type": "null"}]}
            null_fields.append(key)
        else:
            properties[key] = _infer_schema(val, warnings, strict)

    if null_fields:
        warnings.append(
            f"Campos con valor null en el ejemplo (tipo real desconocido, inferido como string|null): "
            f"{', '.join(null_fields)}"
        )

    schema: dict[str, Any] = {"type": "object", "properties": properties}

    if strict:
        schema["required"] = list(value.keys())
        schema["additionalProperties"] = False

    return schema


# ---------------------------------------------------------------------------
# sanitize_schema
# ---------------------------------------------------------------------------


def sanitize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Transforma un JSON Schema para que sea compatible con Bedrock structured output.

    Elimina o transforma automáticamente todas las features no soportadas:
    - Remueve constraints numéricas y de string.
    - Fuerza ``additionalProperties: false`` en objetos.
    - Reemplaza ``$ref`` externos por ``{"type": "string"}``.
    - Ajusta ``minItems`` > 1 a 1.

    Args:
        schema: JSON Schema potencialmente incompatible (dict Python). No se modifica el original.

    Returns:
        Dict con:
        - ``sanitized`` (dict): Schema transformado.
        - ``changes`` (list): Lista de ``{"path": str, "action": str, "reason": str}``.
        - ``was_valid`` (bool): Si el schema original ya era válido (sin cambios).

    Raises:
        ValidationError: Si ``schema`` no es un dict.
    """
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un objeto JSON (dict).")

    sanitized = copy.deepcopy(schema)
    changes: list[dict[str, str]] = []
    _walk_sanitize(sanitized, "$", changes)

    return {
        "sanitized": sanitized,
        "changes": changes,
        "was_valid": len(changes) == 0,
    }


def _walk_sanitize(node: Any, path: str, changes: list[dict[str, str]]) -> None:
    """Recorre y modifica el schema en profundidad."""
    if not isinstance(node, dict):
        return

    # --- Remover constraints numéricas ---
    for kw in _UNSUPPORTED_NUMERIC:
        if kw in node:
            del node[kw]
            changes.append(
                {
                    "path": f"{path}.{kw}",
                    "action": "removed",
                    "reason": f"'{kw}' no está soportado por Bedrock structured output.",
                }
            )

    # --- Remover constraints de string ---
    for kw in _UNSUPPORTED_STRING:
        if kw in node:
            del node[kw]
            changes.append(
                {
                    "path": f"{path}.{kw}",
                    "action": "removed",
                    "reason": f"'{kw}' no está soportado por Bedrock structured output.",
                }
            )

    # --- additionalProperties ---
    if "additionalProperties" in node and node["additionalProperties"] is not False:
        node["additionalProperties"] = False
        changes.append(
            {
                "path": f"{path}.additionalProperties",
                "action": "set_to_false",
                "reason": "Bedrock requiere additionalProperties: false en objetos.",
            }
        )
    elif node.get("type") == "object" and "additionalProperties" not in node:
        node["additionalProperties"] = False
        changes.append(
            {
                "path": f"{path}.additionalProperties",
                "action": "added_false",
                "reason": "Bedrock requiere additionalProperties: false en todos los objetos.",
            }
        )

    # --- minItems ---
    if "minItems" in node:
        v = node["minItems"]
        if v not in (0, 1):
            node["minItems"] = 1
            changes.append(
                {
                    "path": f"{path}.minItems",
                    "action": f"changed_{v}_to_1",
                    "reason": f"Bedrock solo soporta minItems 0 o 1 (valor original: {v}).",
                }
            )

    # --- $ref externo ---
    if "$ref" in node and isinstance(node["$ref"], str) and not node["$ref"].startswith("#"):
        original_ref = node["$ref"]
        node.clear()
        node["type"] = "string"
        changes.append(
            {
                "path": f"{path}.$ref",
                "action": "replaced_with_string",
                "reason": f"$ref externo '{original_ref}' reemplazado por {{type: string}} (Bedrock no soporta refs externos).",
            }
        )
        return  # el nodo fue reemplazado, no hay más que procesar aquí

    # --- enum con tipos complejos ---
    if "enum" in node and isinstance(node["enum"], list):
        cleaned: list[Any] = []
        removed_count = 0
        for val in node["enum"]:
            if isinstance(val, (dict, list)):
                removed_count += 1
            else:
                cleaned.append(val)
        if removed_count:
            node["enum"] = cleaned
            changes.append(
                {
                    "path": f"{path}.enum",
                    "action": f"removed_{removed_count}_complex_values",
                    "reason": "Los valores de 'enum' deben ser string, number, boolean o null.",
                }
            )

    # --- Descender recursivamente ---
    if "properties" in node and isinstance(node["properties"], dict):
        for prop_name, prop_schema in node["properties"].items():
            _walk_sanitize(prop_schema, f"{path}.properties.{prop_name}", changes)

    if "items" in node:
        _walk_sanitize(node["items"], f"{path}.items", changes)

    for kw in ("anyOf", "allOf", "oneOf"):
        if kw in node and isinstance(node[kw], list):
            for i, sub in enumerate(node[kw]):
                _walk_sanitize(sub, f"{path}.{kw}[{i}]", changes)

    if "not" in node:
        _walk_sanitize(node["not"], f"{path}.not", changes)

    for def_key in _DEF_KEYS:
        if def_key in node and isinstance(node[def_key], dict):
            for def_name, def_schema in node[def_key].items():
                _walk_sanitize(def_schema, f"{path}.{def_key}.{def_name}", changes)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def schema_to_typescript(schema: dict[str, Any]) -> str:
    """Convierte un JSON Schema a interfaces TypeScript."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    lines: list[str] = []
    _ts_from_schema(schema, "Root", lines)
    return "\n".join(lines)


def _ts_from_schema(node: Any, name: str, lines: list[str]) -> str:
    if not isinstance(node, dict):
        return "any"
    t = node.get("type", "")
    if t == "object" or "properties" in node:
        props = node.get("properties", {})
        required = set(node.get("required", []))
        fields: list[str] = []
        for prop_name, prop_schema in props.items():
            ts_type = _ts_from_schema(prop_schema, f"{name}_{prop_name}", lines)
            optional = "" if prop_name in required else "?"
            fields.append(f"  {prop_name}{optional}: {ts_type};")
        lines.append(f"interface {name} {{")
        lines.extend(fields)
        lines.append("}")
        return name
    elif t == "array":
        item_type = _ts_from_schema(node.get("items", {}), f"{name}_item", lines)
        return f"{item_type}[]"
    elif t == "string":
        return "string"
    elif t == "integer" or t == "number":
        return "number"
    elif t == "boolean":
        return "boolean"
    elif t == "null":
        return "null"
    return "any"


def schema_to_python(schema: dict[str, Any], class_name: str = "RootModel") -> str:
    """Convierte un JSON Schema a una clase Pydantic."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    lines: list[str] = ["from pydantic import BaseModel", ""]
    _py_from_schema(schema, class_name, lines)
    return "\n".join(lines)


def _py_from_schema(node: Any, name: str, lines: list[str]) -> str:
    if not isinstance(node, dict):
        return "Any"
    t = node.get("type", "")
    if t == "object" or "properties" in node:
        props = node.get("properties", {})
        required = set(node.get("required", []))
        fields: list[str] = []
        for prop_name, prop_schema in props.items():
            py_type = _py_from_schema(prop_schema, f"{name}_{prop_name}", lines)
            if prop_name not in required:
                fields.append(f"    {prop_name}: {py_type} | None = None")
            else:
                fields.append(f"    {prop_name}: {py_type}")
        lines.append(f"class {name}(BaseModel):")
        if fields:
            lines.extend(fields)
        else:
            lines.append("    pass")
        lines.append("")
        return name
    elif t == "array":
        item_type = _py_from_schema(node.get("items", {}), f"{name}_item", lines)
        return f"list[{item_type}]"
    elif t == "string":
        return "str"
    elif t == "integer":
        return "int"
    elif t == "number":
        return "float"
    elif t == "boolean":
        return "bool"
    elif t == "null":
        return "None"
    return "Any"


def flatten_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Aplana un schema resolviendo $ref internos."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    defs = _collect_defs(schema)
    return _resolve_refs(copy.deepcopy(schema), defs)


def _resolve_refs(node: Any, defs: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        if "$ref" in node and isinstance(node["$ref"], str):
            ref = node["$ref"]
            parts = ref.lstrip("#/").split("/")
            if len(parts) >= 2 and parts[0] in _DEF_KEYS:
                def_name = parts[1]
                if def_name in defs:
                    return _resolve_refs(copy.deepcopy(defs[def_name]), defs)
            return node
        return {k: _resolve_refs(v, defs) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(item, defs) for item in node]
    return node


def merge_schemas(schemas: list[dict[str, Any]]) -> dict[str, Any]:
    """Combina multiples schemas en uno solo usando allOf."""
    if not isinstance(schemas, list):
        raise ValidationError(field="schemas", message="schemas debe ser una lista.")
    if not schemas:
        return {"type": "object", "properties": {}, "additionalProperties": False}
    merged_props: dict[str, Any] = {}
    merged_required: list[str] = []
    for s in schemas:
        if not isinstance(s, dict):
            continue
        props = s.get("properties", {})
        merged_props.update(props)
        for r in s.get("required", []):
            if r not in merged_required:
                merged_required.append(r)
    result: dict[str, Any] = {
        "type": "object",
        "properties": merged_props,
        "additionalProperties": False,
    }
    if merged_required:
        result["required"] = merged_required
    return result


def extract_schema_fields(schema: dict[str, Any]) -> list[dict[str, Any]]:
    """Lista todos los campos de un schema con su tipo y ruta."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    fields: list[dict[str, Any]] = []
    _extract_fields(schema, "$", fields)
    return fields


def _extract_fields(node: Any, path: str, fields: list[dict[str, Any]]) -> None:
    if not isinstance(node, dict):
        return
    if "properties" in node and isinstance(node["properties"], dict):
        for prop_name, prop_schema in node["properties"].items():
            field_path = f"{path}.{prop_name}"
            field_type = prop_schema.get("type", "unknown") if isinstance(prop_schema, dict) else "unknown"
            fields.append({
                "path": field_path,
                "name": prop_name,
                "type": field_type,
                "required": prop_name in node.get("required", []),
            })
            _extract_fields(prop_schema, field_path, fields)
    if "items" in node:
        _extract_fields(node["items"], f"{path}[]", fields)


def schema_to_markdown(schema: dict[str, Any]) -> str:
    """Genera documentacion Markdown desde un JSON Schema."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    lines: list[str] = []
    title = schema.get("title", "Schema")
    desc = schema.get("description", "")
    lines.append(f"# {title}")
    if desc:
        lines.append(f"\n{desc}")
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    if props:
        lines.append("\n| Campo | Tipo | Requerido | Descripcion |")
        lines.append("|-------|------|-----------|-------------|")
        for name, prop in props.items():
            ptype = prop.get("type", "any") if isinstance(prop, dict) else "any"
            req = "Si" if name in required else "No"
            pdesc = prop.get("description", "") if isinstance(prop, dict) else ""
            lines.append(f"| {name} | {ptype} | {req} | {pdesc} |")
    return "\n".join(lines)


def validate_json_against_schema(instance: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Valida una instancia JSON contra un JSON Schema."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    try:
        jsonschema.validate(instance=instance, schema=schema)
        return {"valid": True, "errors": []}
    except jsonschema.ValidationError as exc:
        return {"valid": False, "errors": [{"path": list(exc.path), "message": exc.message}]}
    except jsonschema.SchemaError as exc:
        return {"valid": False, "errors": [{"path": [], "message": f"Schema error: {exc.message}"}]}


def schema_diff(schema_a: dict[str, Any], schema_b: dict[str, Any]) -> dict[str, Any]:
    """Compara dos schemas y retorna las diferencias."""
    if not isinstance(schema_a, dict) or not isinstance(schema_b, dict):
        raise ValidationError(field="schema", message="Ambos schemas deben ser dicts.")
    props_a = set(schema_a.get("properties", {}).keys())
    props_b = set(schema_b.get("properties", {}).keys())
    added = props_b - props_a
    removed = props_a - props_b
    common = props_a & props_b
    type_changes: list[dict[str, str]] = []
    for name in common:
        ta = schema_a["properties"][name].get("type", "any")
        tb = schema_b["properties"][name].get("type", "any")
        if ta != tb:
            type_changes.append({"field": name, "from": ta, "to": tb})
    req_a = set(schema_a.get("required", []))
    req_b = set(schema_b.get("required", []))
    return {
        "added_fields": sorted(added),
        "removed_fields": sorted(removed),
        "type_changes": type_changes,
        "required_added": sorted(req_b - req_a),
        "required_removed": sorted(req_a - req_b),
        "are_equal": not added and not removed and not type_changes and req_a == req_b,
    }


def schema_complexity(schema: dict[str, Any]) -> dict[str, Any]:
    """Calcula metricas de complejidad de un schema."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    fields = extract_schema_fields(schema)
    max_depth = 0
    for f in fields:
        depth = f["path"].count(".")
        if depth > max_depth:
            max_depth = depth
    return {
        "total_fields": len(fields),
        "max_depth": max_depth,
        "has_refs": "$ref" in json.dumps(schema),
        "has_defs": any(k in schema for k in _DEF_KEYS),
        "has_enums": _count_enums(schema),
        "estimated_tokens": len(json.dumps(schema)) // 4,
    }


def _count_enums(node: Any) -> int:
    if not isinstance(node, dict):
        return 0
    count = 1 if "enum" in node else 0
    for v in node.values():
        if isinstance(v, dict):
            count += _count_enums(v)
        elif isinstance(v, list):
            for item in v:
                count += _count_enums(item)
    return count


def simplify_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Simplifica un schema removiendo metadatos innecesarios."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    simplified = copy.deepcopy(schema)
    _remove_metadata(simplified)
    return simplified


def _remove_metadata(node: Any) -> None:
    if isinstance(node, dict):
        for key in list(node.keys()):
            if key in ("title", "description", "default", "examples", "$id", "$schema"):
                del node[key]
            elif isinstance(node[key], dict):
                _remove_metadata(node[key])
            elif isinstance(node[key], list):
                for item in node[key]:
                    _remove_metadata(item)


def schema_to_json_example(schema: dict[str, Any]) -> dict[str, Any]:
    """Genera un ejemplo JSON desde un JSON Schema."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    return _generate_example(schema)


def _generate_example(node: Any) -> Any:
    if not isinstance(node, dict):
        return None
    if "enum" in node and isinstance(node["enum"], list) and node["enum"]:
        return node["enum"][0]
    if "default" in node:
        return node["default"]
    if "examples" in node and isinstance(node["examples"], list) and node["examples"]:
        return node["examples"][0]
    t = node.get("type", "")
    if t == "object" or "properties" in node:
        result: dict[str, Any] = {}
        for prop_name, prop_schema in node.get("properties", {}).items():
            result[prop_name] = _generate_example(prop_schema)
        return result
    elif t == "array":
        return [_generate_example(node.get("items", {}))]
    elif t == "string":
        return "string"
    elif t == "integer":
        return 0
    elif t == "number":
        return 0.0
    elif t == "boolean":
        return True
    elif t == "null":
        return None
    return None


def list_schema_keywords(schema: dict[str, Any]) -> list[str]:
    """Lista todas las keywords usadas en un schema."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    keywords: set[str] = set()
    _collect_keywords(schema, keywords)
    return sorted(keywords)


def _collect_keywords(node: Any, keywords: set[str]) -> None:
    if isinstance(node, dict):
        for k in node.keys():
            keywords.add(k)
        for v in node.values():
            _collect_keywords(v, keywords)
    elif isinstance(node, list):
        for item in node:
            _collect_keywords(item, keywords)


def count_schema_fields(schema: dict[str, Any]) -> dict[str, Any]:
    """Cuenta el numero total de campos recursivamente."""
    fields = extract_schema_fields(schema)
    by_type: dict[str, int] = {}
    for f in fields:
        t = f["type"]
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "total": len(fields),
        "by_type": by_type,
        "required": sum(1 for f in fields if f["required"]),
        "optional": sum(1 for f in fields if not f["required"]),
    }


def schema_to_table(schema: dict[str, Any]) -> str:
    """Genera una representacion en tabla de un schema."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    fields = extract_schema_fields(schema)
    if not fields:
        return "Schema sin campos."
    lines = ["| Ruta | Nombre | Tipo | Requerido |", "|------|--------|------|-----------|"]
    for f in fields:
        req = "Si" if f["required"] else "No"
        lines.append(f"| {f['path']} | {f['name']} | {f['type']} | {req} |")
    return "\n".join(lines)


def check_schema_compatibility(schema: dict[str, Any]) -> dict[str, Any]:
    """Verifica compatibilidad con Bedrock y retorna un score."""
    validation = validate_schema(schema)
    errors = [i for i in validation["issues"] if i["severity"] == "error"]
    warnings = [i for i in validation["issues"] if i["severity"] == "warning"]
    total = len(validation["issues"])
    score = 100 if total == 0 else max(0, 100 - (len(errors) * 25 + len(warnings) * 5))
    return {
        "score": score,
        "compatible": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def schema_to_openapi(schema: dict[str, Any], path: str = "/data") -> dict[str, Any]:
    """Convierte un JSON Schema a un componente OpenAPI 3.1."""
    if not isinstance(schema, dict):
        raise ValidationError(field="schema", message="El schema debe ser un dict.")
    return {
        "openapi": "3.1.0",
        "info": {
            "title": schema.get("title", "API"),
            "version": "1.0.0",
        },
        "paths": {
            path: {
                "get": {
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "schema": schema,
                                },
                            },
                        },
                    },
                },
            },
        },
    }
