"""Tools de reportes para datos extraídos COVAF.

Genera reportes estructurados para Cartas, Oficios PLD y Prospectos,
adecuados para el equipo COVAF, QA, operaciones y notificaciones.
"""

from __future__ import annotations

import json
from typing import Any

from mcp_shared.errors import McpError

from .extraction import (
    analyze_confidence,
    analyze_field_coverage,
    analyze_sources_strategies,
    detect_anomalies,
    validate_against_schema,
)

# ---------------------------------------------------------------------------
# Cartas de Confirmación — 15 campos canónicos
# ---------------------------------------------------------------------------

CARTAS_CANONICAL_FIELDS = [
    "institucion",
    "fechaCarta",
    "numeroCarta",
    "fondoInversion",
    "tipoOperacion",
    "montoOperacion",
    "moneda",
    "cliente",
    "rfcCliente",
    "intermediario",
    "tipoCliente",
    "perfilCliente",
    "plazo",
    "tasa",
    "comisiones",
]


def report_cartas(
    extraction_result: str | dict[str, Any],
    schema_json: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Genera un reporte completo para Cartas de Confirmación.

    Args:
        extraction_result: JSON string o dict con resultados de extracción.
        schema_json: Schema opcional para validación. Si no se provee, usa los 15 campos canónicos.
    """
    schema = schema_json if schema_json is not None else {
        "fields": [
            {"name": f, "required": True, "min_confidence": 0.8}
            for f in CARTAS_CANONICAL_FIELDS
        ]
    }
    coverage = analyze_field_coverage(extraction_result, CARTAS_CANONICAL_FIELDS)
    confidence = analyze_confidence(extraction_result)
    sources = analyze_sources_strategies(extraction_result)
    anomalies = detect_anomalies(extraction_result, CARTAS_CANONICAL_FIELDS)
    validation = validate_against_schema(extraction_result, schema)
    return {
        "domain": "cartas_confirmacion",
        "canonical_field_count": len(CARTAS_CANONICAL_FIELDS),
        "coverage": coverage,
        "confidence": confidence,
        "sources_strategies": sources,
        "anomalies": anomalies,
        "validation": validation,
        "verdict": _aggregate_verdict(
            coverage["verdict"],
            confidence["verdict"],
            anomalies["verdict"],
            validation["verdict"],
        ),
        "summary": _build_summary(
            "Cartas de Confirmación",
            coverage,
            confidence,
            anomalies,
            validation,
        ),
    }


# ---------------------------------------------------------------------------
# Oficios PLD
# ---------------------------------------------------------------------------

OFICIOS_PLD_FIELDS = [
    "numeroOficio",
    "folio",
    "expediente",
    "fechaPublicacion",
    "fechaRespuesta",
    "area",
    "autoridadEmisora",
    "solicitudSIARA",
    "referencias",
    "aseguramiento",
    "instrucciones",
    # Entidades/personas
    "entidades",
]


def report_oficios_pld(
    extraction_result: str | dict[str, Any],
    schema_json: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Genera un reporte completo para Oficios PLD.

    Args:
        extraction_result: JSON string o dict con resultados de extracción.
        schema_json: Schema opcional para validación.
    """
    schema = schema_json if schema_json is not None else {
        "fields": [
            {"name": f, "required": True, "min_confidence": 0.7}
            for f in OFICIOS_PLD_FIELDS
        ]
    }
    coverage = analyze_field_coverage(extraction_result, OFICIOS_PLD_FIELDS)
    confidence = analyze_confidence(extraction_result, threshold=0.7)
    sources = analyze_sources_strategies(extraction_result)
    anomalies = detect_anomalies(extraction_result, OFICIOS_PLD_FIELDS)
    validation = validate_against_schema(extraction_result, schema)
    return {
        "domain": "oficios_pld",
        "field_count": len(OFICIOS_PLD_FIELDS),
        "coverage": coverage,
        "confidence": confidence,
        "sources_strategies": sources,
        "anomalies": anomalies,
        "validation": validation,
        "verdict": _aggregate_verdict(
            coverage["verdict"],
            confidence["verdict"],
            anomalies["verdict"],
            validation["verdict"],
        ),
        "summary": _build_summary(
            "Oficios PLD",
            coverage,
            confidence,
            anomalies,
            validation,
        ),
    }


# ---------------------------------------------------------------------------
# Prospectos CNBV — 100 campos
# ---------------------------------------------------------------------------

PROSPECTOS_CONTRACT_SECTIONS = [
    "portada",
    "objetivos_horizonte",
    "politicas_inversion",
    "regimen_inversion",
    "riesgos",
    "operacion_fondo",
    "prestadores_servicios",
    "costos_comisiones",
    "organizacion_capital",
    "secciones_finales",
    "anexo_cartera",
]


def report_prospectos(
    extraction_result: str | dict[str, Any],
    schema_json: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Genera un reporte para Prospectos CNBV.

    Args:
        extraction_result: JSON string o dict con resultados de extracción.
        schema_json: Schema opcional con las 100 secciones del contract.
    """
    if schema_json is None:
        # Schema mínimo basado en secciones del contract
        schema = {
            "fields": [
                {"name": s, "required": True, "min_confidence": 0.7}
                for s in PROSPECTOS_CONTRACT_SECTIONS
            ]
        }
    elif isinstance(schema_json, str):
        try:
            schema = json.loads(schema_json)
        except json.JSONDecodeError as exc:
            raise McpError(f"Schema JSON inválido: {exc}") from exc
    else:
        schema = schema_json
    expected = [f["name"] for f in schema.get("fields", [])]
    coverage = analyze_field_coverage(extraction_result, expected)
    confidence = analyze_confidence(extraction_result, threshold=0.7)
    sources = analyze_sources_strategies(extraction_result)
    anomalies = detect_anomalies(extraction_result, expected)
    validation = validate_against_schema(extraction_result, schema)
    return {
        "domain": "prospectos_cnbv",
        "section_count": len(expected),
        "sections_expected": expected,
        "coverage": coverage,
        "confidence": confidence,
        "sources_strategies": sources,
        "anomalies": anomalies,
        "validation": validation,
        "verdict": _aggregate_verdict(
            coverage["verdict"],
            confidence["verdict"],
            anomalies["verdict"],
            validation["verdict"],
        ),
        "summary": _build_summary(
            "Prospectos CNBV",
            coverage,
            confidence,
            anomalies,
            validation,
        ),
    }


# ---------------------------------------------------------------------------
# Reporte genérico
# ---------------------------------------------------------------------------

def report_generic(
    extraction_result: str | dict[str, Any],
    expected_fields: list[str] | None = None,
    schema_json: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Genera un reporte genérico para cualquier resultado de extracción.

    Args:
        extraction_result: JSON string o dict con resultados de extracción.
        expected_fields: Lista de campos esperados (opcional).
        schema_json: Schema opcional para validación.
    """
    fields = expected_fields or []
    coverage = (
        analyze_field_coverage(extraction_result, fields)
        if fields
        else {"verdict": "NO_DATA", "coverage_pct": 0, "present": [], "missing": [], "empty": []}
    )
    confidence = analyze_confidence(extraction_result)
    sources = analyze_sources_strategies(extraction_result)
    anomalies = detect_anomalies(extraction_result, fields or None)
    validation = (
        validate_against_schema(extraction_result, schema_json)
        if schema_json is not None
        else {"verdict": "SKIP", "findings": [], "pass_count": 0, "fail_count": 0, "warn_count": 0}
    )
    return {
        "domain": "generic",
        "coverage": coverage,
        "confidence": confidence,
        "sources_strategies": sources,
        "anomalies": anomalies,
        "validation": validation,
        "verdict": _aggregate_verdict(
            coverage.get("verdict", "NO_DATA"),
            confidence["verdict"],
            anomalies["verdict"],
            validation.get("verdict", "SKIP"),
        ),
        "summary": _build_summary(
            "Extracción genérica",
            coverage,
            confidence,
            anomalies,
            validation,
        ),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _aggregate_verdict(*verdicts: str) -> str:
    """Agrega múltiples veredictos en uno solo (el peor gana)."""
    severity = {"CRITICAL": 5, "FAIL": 4, "POOR": 3, "WARN": 2, "FAIR": 2, "GOOD": 1, "PASS": 0, "EXCELLENT": 0, "SKIP": 0, "NO_DATA": 0}
    worst = max(verdicts, key=lambda v: severity.get(v, 3))
    return worst


def _build_summary(
    domain_name: str,
    coverage: dict[str, Any],
    confidence: dict[str, Any],
    anomalies: dict[str, Any],
    validation: dict[str, Any],
) -> str:
    """Construye un resumen legible para humanos."""
    parts: list[str] = [f"Reporte de extracción: {domain_name}"]
    if "coverage_pct" in coverage:
        parts.append(f"  Cobertura: {coverage['coverage_pct']}% ({coverage.get('present_count', 0)}/{coverage.get('expected_count', 0)} campos)")
    if "avg_confidence" in confidence:
        parts.append(f"  Confianza promedio: {confidence['avg_confidence']}")
        parts.append(f"  Campos de baja confianza: {confidence.get('low_confidence_count', 0)}")
    if "anomaly_count" in anomalies:
        parts.append(f"  Anomalías: {anomalies['anomaly_count']}")
    if "fail_count" in validation:
        parts.append(f"  Validación: {validation.get('pass_count', 0)} OK, {validation.get('fail_count', 0)} FAIL, {validation.get('warn_count', 0)} WARN")
    parts.append(f"  Veredicto agregado: {_aggregate_verdict(coverage.get('verdict', 'NO_DATA'), confidence.get('verdict', 'NO_DATA'), anomalies.get('verdict', 'NO_DATA'), validation.get('verdict', 'SKIP'))}")
    return "\n".join(parts)
