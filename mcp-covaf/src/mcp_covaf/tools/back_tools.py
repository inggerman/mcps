"""Tools para el motor Java COVAF (CovafDataRefineryBack).

Cobertura: estrategias de extracción, templates, quality gates, endpoints REST,
pipeline de Oficios PLD y Cartas de Confirmación.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mcp_shared.errors import McpError

# Estrategias de extracción soportadas por el motor Java (observado en código).
EXTRACTION_STRATEGIES = [
    "REGEX",
    "KEY_WORD",
    "ADVANCED",
    "TABLE",
    "FORMS",
    "REGEX_ADVANCED",
    "TABLE_ADVANCED",
    "FORM_ADVANCED",
    "CALCULATED",
    "EXTERNAL_CATALOG",
]

# Endpoints REST del motor Java (observado en OrquestadorController y adapters).
ENDPOINT_MAP = {
    "orquestador_process": "POST /orquestador/process",
    "orquestador_status": "GET /orquestador/status/{uuid}",
    "orquestador_execute": "POST /orquestador/execute",
    "orquestador_execute_all": "POST /orquestador/execute-all",
    "orquestador_reprocess": "POST /orquestador/reprocess",
    "cartas_search": "POST /api/v1/search/process",
    "cartas_results_excel": "GET /api/v1/results/data-excel",
    "oficios_extract": "POST /api/v1/oficios/extract",
    "oficios_query": "GET /api/v1/oficios/results",
    "health": "GET /api/v1/health",
    "live": "GET /api/v1/live",
    "ready": "GET /api/v1/ready",
    "templates_reload": "POST /api/templates/reload",
}

# Quality gates observados en el motor Java.
QUALITY_GATES = [
    "ExtractionQualityEvaluator",
    "QualityGateOrchestrator",
    "CrossSourceConsistencyValidator",
    "OcrHealthEvaluator",
    "CorrectionGuard",
    "FieldValueValidator",
    "CandidateRanker",
]


def _resolve_back_path(workspace: Path, relative: Path) -> Path:
    full = workspace / relative
    if not full.exists():
        raise McpError(f"Motor Java no encontrado en {full}")
    return full


def back_list_extraction_strategies(workspace: Path, back_path: Path) -> dict[str, Any]:
    """Lista las estrategias de extracción soportadas por el motor Java."""
    _resolve_back_path(workspace, back_path)
    return {
        "strategies": EXTRACTION_STRATEGIES,
        "count": len(EXTRACTION_STRATEGIES),
        "description": "Estrategias de búsqueda multi-estrategia con Apache Lucene",
    }


def back_list_templates(workspace: Path, back_path: Path) -> dict[str, Any]:
    """Lista los templates de extracción disponibles (Cartas, Oficios PLD)."""
    full = _resolve_back_path(workspace, back_path)
    templates = []
    # Buscar archivos de template en resources
    resources = full / "src/main/resources"
    if resources.exists():
        for t in resources.rglob("*.json"):
            if "template" in t.name.lower():
                templates.append(str(t.relative_to(full)))
    return {
        "templates": templates,
        "count": len(templates),
        "domains": ["cartas_confirmacion", "oficios_pld"],
    }


def back_list_quality_gates(workspace: Path, back_path: Path) -> dict[str, Any]:
    """Lista los quality gates del motor Java."""
    _resolve_back_path(workspace, back_path)
    return {
        "quality_gates": QUALITY_GATES,
        "count": len(QUALITY_GATES),
        "description": "Validadores de calidad de extracción",
    }


def back_search_code(
    workspace: Path, back_path: Path, pattern: str, max_results: int = 20
) -> dict[str, Any]:
    """Busca un patrón (regex) en el código Java del motor."""
    full = _resolve_back_path(workspace, back_path)
    matches: list[dict[str, Any]] = []
    src = full / "src/main/java"
    if not src.exists():
        return {"matches": [], "count": 0, "error": "src/main/java no existe"}
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise McpError(f"Regex inválido: {exc}") from exc
    for f in src.rglob("*.java"):
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


def back_get_endpoint_map(workspace: Path, back_path: Path) -> dict[str, Any]:
    """Retorna el mapa de endpoints REST del motor Java."""
    _resolve_back_path(workspace, back_path)
    return {
        "endpoints": ENDPOINT_MAP,
        "count": len(ENDPOINT_MAP),
        "base_controllers": [
            "OrquestadorController",
            "SearchController",
            "OficiosExtractController",
            "ResultsController",
            "HealthController",
            "TemplateReloadController",
        ],
    }


def back_analyze_oficios_pipeline(workspace: Path, back_path: Path) -> dict[str, Any]:
    """Analiza el pipeline de extracción de Oficios PLD del motor Java."""
    full = _resolve_back_path(workspace, back_path)
    components = [
        "OficiosExtractService",
        "OficiosPldXmlExtractor",
        "OficiosPldJsonPdfExtractor",
        "OficiosPostProcessor",
        "OficiosDerivedFieldCalculator",
        "OficiosTipoRequerimientoClassifier",
        "OficiosEntityRagExtractor",
        "OficiosEntityWindowExtractor",
        "OficiosEntityRules",
        "OficiosEntityTableParser",
        "OficiosLlmFieldRules",
        "PldPolicyValidator",
        "PldEntityExtractor",
        "PldPatternCatalog",
        "PldPatternMatcher",
    ]
    # Verificar cuáles existen en el código
    src = full / "src/main/java"
    found: list[str] = []
    if src.exists():
        all_text = ""
        for f in src.rglob("*.java"):
            try:
                all_text += f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
        for c in components:
            if f"class {c}" in all_text or f"interface {c}" in all_text:
                found.append(c)
    return {
        "pipeline_components": components,
        "components_found": found,
        "components_missing": [c for c in components if c not in found],
        "domain": "PLD (Prevención de Lavado de Dinero)",
        "endpoint": "POST /api/v1/oficios/extract",
    }


def back_analyze_cartas_pipeline(workspace: Path, back_path: Path) -> dict[str, Any]:
    """Analiza el pipeline de extracción de Cartas de Confirmación del motor Java."""
    full = _resolve_back_path(workspace, back_path)
    components = [
        "ProcessDocumentService",
        "SearchController",
        "ResultsController",
        "ExcelExportService",
        "S3FileUploadService",
        "FieldProcessorService",
        "BypassExtractionService",
        "CandidateRanker",
        "ExpressionEvaluator",
        "ExternalCatalogProcessor",
        "FieldValueValidator",
        "TableModelBuilder",
        "TextNormalizerService",
        "SimilarityValidatorService",
        "XmlExtractorService",
        "OpenNlpService",
        "SpanishNumberParser",
        "TotalsRowDetector",
        "ValidationService",
    ]
    src = full / "src/main/java"
    found: list[str] = []
    if src.exists():
        all_text = ""
        for f in src.rglob("*.java"):
            try:
                all_text += f.read_text(encoding='utf-8', errors='ignore')
            except OSError:
                continue
        for c in components:
            if f"class {c}" in all_text or f"interface {c}" in all_text:
                found.append(c)
    return {
        "pipeline_components": components,
        "components_found": found,
        "components_missing": [c for c in components if c not in found],
        "domain": "Cartas de Confirmación bursátiles",
        "endpoint": "POST /api/v1/search/process",
        "campos_canonicos": [
            "fondo", "tipoValor", "instrumento", "serie", "tipoMovimiento",
            "titulos", "monto", "fechaOperacion", "institucion", "contrato",
            "firma", "observaciones",
        ],
    }
