"""
Servidor FastMCP para mcp-covaf-data.

Tools para leer y analizar formatos de datos COVAF:
PDF, Excel, Word, XML, JSON, JSON-PDF, JSON-Word, XML-Short,
y análisis de extracciones (cobertura, confianza, fuentes, anomalías, validación).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import MCPError as SdkMcpError
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_covaf_data import __version__
from mcp_covaf_data.config import settings
from mcp_covaf_data.tools import (
    analyze_confidence,
    analyze_field_coverage,
    analyze_sources_strategies,
    detect_anomalies,
    list_extraction_sources,
    parse_s3_path,
    read_excel,
    read_json,
    read_jsonpdf,
    read_jsonword,
    read_pdf,
    read_word,
    read_xml,
    read_xmlshort,
    report_cartas,
    report_generic,
    report_oficios_pld,
    report_prospectos,
    validate_against_schema,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-covaf-data",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-covaf-data")
    logger.info(
        "mcp-covaf-data iniciando",
        version=__version__,
        workspace=str(settings.workspace_path),
    )
    yield
    logger.info("mcp-covaf-data detenido")


# ---------------------------------------------------------------------------
# FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-covaf-data",
    instructions=(
        "Servidor MCP para lectura y análisis de formatos de datos COVAF. "
        "Lee PDF, Excel, Word, XML, JSON, JSON-PDF, JSON-Word, XML-Short. "
        "Analiza extracciones: cobertura, confianza, fuentes, estrategias, anomalías. "
        "Genera reportes para Cartas de Confirmación, Oficios PLD y Prospectos CNBV."
    ),
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(code=-32000, message=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=getattr(fn, "__name__", "?"), error=str(exc))
        raise SdkMcpError(code=-32603, message=f"Error interno: {exc}") from exc


# ---------------------------------------------------------------------------
# Tools — Lectura de formatos
# ---------------------------------------------------------------------------

@mcp.tool(
    name="read_pdf",
    description="Lee un PDF y extrae texto plano por página. Usa pdfplumber o pymupdf si están disponibles.",
)
def tool_read_pdf(file_path: str, max_pages: int = 50) -> dict[str, Any]:
    return _handle(read_pdf, file_path, max_pages)


@mcp.tool(
    name="read_excel",
    description="Lee un archivo Excel (.xlsx) y devuelve filas como diccionarios. Requiere openpyxl.",
)
def tool_read_excel(file_path: str, sheet_name: str | None = None, max_rows: int = 100) -> dict[str, Any]:
    return _handle(read_excel, file_path, sheet_name, max_rows)


@mcp.tool(
    name="read_word",
    description="Lee un documento Word (.docx) y extrae texto, tablas y propiedades (core.xml, custom.xml).",
)
def tool_read_word(file_path: str) -> dict[str, Any]:
    return _handle(read_word, file_path)


@mcp.tool(
    name="read_xml",
    description="Lee un archivo XML y lo convierte a diccionario recursivo (maneja namespaces y atributos).",
)
def tool_read_xml(file_path: str) -> dict[str, Any]:
    return _handle(read_xml, file_path)


@mcp.tool(
    name="read_json",
    description="Lee un archivo JSON genérico y devuelve su contenido.",
)
def tool_read_json(file_path: str) -> dict[str, Any]:
    return _handle(read_json, file_path)


@mcp.tool(
    name="read_jsonpdf",
    description=(
        "Lee un JSON-PDF (salida de OCR) y lo normaliza al formato canónico COVAF. "
        "Soporta 4 variantes: array de documentos, objeto por institución, documento simple, bloques Textract crudos."
    ),
)
def tool_read_jsonpdf(file_path: str) -> dict[str, Any]:
    return _handle(read_jsonpdf, file_path)


@mcp.tool(
    name="read_jsonword",
    description="Lee un JSON-Word (representación JSON de un Word). Usa el mismo parser que JSON-PDF.",
)
def tool_read_jsonword(file_path: str) -> dict[str, Any]:
    return _handle(read_jsonword, file_path)


@mcp.tool(
    name="read_xmlshort",
    description=(
        "Lee un XML-Short de SITIAA y lo convierte a un Map<String,String>. "
        "Soporta múltiples <RequerimientoDescargado> y selección por folio_id."
    ),
)
def tool_read_xmlshort(file_path: str, folio_id: str | None = None) -> dict[str, Any]:
    return _handle(read_xmlshort, file_path, folio_id)


@mcp.tool(
    name="parse_s3_path",
    description="Parsea una URI S3 (s3://bucket/path) en sus componentes y detecta el tipo de archivo COVAF.",
)
def tool_parse_s3_path(s3_uri: str) -> dict[str, Any]:
    return _handle(parse_s3_path, s3_uri)


@mcp.tool(
    name="list_extraction_sources",
    description=(
        "Lista las fuentes de extracción disponibles en un folio de request (OficiosFolioDto). "
        "Determina el config type (XML_FULL, XML_SHORT_JSON_WORD, XML_SHORT_WORD)."
    ),
)
def tool_list_extraction_sources(folio_json: str) -> dict[str, Any]:
    return _handle(list_extraction_sources, folio_json)


# ---------------------------------------------------------------------------
# Tools — Análisis de extracciones
# ---------------------------------------------------------------------------

@mcp.tool(
    name="analyze_field_coverage",
    description="Analiza la cobertura de campos extraídos vs esperados. Retorna % cobertura, presentes, faltantes y vacíos.",
)
def tool_analyze_field_coverage(
    extraction_result: str,
    expected_fields: list[str],
) -> dict[str, Any]:
    return _handle(analyze_field_coverage, extraction_result, expected_fields)


@mcp.tool(
    name="analyze_confidence",
    description="Analiza la distribución de confianza de los campos extraídos. Clasifica en alta/media/baja.",
)
def tool_analyze_confidence(
    extraction_result: str,
    threshold: float = 0.8,
    low_threshold: float = 0.5,
) -> dict[str, Any]:
    return _handle(analyze_confidence, extraction_result, threshold, low_threshold)


@mcp.tool(
    name="analyze_sources_strategies",
    description="Analiza la distribución de fuentes (XML, JSON_PDF, WORD, etc.) y estrategias (REGEX, KEY_WORD, TABLE, etc.) usadas.",
)
def tool_analyze_sources_strategies(extraction_result: str) -> dict[str, Any]:
    return _handle(analyze_sources_strategies, extraction_result)


@mcp.tool(
    name="detect_anomalies",
    description=(
        "Detecta anomalías en resultados de extracción: campos faltantes, vacíos, duplicados, "
        "contradictorios, baja confianza y malformados."
    ),
)
def tool_detect_anomalies(
    extraction_result: str,
    expected_fields: list[str] | None = None,
) -> dict[str, Any]:
    return _handle(detect_anomalies, extraction_result, expected_fields)


@mcp.tool(
    name="validate_against_schema",
    description=(
        "Valida resultados de extracción contra un schema/contract. "
        "Formato schema: {\"fields\": [{\"name\": \"campo\", \"required\": true, \"min_confidence\": 0.8}]}"
    ),
)
def tool_validate_against_schema(
    extraction_result: str,
    schema: str,
) -> dict[str, Any]:
    return _handle(validate_against_schema, extraction_result, schema)


# ---------------------------------------------------------------------------
# Tools — Reportes COVAF
# ---------------------------------------------------------------------------

@mcp.tool(
    name="report_cartas",
    description="Genera un reporte completo para Cartas de Confirmación (15 campos canónicos).",
)
def tool_report_cartas(
    extraction_result: str,
    schema: str | None = None,
) -> dict[str, Any]:
    return _handle(report_cartas, extraction_result, schema)


@mcp.tool(
    name="report_oficios_pld",
    description="Genera un reporte completo para Oficios PLD (metadata, autoridades, entidades, instrucciones).",
)
def tool_report_oficios_pld(
    extraction_result: str,
    schema: str | None = None,
) -> dict[str, Any]:
    return _handle(report_oficios_pld, extraction_result, schema)


@mcp.tool(
    name="report_prospectos",
    description="Genera un reporte para Prospectos CNBV (100 campos del contract).",
)
def tool_report_prospectos(
    extraction_result: str,
    schema: str | None = None,
) -> dict[str, Any]:
    return _handle(report_prospectos, extraction_result, schema)


@mcp.tool(
    name="report_generic",
    description="Genera un reporte genérico para cualquier resultado de extracción COVAF.",
)
def tool_report_generic(
    extraction_result: str,
    expected_fields: list[str] | None = None,
    schema: str | None = None,
) -> dict[str, Any]:
    return _handle(report_generic, extraction_result, expected_fields, schema)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
