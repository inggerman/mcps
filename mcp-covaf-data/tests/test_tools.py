"""Tests para mcp-covaf-data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from mcp_covaf_data.tools.extraction import (
    analyze_confidence,
    analyze_field_coverage,
    analyze_sources_strategies,
    detect_anomalies,
    validate_against_schema,
)
from mcp_covaf_data.tools.readers import (
    _normalize_jsonpdf,
    _textract_blocks_to_doc,
    list_extraction_sources,
    parse_s3_path,
    read_json,
    read_jsonpdf,
    read_jsonword,
    read_xml,
    read_xmlshort,
)
from mcp_covaf_data.tools.reports import (
    CARTAS_CANONICAL_FIELDS,
    OFICIOS_PLD_FIELDS,
    report_cartas,
    report_generic,
    report_oficios_pld,
    report_prospectos,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_json_file(tmp_path: Path) -> Path:
    """Crea un archivo JSON temporal."""
    p = tmp_path / "test.json"
    p.write_text(json.dumps({"key": "value", "nested": {"a": 1}}), encoding="utf-8")
    return p


@pytest.fixture
def tmp_xml_file(tmp_path: Path) -> Path:
    """Crea un archivo XML temporal."""
    p = tmp_path / "test.xml"
    p.write_text(
        '<?xml version="1.0"?>\n<root><name>test</name><value>42</value></root>',
        encoding="utf-8",
    )
    return p


@pytest.fixture
def tmp_xmlshort_file(tmp_path: Path) -> Path:
    """Crea un XML-Short de SITIAA temporal."""
    p = tmp_path / "xmlshort.xml"
    p.write_text(
        '<?xml version="1.0"?>\n<Requerimientos>'
        '<RequerimientoDescargado>'
        '<IdFolio>21260039</IdFolio>'
        '<Expediente>EXP-001</Expediente>'
        '<Autoridad>UIF</Autoridad>'
        '</RequerimientoDescargado>'
        '<RequerimientoDescargado>'
        '<IdFolio>21260040</IdFolio>'
        '<Expediente>EXP-002</Expediente>'
        '<Autoridad>UIF</Autoridad>'
        '</RequerimientoDescargado>'
        '</Requerimientos>',
        encoding="utf-8",
    )
    return p


@pytest.fixture
def jsonpdf_array_format() -> dict[str, Any]:
    """JSON-PDF en formato 1: array de documentos."""
    return [
        {
            "documento": {
                "contenido": "Texto de la carta",
                "tablas": [{"id": "t1", "confianza": 0.95, "filas": []}],
                "formularios": [{"clave": "f1", "valor": "v1", "confianza": 0.9}],
            },
            "uuidDocumento": "uuid-1",
            "institution": "BANCO_1",
            "formato": "CARTA",
        }
    ]


@pytest.fixture
def jsonpdf_institution_format() -> dict[str, Any]:
    """JSON-PDF en formato 2: objeto por institución."""
    return {
        "BANCO_1": {
            "contenido": "Texto banco 1",
            "tablas": [],
            "formularios": [],
        },
        "BANCO_2": {
            "contenido": "Texto banco 2",
            "tablas": [],
            "formularios": [],
        },
    }


@pytest.fixture
def jsonpdf_single_doc_format() -> dict[str, Any]:
    """JSON-PDF en formato 3: documento simple."""
    return {
        "documento": {
            "contenido": "Texto simple",
            "tablas": [],
            "formularios": [],
        },
        "uuidDocumento": "uuid-simple",
    }


@pytest.fixture
def jsonpdf_textract_raw() -> list[dict[str, Any]]:
    """JSON-PDF en formato 0: bloques Textract crudos."""
    return [
        {"BlockType": "LINE", "Text": "Línea 1"},
        {"BlockType": "LINE", "Text": "Línea 2"},
        {"BlockType": "WORD", "Text": "word"},
    ]


@pytest.fixture
def extraction_result_full() -> dict[str, Any]:
    """Resultado de extracción completo con metadata."""
    return {
        "fields": [
            {"name": "institucion", "value": "BANCO_1", "confidence": 0.95, "source": "JSON_PDF", "strategyUsed": "REGEX"},
            {"name": "fechaCarta", "value": "2026-01-15", "confidence": 0.92, "source": "JSON_PDF", "strategyUsed": "KEY_WORD"},
            {"name": "numeroCarta", "value": "CARTA-001", "confidence": 0.88, "source": "JSON_PDF", "strategyUsed": "FORMS"},
            {"name": "montoOperacion", "value": "1000000", "confidence": 0.45, "source": "JSON_PDF", "strategyUsed": "TABLE"},
            {"name": "rfcCliente", "value": "", "confidence": 0.0, "source": "JSON_PDF", "strategyUsed": "REGEX"},
        ]
    }


@pytest.fixture
def extraction_result_missing() -> dict[str, Any]:
    """Resultado de extracción con campos faltantes."""
    return {
        "fields": [
            {"name": "institucion", "value": "BANCO_1", "confidence": 0.95, "source": "JSON_PDF"},
            {"name": "fechaCarta", "value": "2026-01-15", "confidence": 0.92, "source": "JSON_PDF"},
        ]
    }


# ---------------------------------------------------------------------------
# Tests — Readers
# ---------------------------------------------------------------------------

class TestReadJson:
    def test_read_json_valid(self, tmp_json_file: Path) -> None:
        result = read_json(str(tmp_json_file))
        assert result["data"]["key"] == "value"
        assert result["data"]["nested"]["a"] == 1

    def test_read_json_not_found(self) -> None:
        from mcp_shared.errors import McpError
        with pytest.raises(McpError):
            read_json("/nonexistent/file.json")


class TestReadXml:
    def test_read_xml_valid(self, tmp_xml_file: Path) -> None:
        result = read_xml(str(tmp_xml_file))
        assert result["root_tag"] == "root"
        assert result["data"]["name"] == "test"
        assert result["data"]["value"] == "42"

    def test_read_xml_not_found(self) -> None:
        from mcp_shared.errors import McpError
        with pytest.raises(McpError):
            read_xml("/nonexistent/file.xml")


class TestReadXmlShort:
    def test_read_xmlshort_multiple_records(self, tmp_xmlshort_file: Path) -> None:
        result = read_xmlshort(str(tmp_xmlshort_file))
        assert result["record_count"] == 2
        assert result["records"][0]["IdFolio"] == "21260039"
        assert result["records"][1]["IdFolio"] == "21260040"

    def test_read_xmlshort_select_folio(self, tmp_xmlshort_file: Path) -> None:
        result = read_xmlshort(str(tmp_xmlshort_file), folio_id="21260040")
        assert result["selected_count"] == 1
        assert result["selected"]["IdFolio"] == "21260040"
        assert result["selected"]["Expediente"] == "EXP-002"

    def test_read_xmlshort_folio_not_found(self, tmp_xmlshort_file: Path) -> None:
        result = read_xmlshort(str(tmp_xmlshort_file), folio_id="99999999")
        assert result["selected_count"] == 0
        assert result["selected"] == {}


class TestJsonPdfNormalization:
    def test_normalize_array_format(self, jsonpdf_array_format: list[dict[str, Any]]) -> None:
        result = _normalize_jsonpdf(jsonpdf_array_format, "test.json")
        assert result["format_detected"] == "array_documents"
        assert result["document_count"] == 1
        doc = result["documents"][0]
        assert doc["documento"]["contenido"] == "Texto de la carta"
        assert doc["metadata"]["institution"] == "BANCO_1"
        assert doc["metadata"]["uuidDocumento"] == "uuid-1"

    def test_normalize_institution_format(self, jsonpdf_institution_format: dict[str, Any]) -> None:
        result = _normalize_jsonpdf(jsonpdf_institution_format, "test.json")
        assert result["format_detected"] == "by_institution"
        assert result["document_count"] == 2
        institutions = [d["metadata"].get("institution") for d in result["documents"]]
        assert "BANCO_1" in institutions
        assert "BANCO_2" in institutions

    def test_normalize_single_doc_format(self, jsonpdf_single_doc_format: dict[str, Any]) -> None:
        result = _normalize_jsonpdf(jsonpdf_single_doc_format, "test.json")
        assert result["format_detected"] == "single_document"
        assert result["document_count"] == 1
        assert result["documents"][0]["documento"]["contenido"] == "Texto simple"

    def test_normalize_textract_raw(self, jsonpdf_textract_raw: list[dict[str, Any]]) -> None:
        result = _normalize_jsonpdf(jsonpdf_textract_raw, "test.json")
        assert result["format_detected"] == "textract_raw"
        assert result["document_count"] == 1
        assert "Línea 1" in result["documents"][0]["documento"]["contenido"]
        assert "Línea 2" in result["documents"][0]["documento"]["contenido"]

    def test_textract_blocks_to_doc(self) -> None:
        blocks = [
            {"BlockType": "LINE", "Text": "Hello"},
            {"BlockType": "LINE", "Text": "World"},
            {"BlockType": "WORD", "Text": "ignored"},
        ]
        docs = _textract_blocks_to_doc(blocks)
        assert len(docs) == 1
        assert "Hello" in docs[0]["documento"]["contenido"]
        assert "World" in docs[0]["documento"]["contenido"]


class TestReadJsonPdf:
    def test_read_jsonpdf_file(
        self,
        tmp_path: Path,
        jsonpdf_array_format: list[dict[str, Any]],
    ) -> None:
        p = tmp_path / "jsonpdf.json"
        p.write_text(json.dumps(jsonpdf_array_format), encoding="utf-8")
        result = read_jsonpdf(str(p))
        assert result["document_count"] == 1
        assert result["documents"][0]["metadata"]["institution"] == "BANCO_1"


class TestReadJsonWord:
    def test_read_jsonword_uses_same_parser(
        self,
        tmp_path: Path,
        jsonpdf_single_doc_format: dict[str, Any],
    ) -> None:
        p = tmp_path / "jsonword.json"
        p.write_text(json.dumps(jsonpdf_single_doc_format), encoding="utf-8")
        result = read_jsonword(str(p))
        assert result["format_source"] == "jsonword"
        assert result["document_count"] == 1


class TestParseS3Path:
    def test_parse_s3_pdf(self) -> None:
        result = parse_s3_path("s3://bucket/path/document.pdf")
        assert result["bucket"] == "bucket"
        assert result["key"] == "path/document.pdf"
        assert result["file_type"] == "pdf"

    def test_parse_s3_excel(self) -> None:
        result = parse_s3_path("s3://bucket/report.xlsx")
        assert result["file_type"] == "excel"

    def test_parse_s3_word(self) -> None:
        result = parse_s3_path("s3://bucket/document.docx")
        assert result["file_type"] == "word"

    def test_parse_s3_xml_short(self) -> None:
        result = parse_s3_path("s3://bucket/document_short.xml")
        assert result["file_type"] == "xml_short"

    def test_parse_s3_xml_full(self) -> None:
        result = parse_s3_path("s3://bucket/sitiaa_full.xml")
        assert result["file_type"] == "xml_full"

    def test_parse_s3_json_pdf(self) -> None:
        result = parse_s3_path("s3://bucket/jsonpdf_output.json")
        assert result["file_type"] == "json_pdf"

    def test_parse_s3_json_word(self) -> None:
        result = parse_s3_path("s3://bucket/jsonword_v5.json")
        assert result["file_type"] == "json_word"

    def test_parse_s3_invalid(self) -> None:
        from mcp_shared.errors import McpError
        with pytest.raises(McpError):
            parse_s3_path("not-an-s3-uri")


class TestListExtractionSources:
    def test_list_sources_xml_full(self) -> None:
        folio = json.dumps({
            "folioId": "12345",
            "tengoXml": "true",
            "xml": "s3://bucket/full.xml",
            "word": "s3://bucket/doc.docx",
        })
        result = list_extraction_sources(folio)
        assert result["config_type"] == "XML_FULL"
        assert result["tengo_xml"] is True
        assert result["source_count"] == 2

    def test_list_sources_xml_short_json_word(self) -> None:
        folio = json.dumps({
            "folioId": "12345",
            "tengoXml": "false",
            "word": "s3://bucket/doc.docx",
            "jsonWord": "s3://bucket/jw.json",
            "xmlShort": "s3://bucket/short.xml",
        })
        result = list_extraction_sources(folio)
        assert result["config_type"] == "XML_SHORT_JSON_WORD"
        assert result["source_count"] == 3

    def test_list_sources_xml_short_word(self) -> None:
        folio = json.dumps({
            "folioId": "12345",
            "tengoXml": "false",
            "word": "s3://bucket/doc.docx",
            "xmlShort": "s3://bucket/short.xml",
        })
        result = list_extraction_sources(folio)
        assert result["config_type"] == "XML_SHORT_WORD"
        assert result["source_count"] == 2


# ---------------------------------------------------------------------------
# Tests — Extraction analysis
# ---------------------------------------------------------------------------

class TestAnalyzeFieldCoverage:
    def test_full_coverage(self, extraction_result_full: dict[str, Any]) -> None:
        expected = ["institucion", "fechaCarta", "numeroCarta"]
        result = analyze_field_coverage(extraction_result_full, expected)
        assert result["coverage_pct"] == 100.0
        assert result["verdict"] == "EXCELLENT"
        assert len(result["missing"]) == 0

    def test_partial_coverage(self, extraction_result_missing: dict[str, Any]) -> None:
        expected = ["institucion", "fechaCarta", "numeroCarta", "montoOperacion"]
        result = analyze_field_coverage(extraction_result_missing, expected)
        assert result["present_count"] == 2
        assert result["missing_count"] == 2
        assert "numeroCarta" in result["missing"]

    def test_empty_fields(self, extraction_result_full: dict[str, Any]) -> None:
        expected = ["institucion", "rfcCliente"]
        result = analyze_field_coverage(extraction_result_full, expected)
        # rfcCliente tiene value="" → empty
        assert "rfcCliente" in result["empty"]

    def test_accepts_json_string(self, extraction_result_full: dict[str, Any]) -> None:
        result = analyze_field_coverage(
            json.dumps(extraction_result_full),
            ["institucion"],
        )
        assert result["present_count"] == 1


class TestAnalyzeConfidence:
    def test_confidence_distribution(self, extraction_result_full: dict[str, Any]) -> None:
        result = analyze_confidence(extraction_result_full)
        assert result["field_count"] == 5
        assert result["avg_confidence"] > 0
        # montoOperacion tiene confidence=0.45 < 0.5 → low
        assert result["low_confidence_count"] >= 1
        low_fields = [f["field"] for f in result["low_confidence_fields"]]
        assert "montoOperacion" in low_fields

    def test_no_confidence_data(self) -> None:
        result = analyze_confidence({"fields": [{"name": "x", "value": "y"}]})
        assert result["verdict"] == "NO_DATA"
        assert result["field_count"] == 0


class TestAnalyzeSourcesStrategies:
    def test_source_distribution(self, extraction_result_full: dict[str, Any]) -> None:
        result = analyze_sources_strategies(extraction_result_full)
        assert "JSON_PDF" in result["sources"]
        assert result["sources"]["JSON_PDF"] == 5
        assert "REGEX" in result["strategies"]
        assert "KEY_WORD" in result["strategies"]
        assert "FORMS" in result["strategies"]
        assert "TABLE" in result["strategies"]
        assert result["dominant_source"] == "JSON_PDF"

    def test_empty_data(self) -> None:
        result = analyze_sources_strategies({"fields": []})
        assert result["total_fields"] == 0
        assert result["dominant_source"] is None


class TestDetectAnomalies:
    def test_detect_missing(self, extraction_result_missing: dict[str, Any]) -> None:
        result = detect_anomalies(extraction_result_missing, ["institucion", "numeroCarta", "montoOperacion"])
        types = [a["type"] for a in result["anomalies"]]
        assert "MISSING" in types
        assert result["verdict"] == "FAIL"

    def test_detect_empty(self, extraction_result_full: dict[str, Any]) -> None:
        result = detect_anomalies(extraction_result_full)
        types = [a["type"] for a in result["anomalies"]]
        assert "EMPTY" in types  # rfcCliente está vacío

    def test_detect_low_confidence(self, extraction_result_full: dict[str, Any]) -> None:
        result = detect_anomalies(extraction_result_full)
        types = [a["type"] for a in result["anomalies"]]
        assert "LOW_CONFIDENCE" in types  # montoOperacion=0.45

    def test_no_anomalies(self) -> None:
        data = {"fields": [{"name": "x", "value": "y", "confidence": 0.95}]}
        result = detect_anomalies(data, ["x"])
        assert result["anomaly_count"] == 0
        assert result["verdict"] == "PASS"


class TestValidateAgainstSchema:
    def test_validate_pass(self, extraction_result_full: dict[str, Any]) -> None:
        schema = {
            "fields": [
                {"name": "institucion", "required": True, "min_confidence": 0.8},
                {"name": "fechaCarta", "required": True, "min_confidence": 0.8},
            ]
        }
        result = validate_against_schema(extraction_result_full, schema)
        assert result["pass_count"] == 2
        assert result["fail_count"] == 0
        assert result["verdict"] == "PASS"

    def test_validate_missing_required(self, extraction_result_missing: dict[str, Any]) -> None:
        schema = {
            "fields": [
                {"name": "numeroCarta", "required": True, "min_confidence": 0.8},
            ]
        }
        result = validate_against_schema(extraction_result_missing, schema)
        assert result["fail_count"] == 1
        assert result["verdict"] == "FAIL"

    def test_validate_low_confidence_warning(self, extraction_result_full: dict[str, Any]) -> None:
        schema = {
            "fields": [
                {"name": "montoOperacion", "required": True, "min_confidence": 0.8},
            ]
        }
        result = validate_against_schema(extraction_result_full, schema)
        assert result["warn_count"] == 1
        assert result["verdict"] == "WARN"

    def test_validate_accepts_json_string(self, extraction_result_full: dict[str, Any]) -> None:
        schema = {"fields": [{"name": "institucion", "required": True}]}
        result = validate_against_schema(json.dumps(extraction_result_full), json.dumps(schema))
        assert result["pass_count"] == 1


# ---------------------------------------------------------------------------
# Tests — Reports
# ---------------------------------------------------------------------------

class TestReportCartas:
    def test_report_cartas_full(self, extraction_result_full: dict[str, Any]) -> None:
        result = report_cartas(extraction_result_full)
        assert result["domain"] == "cartas_confirmacion"
        assert result["canonical_field_count"] == len(CARTAS_CANONICAL_FIELDS)
        assert "coverage" in result
        assert "confidence" in result
        assert "anomalies" in result
        assert "validation" in result
        assert "verdict" in result
        assert "summary" in result

    def test_report_cartas_with_schema(self, extraction_result_full: dict[str, Any]) -> None:
        schema = {"fields": [{"name": "institucion", "required": True, "min_confidence": 0.9}]}
        result = report_cartas(extraction_result_full, schema)
        assert result["validation"]["total_fields"] == 1


class TestReportOficiosPld:
    def test_report_oficios_pld(self, extraction_result_full: dict[str, Any]) -> None:
        result = report_oficios_pld(extraction_result_full)
        assert result["domain"] == "oficios_pld"
        assert result["field_count"] == len(OFICIOS_PLD_FIELDS)
        assert "summary" in result


class TestReportProspectos:
    def test_report_prospectos_default_sections(self, extraction_result_full: dict[str, Any]) -> None:
        result = report_prospectos(extraction_result_full)
        assert result["domain"] == "prospectos_cnbv"
        assert "coverage" in result
        assert "validation" in result

    def test_report_prospectos_custom_schema(self, extraction_result_full: dict[str, Any]) -> None:
        schema = {"fields": [{"name": "portada", "required": True}]}
        result = report_prospectos(extraction_result_full, schema)
        assert result["section_count"] == 1


class TestReportGeneric:
    def test_report_generic_with_fields(self, extraction_result_full: dict[str, Any]) -> None:
        result = report_generic(
            extraction_result_full,
            expected_fields=["institucion", "fechaCarta", "missing_field"],
        )
        assert result["domain"] == "generic"
        assert result["coverage"]["expected_count"] == 3
        assert result["verdict"] in ("FAIL", "WARN", "PASS", "CRITICAL", "POOR", "FAIR", "GOOD", "EXCELLENT")

    def test_report_generic_no_fields(self, extraction_result_full: dict[str, Any]) -> None:
        result = report_generic(extraction_result_full)
        assert result["domain"] == "generic"
        assert "confidence" in result
        assert "anomalies" in result

    def test_report_generic_with_schema(self, extraction_result_full: dict[str, Any]) -> None:
        schema = {"fields": [{"name": "institucion", "required": True}]}
        result = report_generic(extraction_result_full, schema_json=schema)
        assert result["validation"]["pass_count"] == 1
