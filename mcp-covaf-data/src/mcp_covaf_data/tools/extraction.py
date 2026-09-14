"""Tools de análisis de extracciones COVAF.

Analiza resultados de extracción: cobertura, confianza, fuentes, estrategias,
campos faltantes, duplicados, contradictorios, malformados.
"""

from __future__ import annotations

import json
import re
from typing import Any

from mcp_shared.errors import McpError

# ---------------------------------------------------------------------------
# Field coverage
# ---------------------------------------------------------------------------

def analyze_field_coverage(
    extraction_result: str | dict[str, Any],
    expected_fields: list[str],
) -> dict[str, Any]:
    """Analiza cobertura de campos extraídos vs esperados.

    Args:
        extraction_result: JSON string o dict con resultados de extracción.
        expected_fields: Lista de campos esperados (puede ser plana o anidada con dots).
    """
    data = _parse_extraction_result(extraction_result)
    flat = _flatten_extraction(data)
    present: list[str] = []
    missing: list[str] = []
    empty: list[str] = []
    for field in expected_fields:
        if field in flat:
            val = flat[field]
            # Si es dict con value/valor, extraer el valor real
            if isinstance(val, dict):
                inner = val.get("value", val.get("valor"))
            else:
                inner = val
            if inner is None or inner == "" or inner == "null":
                empty.append(field)
            else:
                present.append(field)
        else:
            missing.append(field)
    coverage_pct = round(len(present) / len(expected_fields) * 100, 2) if expected_fields else 0
    return {
        "expected_count": len(expected_fields),
        "present_count": len(present),
        "missing_count": len(missing),
        "empty_count": len(empty),
        "coverage_pct": coverage_pct,
        "present": present,
        "missing": missing,
        "empty": empty,
        "verdict": _coverage_verdict(coverage_pct),
    }


def _coverage_verdict(pct: float) -> str:
    if pct >= 95:
        return "EXCELLENT"
    if pct >= 80:
        return "GOOD"
    if pct >= 60:
        return "FAIR"
    if pct >= 40:
        return "POOR"
    return "CRITICAL"


# ---------------------------------------------------------------------------
# Confidence analysis
# ---------------------------------------------------------------------------

def analyze_confidence(
    extraction_result: str | dict[str, Any],
    threshold: float = 0.8,
    low_threshold: float = 0.5,
) -> dict[str, Any]:
    """Analiza la distribución de confianza de los campos extraídos."""
    data = _parse_extraction_result(extraction_result)
    flat = _flatten_extraction(data)
    confidences: list[dict[str, Any]] = []
    for field, val in flat.items():
        if isinstance(val, dict) and "confidence" in val:
            conf = val["confidence"]
            confidences.append({
                "field": field,
                "confidence": conf,
                "value": val.get("value", val.get("valor", "")),
                "source": val.get("source", val.get("fuente", "")),
                "strategy": val.get("strategyUsed", val.get("estrategia", "")),
            })
    if not confidences:
        return {
            "field_count": 0,
            "avg_confidence": 0,
            "high_confidence_count": 0,
            "medium_confidence_count": 0,
            "low_confidence_count": 0,
            "low_confidence_fields": [],
            "verdict": "NO_DATA",
        }
    avg = sum(c["confidence"] for c in confidences) / len(confidences)
    high = [c for c in confidences if c["confidence"] >= threshold]
    medium = [c for c in confidences if low_threshold <= c["confidence"] < threshold]
    low = [c for c in confidences if c["confidence"] < low_threshold]
    return {
        "field_count": len(confidences),
        "avg_confidence": round(avg, 4),
        "high_confidence_count": len(high),
        "medium_confidence_count": len(medium),
        "low_confidence_count": len(low),
        "low_confidence_fields": low,
        "threshold": threshold,
        "low_threshold": low_threshold,
        "verdict": _confidence_verdict(avg, len(low)),
    }


def _confidence_verdict(avg: float, low_count: int) -> str:
    if avg >= 0.9 and low_count == 0:
        return "EXCELLENT"
    if avg >= 0.8:
        return "GOOD"
    if avg >= 0.6:
        return "FAIR"
    return "POOR"


# ---------------------------------------------------------------------------
# Source/strategy analysis
# ---------------------------------------------------------------------------

def analyze_sources_strategies(
    extraction_result: str | dict[str, Any],
) -> dict[str, Any]:
    """Analiza distribución de fuentes y estrategias usadas."""
    data = _parse_extraction_result(extraction_result)
    flat = _flatten_extraction(data)
    sources: dict[str, int] = {}
    strategies: dict[str, int] = {}
    source_strategy_matrix: dict[str, dict[str, int]] = {}
    for _field, val in flat.items():
        if isinstance(val, dict):
            src = val.get("source", val.get("fuente", "UNKNOWN"))
            strat = val.get("strategyUsed", val.get("estrategia", "UNKNOWN"))
            sources[src] = sources.get(src, 0) + 1
            strategies[strat] = strategies.get(strat, 0) + 1
            if src not in source_strategy_matrix:
                source_strategy_matrix[src] = {}
            source_strategy_matrix[src][strat] = source_strategy_matrix[src].get(strat, 0) + 1
    return {
        "sources": sources,
        "strategies": strategies,
        "source_strategy_matrix": source_strategy_matrix,
        "total_fields": sum(sources.values()),
        "dominant_source": max(sources, key=sources.get) if sources else None,
        "dominant_strategy": max(strategies, key=strategies.get) if strategies else None,
    }


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

def detect_anomalies(
    extraction_result: str | dict[str, Any],
    expected_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Detecta anomalías en resultados de extracción.

    Detecta:
    - Campos faltantes (vs expected_fields)
    - Campos vacíos
    - Campos duplicados
    - Campos contradictorios (mismo campo, distintos valores)
    - Confianza baja
    - Campos malformados (no diccionario con value/confidence)
    """
    data = _parse_extraction_result(extraction_result)
    flat = _flatten_extraction(data)
    anomalies: list[dict[str, Any]] = []
    # Faltantes
    if expected_fields:
        for field in expected_fields:
            if field not in flat:
                anomalies.append({"type": "MISSING", "field": field, "severity": "HIGH"})
    seen_values: dict[str, list[Any]] = {}
    for field, val in flat.items():
        # Extraer valor interno si es dict
        inner_val = val
        if isinstance(val, dict):
            inner_val = val.get("value", val.get("valor"))
        # Vacío
        if inner_val is None or inner_val == "" or inner_val == "null":
            anomalies.append({"type": "EMPTY", "field": field, "severity": "MEDIUM"})
            continue
        # Malformado
        if isinstance(val, dict):
            if "value" not in val and "valor" not in val:
                anomalies.append({"type": "MALFORMED", "field": field, "severity": "LOW", "reason": "Falta value/valor"})
            conf = val.get("confidence", val.get("confianza"))
            if conf is not None and conf < 0.5:
                anomalies.append({"type": "LOW_CONFIDENCE", "field": field, "severity": "MEDIUM", "confidence": conf})
            # Duplicados
            v = inner_val
            if field in seen_values:
                for prev in seen_values[field]:
                    if prev != v:
                        anomalies.append({
                            "type": "CONTRADICTORY",
                            "field": field,
                            "severity": "HIGH",
                            "values": [prev, v],
                        })
                seen_values[field].append(v)
            else:
                seen_values[field] = [v]
        else:
            # Valor plano sin metadata
            if field in seen_values:
                for prev in seen_values[field]:
                    if prev != val:
                        anomalies.append({
                            "type": "CONTRADICTORY",
                            "field": field,
                            "severity": "HIGH",
                            "values": [prev, val],
                        })
                seen_values[field].append(val)
            else:
                seen_values[field] = [val]
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    anomalies.sort(key=lambda a: severity_order.get(a["severity"], 3))
    counts: dict[str, int] = {}
    for a in anomalies:
        counts[a["type"]] = counts.get(a["type"], 0) + 1
    high_count = sum(1 for a in anomalies if a["severity"] == "HIGH")
    return {
        "anomaly_count": len(anomalies),
        "counts_by_type": counts,
        "anomalies": anomalies,
        "verdict": "PASS" if not anomalies else ("FAIL" if high_count > 0 else "WARN"),
    }


# ---------------------------------------------------------------------------
# Schema/template/contract validation
# ---------------------------------------------------------------------------

def validate_against_schema(
    extraction_result: str | dict[str, Any],
    schema: str | dict[str, Any],
) -> dict[str, Any]:
    """Valida resultados de extracción contra un schema/contract.

    Args:
        extraction_result: JSON string o dict con resultados.
        schema: JSON string o dict con schema esperado.
            Formato: {"fields": [{"name": "campo", "required": true, "min_confidence": 0.8}]}
    """
    data = _parse_extraction_result(extraction_result)
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except json.JSONDecodeError as exc:
            raise McpError(f"Schema JSON inválido: {exc}") from exc
    flat = _flatten_extraction(data)
    findings: list[dict[str, Any]] = []
    pass_count = 0
    for field_def in schema.get("fields", []):
        name = field_def["name"]
        required = field_def.get("required", False)
        min_conf = field_def.get("min_confidence", 0.0)
        if name not in flat:
            if required:
                findings.append({
                    "field": name,
                    "status": "FAIL",
                    "reason": "Campo requerido faltante",
                    "severity": "HIGH",
                })
            else:
                findings.append({
                    "field": name,
                    "status": "SKIP",
                    "reason": "Campo opcional faltante",
                    "severity": "LOW",
                })
            continue
        val = flat[name]
        if isinstance(val, dict):
            v = val.get("value", val.get("valor"))
            conf = val.get("confidence", val.get("confianza", 1.0))
            if v is None or v == "":
                findings.append({
                    "field": name,
                    "status": "FAIL",
                    "reason": "Valor vacío",
                    "severity": "HIGH" if required else "MEDIUM",
                })
                continue
            if conf < min_conf:
                findings.append({
                    "field": name,
                    "status": "WARN",
                    "reason": f"Confianza {conf} < {min_conf}",
                    "severity": "MEDIUM",
                    "confidence": conf,
                })
                continue
            findings.append({
                "field": name,
                "status": "PASS",
                "value_preview": _redact(str(v)[:50]),
                "confidence": conf,
            })
            pass_count += 1
        else:
            if val is None or val == "":
                findings.append({
                    "field": name,
                    "status": "FAIL",
                    "reason": "Valor vacío",
                    "severity": "HIGH" if required else "MEDIUM",
                })
            else:
                findings.append({
                    "field": name,
                    "status": "PASS",
                    "value_preview": _redact(str(val)[:50]),
                })
                pass_count += 1
    fail_count = sum(1 for f in findings if f["status"] == "FAIL")
    warn_count = sum(1 for f in findings if f["status"] == "WARN")
    if fail_count > 0:
        verdict = "FAIL"
    elif warn_count > 0:
        verdict = "WARN"
    else:
        verdict = "PASS"
    return {
        "total_fields": len(schema.get("fields", [])),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "findings": findings,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_extraction_result(data: str | dict[str, Any]) -> dict[str, Any]:
    """Convierte string JSON o dict a dict."""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError as exc:
            raise McpError(f"JSON inválido: {exc}") from exc
    if isinstance(data, dict):
        return data
    raise McpError(f"Tipo no soportado: {type(data)}")


def _flatten_extraction(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Aplana un resultado de extracción anidado.

    Soporta dos formas:
    - Lista de campos: [{"name": "x", "value": "y", "confidence": 0.9}, ...]
    - Dict anidado: {"seccion": {"campo": {"value": "y", "confidence": 0.9}}}
    """
    flat: dict[str, Any] = {}
    # Caso 1: lista de campos con name/value
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "name" in item:
                key = item["name"]
                flat[key] = item
        return flat
    if not isinstance(data, dict):
        return flat
    # Caso 2: dict con "fields" o "campos"
    if "fields" in data and isinstance(data["fields"], list):
        return _flatten_extraction(data["fields"])
    if "campos" in data and isinstance(data["campos"], list):
        return _flatten_extraction(data["campos"])
    # Caso 3: dict anidado
    for key, val in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(val, dict):
            # Si tiene value/valor, es un campo terminal
            if "value" in val or "valor" in val or "confidence" in val or "confianza" in val:
                flat[full_key] = val
            else:
                flat.update(_flatten_extraction(val, full_key))
        elif isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, dict) and "name" in item:
                    flat[item["name"]] = item
                elif isinstance(item, dict):
                    flat.update(_flatten_extraction(item, f"{full_key}[{i}]"))
        else:
            flat[full_key] = val
    return flat


def _redact(value: str) -> str:
    """Redacta valores sensibles para logs/reportes.

    Redacta patrones comunes: RFC, CURP, CLABE, números de cuenta.
    """
    if not isinstance(value, str):
        return str(value)
    # RFC: 4 letras + 6 dígitos + 3 alfanumérico
    value = re.sub(r"\b[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}\b", "[RFC_REDACTED]", value)
    # CURP: 18 caracteres
    value = re.sub(r"\b[A-Z&Ñ]{4}\d{6}[A-Z]{6}[A-Z0-9]{2}\b", "[CURP_REDACTED]", value)
    # CLABE: 18 dígitos
    value = re.sub(r"\b\d{18}\b", "[CLABE_REDACTED]", value)
    # Números de tarjeta: 16 dígitos
    value = re.sub(r"\b\d{16}\b", "[CARD_REDACTED]", value)
    return value
