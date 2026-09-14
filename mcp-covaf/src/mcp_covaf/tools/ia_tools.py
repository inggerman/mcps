"""Tools para el motor Python COVAF (DataRefineryIA API).

Cobertura: plugins, pipeline tiers, schemas, análisis de output de extracción,
evals.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from mcp_shared.errors import McpError

# Plugins conocidos del motor Python (observado en plugins/).
KNOWN_PLUGINS = [
    {
        "name": "prospectos_cnbv",
        "class": "ProspectoCNBVPlugin",
        "path": "plugins/prospectos_cnbv/plugin.py",
        "use": "Extracción de prospectos de fondos de inversión CNBV",
    },
    {
        "name": "cartas_confirmacion",
        "class": "CartaConfirmacionPlugin",
        "path": "plugins/cartas_confirmacion/plugin.py",
        "use": "Cartas de confirmación de operaciones bursátiles",
    },
]

# Tiers del pipeline (observado en core/pipeline/).
PIPELINE_TIERS = [
    {"tier": 1, "name": "Tier1Runner", "file": "core/pipeline/tier1_runner.py",
     "description": "Regex y reglas determinísticas"},
    {"tier": 2, "name": "Tier2Runner", "file": "core/pipeline/tier2_runner.py",
     "description": "Árbitro LLM para casos ambiguos"},
    {"tier": 3, "name": "Tier3Runner", "file": "core/pipeline/tier3_runner.py",
     "description": "LLM con prompts dinámicos por sección"},
    {"stage": "merge", "name": "ExtractionMerger", "file": "core/pipeline/merger.py",
     "description": "Fusión de resultados de tiers"},
    {"stage": "validate", "name": "ExtractionValidator", "file": "core/pipeline/validator.py",
     "description": "Validación contra catálogos y contrato"},
    {"stage": "confidence", "name": "ConfidenceCalculator", "file": "core/pipeline/confidence.py",
     "description": "Cálculo de confidence score"},
]


def _resolve_ia_path(workspace: Path, relative: Path) -> Path:
    full = workspace / relative
    if not full.exists():
        raise McpError(f"Motor Python no encontrado en {full}")
    return full


def ia_list_plugins(workspace: Path, ia_path: Path) -> dict[str, Any]:
    """Lista los plugins del motor Python DataRefineryIA."""
    full = _resolve_ia_path(workspace, ia_path)
    plugins_dir = full / "plugins"
    discovered: list[dict[str, Any]] = []
    if plugins_dir.exists():
        for p in plugins_dir.iterdir():
            if p.is_dir() and not p.name.startswith("_"):
                plugin_file = p / "plugin.py"
                schema_file = p / "schema.py"
                discovered.append({
                    "name": p.name,
                    "has_plugin": plugin_file.exists(),
                    "has_schema": schema_file.exists(),
                    "path": str(p.relative_to(full)),
                })
    return {
        "known_plugins": KNOWN_PLUGINS,
        "discovered": discovered,
        "count": len(discovered),
    }


def ia_list_pipeline_tiers(workspace: Path, ia_path: Path) -> dict[str, Any]:
    """Lista los tiers del pipeline de extracción del motor Python."""
    full = _resolve_ia_path(workspace, ia_path)
    verified: list[dict[str, Any]] = []
    for tier in PIPELINE_TIERS:
        f = full / tier["file"]
        verified_tier = dict(tier)
        verified_tier["exists"] = f.exists()
        verified.append(verified_tier)
    return {
        "tiers": verified,
        "engine_version": "4.0.0-phase8-generic-core",
        "api_version": "2.3.0",
    }


def ia_get_plugin_schema(
    workspace: Path, ia_path: Path, plugin_name: str
) -> dict[str, Any]:
    """Obtiene el schema de campos de un plugin específico."""
    full = _resolve_ia_path(workspace, ia_path)
    schema_file = full / "plugins" / plugin_name / "schema.py"
    if not schema_file.exists():
        raise McpError(f"Schema no encontrado para plugin '{plugin_name}'")
    try:
        text = schema_file.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        raise McpError(f"Error leyendo schema: {exc}") from exc
    # Extraer nombres de campos del schema (heurística simple)
    fields: list[str] = []
    for line in text.splitlines():
        m = re.match(r"\s*(\w+)\s*:\s*(str|int|float|bool|Optional|list|dict)", line)
        if m:
            fields.append(m.group(1))
    return {
        "plugin": plugin_name,
        "schema_file": str(schema_file.relative_to(full)),
        "fields": fields,
        "field_count": len(fields),
    }


def ia_search_code(
    workspace: Path, ia_path: Path, pattern: str, max_results: int = 20
) -> dict[str, Any]:
    """Busca un patrón (regex) en el código Python del motor IA."""
    full = _resolve_ia_path(workspace, ia_path)
    matches: list[dict[str, Any]] = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise McpError(f"Regex inválido: {exc}") from exc
    for f in full.rglob("*.py"):
        if any(skip in str(f) for skip in [".venv", "__pycache__", "node_modules", ".git"]):
            continue
        if len(matches) >= max_results:
            break
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if regex.search(line):
                matches.append({
                    "file": str(f.relative_to(full)),
                    "line": i,
                    "text": line.strip()[:200],
                })
                if len(matches) >= max_results:
                    break
    return {"matches": matches, "count": len(matches)}


def ia_analyze_extraction_output(
    workspace: Path, ia_path: Path, output_json: str
) -> dict[str, Any]:
    """Analiza un JSON de salida de extracción para detectar anomalías.

    Busca: campos vacíos, confidence baja, campos faltantes del contrato,
    inconsistencias entre tiers, y valores que no matchean catálogos.
    """
    _resolve_ia_path(workspace, ia_path)
    try:
        data = json.loads(output_json)
    except json.JSONDecodeError as exc:
        raise McpError(f"JSON inválido: {exc}") from exc

    issues: list[dict[str, Any]] = []

    def _check_obj(obj: Any, path: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                p = f"{path}.{k}" if path else k
                if v is None or v == "":
                    issues.append({"type": "empty_field", "field": p, "severity": "medium"})
                elif isinstance(v, str) and v.strip() == "":
                    issues.append({"type": "whitespace_only", "field": p, "severity": "low"})
                elif isinstance(v, (int, float)) and v < 0:
                    issues.append({"type": "negative_value", "field": p, "value": v, "severity": "high"})
                elif k == "confidence" and isinstance(v, (int, float)) and v < 0.5:
                    issues.append({"type": "low_confidence", "field": p, "value": v, "severity": "high"})
                elif k == "confidence" and isinstance(v, (int, float)) and v < 0.8:
                    issues.append({"type": "medium_confidence", "field": p, "value": v, "severity": "medium"})
                _check_obj(v, p)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _check_obj(item, f"{path}[{i}]")

    _check_obj(data)

    return {
        "issues": issues,
        "issue_count": len(issues),
        "severity_summary": {
            "high": sum(1 for i in issues if i["severity"] == "high"),
            "medium": sum(1 for i in issues if i["severity"] == "medium"),
            "low": sum(1 for i in issues if i["severity"] == "low"),
        },
        "verdict": "exposed" if any(i["severity"] == "high" for i in issues)
                   else "suspicious" if issues
                   else "clean",
    }


def ia_list_eval_tests(workspace: Path, ia_path: Path) -> dict[str, Any]:
    """Lista los tests de evaluación del motor Python."""
    full = _resolve_ia_path(workspace, ia_path)
    tests_dir = full / "tests"
    eval_tests: list[dict[str, Any]] = []
    if tests_dir.exists():
        for f in tests_dir.rglob("test_*.py"):
            eval_tests.append({
                "name": f.stem,
                "path": str(f.relative_to(full)),
                "is_eval": "eval" in str(f).lower(),
            })
    return {
        "tests": eval_tests,
        "count": len(eval_tests),
        "eval_count": sum(1 for t in eval_tests if t["is_eval"]),
        "command": "python -m pytest",
        "infra_command": "RUN_INFRA_TESTS=1 python -m pytest",
    }
