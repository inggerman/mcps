"""Tools de mcp-covaf-data."""

from .extraction import (
    analyze_confidence,
    analyze_field_coverage,
    analyze_sources_strategies,
    detect_anomalies,
    validate_against_schema,
)
from .readers import (
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
)
from .reports import (
    CARTAS_CANONICAL_FIELDS,
    OFICIOS_PLD_FIELDS,
    PROSPECTOS_CONTRACT_SECTIONS,
    report_cartas,
    report_generic,
    report_oficios_pld,
    report_prospectos,
)

__all__ = [
    # Readers
    "read_pdf",
    "read_excel",
    "read_word",
    "read_xml",
    "read_json",
    "read_jsonpdf",
    "read_jsonword",
    "read_xmlshort",
    "parse_s3_path",
    "list_extraction_sources",
    # Extraction analysis
    "analyze_field_coverage",
    "analyze_confidence",
    "analyze_sources_strategies",
    "detect_anomalies",
    "validate_against_schema",
    # Reports
    "report_cartas",
    "report_oficios_pld",
    "report_prospectos",
    "report_generic",
    "CARTAS_CANONICAL_FIELDS",
    "OFICIOS_PLD_FIELDS",
    "PROSPECTOS_CONTRACT_SECTIONS",
]
