"""Tools de templates para COVAF.

Lista, valida y genera scaffolds de templates de extracción para los motores
Java y Python.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp_shared.errors import McpError

# Schemas de templates conocidos.
TEMPLATE_SCHEMAS = {
    "cartas_confirmacion": {
        "domain": "Cartas de Confirmación bursátiles",
        "motor": "java",
        "fields": [
            "fondo", "tipoValor", "instrumento", "serie", "tipoMovimiento",
            "titulos", "monto", "fechaOperacion", "institucion", "contrato",
            "firma", "observaciones",
        ],
        "strategies": ["REGEX", "KEY_WORD", "TABLE", "ADVANCED"],
        "layouts_count": 34,
    },
    "oficios_pld": {
        "domain": "Oficios PLD (Prevención de Lavado de Dinero)",
        "motor": "java",
        "fields": [
            "autoridad", "numeroOficio", "fecha", "tipoRequerimiento",
            "personas", "entidades", "rfc", "instrucciones", "aseguramientos",
            "solicitudSIARA",
        ],
        "strategies": ["REGEX", "KEY_WORD", "TABLE", "FORMS"],
    },
    "prospectos_cnbv": {
        "domain": "Prospectos de fondos de inversión CNBV",
        "motor": "python",
        "fields": [
            "fondo", "serie", "rendimiento", "comision", "riesgo",
            "horizonte", "liquidez", "fiscal",
        ],
        "tiers": [1, 2, 3],
    },
}


def template_list(workspace: Path, docs_path: Path) -> dict[str, Any]:
    """Lista los templates de extracción disponibles en COVAF."""
    return {
        "templates": [
            {
                "name": name,
                "domain": schema["domain"],
                "motor": schema["motor"],
                "field_count": len(schema["fields"]),
            }
            for name, schema in TEMPLATE_SCHEMAS.items()
        ],
        "count": len(TEMPLATE_SCHEMAS),
    }


def template_get_schema(template_name: str) -> dict[str, Any]:
    """Obtiene el schema completo de un template específico."""
    if template_name not in TEMPLATE_SCHEMAS:
        raise McpError(
            f"Template desconocido: {template_name}. "
            f"Disponibles: {list(TEMPLATE_SCHEMAS)}"
        )
    return {
        "name": template_name,
        "schema": TEMPLATE_SCHEMAS[template_name],
    }


def template_validate(template_name: str, data_json: str) -> dict[str, Any]:
    """Valida un JSON de datos contra el schema de un template."""
    if template_name not in TEMPLATE_SCHEMAS:
        raise McpError(f"Template desconocido: {template_name}")
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as exc:
        raise McpError(f"JSON inválido: {exc}") from exc
    schema = TEMPLATE_SCHEMAS[template_name]
    required_fields = set(schema["fields"])
    provided_fields = set(data.keys()) if isinstance(data, dict) else set()
    missing = required_fields - provided_fields
    extra = provided_fields - required_fields
    return {
        "template": template_name,
        "valid": len(missing) == 0,
        "missing_fields": sorted(missing),
        "extra_fields": sorted(extra),
        "coverage_pct": round(
            len(required_fields - missing) / len(required_fields) * 100, 1
        ) if required_fields else 100,
    }


def template_scaffold_new(
    workspace: Path,
    ia_path: Path,
    plugin_name: str,
    domain_description: str = "",
) -> dict[str, Any]:
    """Genera un scaffold de nuevo plugin para el motor Python DataRefineryIA.

    Usa el comando `python -m core.scaffold <nombre>` del motor.
    """
    full = workspace / ia_path
    if not full.exists():
        raise McpError(f"Motor Python no encontrado en {full}")
    scaffold = full / "core/scaffold.py"
    if not scaffold.exists():
        raise McpError("core/scaffold.py no encontrado en el motor Python")
    return {
        "plugin_name": plugin_name,
        "domain": domain_description or "No especificado",
        "scaffold_command": f"python -m core.scaffold {plugin_name}",
        "output_dir": f"plugins/{plugin_name}/",
        "files_to_create": [
            f"plugins/{plugin_name}/plugin.py",
            f"plugins/{plugin_name}/schema.py",
            f"plugins/{plugin_name}/field_tiers.py",
            f"plugins/{plugin_name}/__init__.py",
        ],
        "instructions": (
            "Ejecuta el comando scaffold desde el directorio del motor Python. "
            "Después edita schema.py con los campos del dominio, field_tiers.py "
            "con la clasificación de campos, y plugin.py con la lógica de extracción."
        ),
    }
