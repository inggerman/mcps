"""Tests para mcp-covaf tools."""

from __future__ import annotations

import json
from pathlib import Path

from mcp_covaf.tools.back_tools import (
    back_analyze_cartas_pipeline,
    back_analyze_oficios_pipeline,
    back_get_endpoint_map,
    back_list_extraction_strategies,
    back_list_quality_gates,
    back_search_code,
)
from mcp_covaf.tools.front_tools import (
    front_get_mfe_config,
    front_list_modules,
    front_list_routes,
    front_list_services,
    front_search_code,
)
from mcp_covaf.tools.ia_tools import (
    ia_analyze_extraction_output,
    ia_get_plugin_schema,
    ia_list_eval_tests,
    ia_list_pipeline_tiers,
    ia_list_plugins,
    ia_search_code,
)
from mcp_covaf.tools.lifecycle_tools import (
    lifecycle_get_dependencies,
    lifecycle_get_deploy_manifests,
    lifecycle_get_git_info,
    lifecycle_get_status,
    lifecycle_get_test_command,
    lifecycle_list_components,
)
from mcp_covaf.tools.report_tools import (
    report_format_for_team,
    report_generate_summary,
    report_get_health,
    report_list_findings,
)
from mcp_covaf.tools.template_tools import (
    template_get_schema,
    template_list,
    template_scaffold_new,
    template_validate,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

WORKSPACE = Path(__file__).resolve().parents[3]  # engineering/
BACK_PATH = Path("covaf/CovafDataRefineryBack")
IA_PATH = Path("covaf/IA_IMPL_COVAF/datarefineryia-api")
FRONT_PATH = Path("covaf/CovafAlternativosFront")
DOCS_PATH = Path("docs/projects/covaf")


# ---------------------------------------------------------------------------
# back_tools
# ---------------------------------------------------------------------------

class TestBackTools:
    def test_list_extraction_strategies(self):
        result = back_list_extraction_strategies(WORKSPACE, BACK_PATH)
        assert result["count"] == 10
        assert "REGEX" in result["strategies"]
        assert "TABLE" in result["strategies"]

    def test_list_quality_gates(self):
        result = back_list_quality_gates(WORKSPACE, BACK_PATH)
        assert result["count"] > 0
        assert "ExtractionQualityEvaluator" in result["quality_gates"]

    def test_get_endpoint_map(self):
        result = back_get_endpoint_map(WORKSPACE, BACK_PATH)
        assert result["count"] > 0
        assert "cartas_search" in result["endpoints"]
        assert "oficios_extract" in result["endpoints"]

    def test_search_code(self):
        result = back_search_code(WORKSPACE, BACK_PATH, "class.*Controller", max_results=5)
        assert "matches" in result
        assert isinstance(result["matches"], list)

    def test_analyze_oficios_pipeline(self):
        result = back_analyze_oficios_pipeline(WORKSPACE, BACK_PATH)
        assert "pipeline_components" in result
        assert "OficiosExtractService" in result["pipeline_components"]
        assert result["domain"] == "PLD (Prevención de Lavado de Dinero)"

    def test_analyze_cartas_pipeline(self):
        result = back_analyze_cartas_pipeline(WORKSPACE, BACK_PATH)
        assert "pipeline_components" in result
        assert "ProcessDocumentService" in result["pipeline_components"]
        assert "fondo" in result["campos_canonicos"]


# ---------------------------------------------------------------------------
# ia_tools
# ---------------------------------------------------------------------------

class TestIaTools:
    def test_list_plugins(self):
        result = ia_list_plugins(WORKSPACE, IA_PATH)
        assert result["count"] >= 0
        assert any(p["name"] == "prospectos_cnbv" for p in result["known_plugins"])

    def test_list_pipeline_tiers(self):
        result = ia_list_pipeline_tiers(WORKSPACE, IA_PATH)
        assert len(result["tiers"]) >= 3
        assert result["engine_version"] == "4.0.0-phase8-generic-core"

    def test_get_plugin_schema(self):
        result = ia_get_plugin_schema(WORKSPACE, IA_PATH, "prospectos_cnbv")
        assert result["plugin"] == "prospectos_cnbv"
        assert isinstance(result["fields"], list)

    def test_search_code(self):
        result = ia_search_code(WORKSPACE, IA_PATH, "class.*Plugin", max_results=5)
        assert "matches" in result

    def test_analyze_extraction_output_clean(self):
        data = json.dumps({"fondo": "Test", "serie": "A", "confidence": 0.95})
        result = ia_analyze_extraction_output(WORKSPACE, IA_PATH, data)
        assert result["verdict"] == "clean"
        assert result["issue_count"] == 0

    def test_analyze_extraction_output_low_confidence(self):
        data = json.dumps({"fondo": "Test", "confidence": 0.3})
        result = ia_analyze_extraction_output(WORKSPACE, IA_PATH, data)
        assert result["verdict"] == "exposed"
        assert any(i["type"] == "low_confidence" for i in result["issues"])

    def test_analyze_extraction_output_empty_field(self):
        data = json.dumps({"fondo": "", "confidence": 0.9})
        result = ia_analyze_extraction_output(WORKSPACE, IA_PATH, data)
        assert result["verdict"] == "suspicious"
        assert any(i["type"] == "empty_field" for i in result["issues"])

    def test_list_eval_tests(self):
        result = ia_list_eval_tests(WORKSPACE, IA_PATH)
        assert result["count"] >= 0
        assert result["command"] == "python -m pytest"


# ---------------------------------------------------------------------------
# front_tools
# ---------------------------------------------------------------------------

class TestFrontTools:
    def test_list_routes(self):
        result = front_list_routes(WORKSPACE, FRONT_PATH)
        assert result["count"] > 0
        assert result["base_path"] == "/covafalternativos"
        paths = [r["path"] for r in result["routes"]]
        assert "instrumentos" in paths
        assert "cartasconfirmacion" in paths

    def test_list_modules(self):
        result = front_list_modules(WORKSPACE, FRONT_PATH)
        assert result["count"] >= 0

    def test_list_services(self):
        result = front_list_services(WORKSPACE, FRONT_PATH)
        assert result["count"] >= 0

    def test_search_code(self):
        result = front_search_code(WORKSPACE, FRONT_PATH, "import", max_results=5)
        assert "matches" in result

    def test_get_mfe_config(self):
        result = front_get_mfe_config(WORKSPACE, FRONT_PATH)
        assert result["mfe"]["name"] == "covafalternativos"
        assert "Vue" in result["framework"]


# ---------------------------------------------------------------------------
# lifecycle_tools
# ---------------------------------------------------------------------------

class TestLifecycleTools:
    def test_list_components(self):
        result = lifecycle_list_components(WORKSPACE)
        assert result["count"] == 4
        keys = [c["key"] for c in result["components"]]
        assert "covaf-back" in keys
        assert "covaf-ia" in keys
        assert "covaf-front" in keys

    def test_get_status(self):
        result = lifecycle_get_status(WORKSPACE)
        assert result["count"] == 4
        for c in result["components"]:
            assert "status" in c

    def test_get_git_info(self):
        result = lifecycle_get_git_info(WORKSPACE, "covaf-back")
        assert result["key"] == "covaf-back"
        assert "head" in result or "error" in result

    def test_get_dependencies(self):
        result = lifecycle_get_dependencies(WORKSPACE, "covaf-back")
        assert result["key"] == "covaf-back"
        assert isinstance(result["dependencies"], list)

    def test_get_test_command(self):
        result = lifecycle_get_test_command(WORKSPACE, "covaf-back")
        assert result["test_command"] == "mvn test"

    def test_get_deploy_manifests(self):
        result = lifecycle_get_deploy_manifests(WORKSPACE, "covaf-back")
        assert result["key"] == "covaf-back"
        assert isinstance(result["manifests"], list)


# ---------------------------------------------------------------------------
# report_tools
# ---------------------------------------------------------------------------

class TestReportTools:
    def test_get_health(self):
        result = report_get_health(WORKSPACE, DOCS_PATH)
        assert "observed_count" in result
        assert "unverified_count" in result

    def test_list_findings(self):
        result = report_list_findings(WORKSPACE, DOCS_PATH)
        assert "findings" in result
        assert "count" in result

    def test_generate_summary(self):
        result = report_generate_summary(WORKSPACE, DOCS_PATH)
        assert "components_total" in result
        assert "documentation_health" in result

    def test_format_for_team_status(self):
        result = report_format_for_team(WORKSPACE, DOCS_PATH, "status")
        assert result["report_type"] == "status"
        assert "formatted_text" in result
        assert "COVAF" in result["formatted_text"]

    def test_format_for_team_lifecycle(self):
        result = report_format_for_team(WORKSPACE, DOCS_PATH, "lifecycle")
        assert result["report_type"] == "lifecycle"
        assert "Componentes" in result["formatted_text"]


# ---------------------------------------------------------------------------
# template_tools
# ---------------------------------------------------------------------------

class TestTemplateTools:
    def test_list(self):
        result = template_list(WORKSPACE, DOCS_PATH)
        assert result["count"] == 3
        names = [t["name"] for t in result["templates"]]
        assert "cartas_confirmacion" in names
        assert "oficios_pld" in names
        assert "prospectos_cnbv" in names

    def test_get_schema(self):
        result = template_get_schema("cartas_confirmacion")
        assert result["name"] == "cartas_confirmacion"
        assert "fondo" in result["schema"]["fields"]

    def test_validate_valid(self):
        data = json.dumps({"fondo": "X", "tipoValor": "A", "instrumento": "B",
                          "serie": "1", "tipoMovimiento": "C", "titulos": 10,
                          "monto": 100, "fechaOperacion": "2026-01-01",
                          "institucion": "I", "contrato": "C",
                          "firma": "F", "observaciones": "O"})
        result = template_validate("cartas_confirmacion", data)
        assert result["valid"] is True
        assert result["coverage_pct"] == 100

    def test_validate_missing(self):
        data = json.dumps({"fondo": "X"})
        result = template_validate("cartas_confirmacion", data)
        assert result["valid"] is False
        assert len(result["missing_fields"]) > 0

    def test_scaffold_new(self):
        result = template_scaffold_new(WORKSPACE, IA_PATH, "test_plugin", "Test domain")
        assert result["plugin_name"] == "test_plugin"
        assert "scaffold_command" in result
