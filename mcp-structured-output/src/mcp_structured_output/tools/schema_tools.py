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
        raise ValidationError(
            field="example", message="El ejemplo debe ser un objeto JSON (dict)."
        )

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


def _infer_array_schema(
    value: list[Any], warnings: list[str], strict: bool
) -> dict[str, Any]:
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
