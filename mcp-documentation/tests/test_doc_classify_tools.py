"""Tests para Doc Classify Tools y classifiers."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_documentation.classifiers import (
    add_custom_category,
    classify_document,
    classify_from_frontmatter,
    classify_text,
    get_all_categories,
    get_directory_for_category,
    load_custom_categories,
    validate_classification,
)
from mcp_documentation.tools.doc_classify_tools import (
    add_custom_category_tool,
    classify_document_tool,
    get_categories,
    reclassify_document,
    validate_classification_tool,
)


class TestClassifyText:
    def test_feature_keywords(self):
        result = classify_text("Nueva funcionalidad para el sistema de autenticación")
        assert result == "feature"

    def test_fix_keywords(self):
        result = classify_text("Bug fix: corrección del error de login")
        assert result == "fix"

    def test_hotfix_keywords(self):
        result = classify_text("Hotfix urgente para producción, parche crítico")
        assert result == "hotfix"

    def test_bitacora_keywords(self):
        result = classify_text("Bitácora de la sesión de trabajo del día")
        assert result == "bitacora"

    def test_investigation_keywords(self):
        result = classify_text("Investigación del root cause del incidente")
        assert result == "investigation"

    def test_no_match_defaults_information(self):
        result = classify_text("Texto sin keywords específicos")
        assert result == "information"


class TestClassifyFromFrontmatter:
    def test_valid_type(self):
        assert classify_from_frontmatter({"type": "feature"}) == "feature"

    def test_invalid_type(self):
        assert classify_from_frontmatter({"type": "unknown_type"}) is None

    def test_no_frontmatter(self):
        assert classify_from_frontmatter(None) is None


class TestClassifyDocument:
    def test_frontmatter_priority(self):
        result = classify_document("bug fix content", {"type": "feature"})
        assert result == "feature"

    def test_text_fallback(self):
        result = classify_document("Nueva funcionalidad del módulo", None)
        assert result == "feature"


class TestGetAllCategories:
    def test_includes_core(self):
        cats = get_all_categories()
        assert "feature" in cats
        assert "fix" in cats
        assert "bitacora" in cats
        assert "architecture" in cats

    def test_includes_custom(self, tmp_path):
        custom = tmp_path / ".categories.json"
        custom.write_text('{"custom_cat": ["keyword1"]}', encoding="utf-8")
        cats = get_all_categories(custom)
        assert "custom_cat" in cats
        assert cats["custom_cat"]["is_custom"] is True


class TestGetDirectoryForCategory:
    def test_known_category(self):
        assert get_directory_for_category("feature") == "feature"
        assert get_directory_for_category("bitacora") == "bitacoras"
        assert get_directory_for_category("decision") == "decisions"


class TestValidateClassification:
    def test_correct_dir(self, tmp_path):
        file_path = tmp_path / "feature" / "doc.md"
        file_path.parent.mkdir()
        file_path.write_text("content")
        result = validate_classification(file_path, "feature", tmp_path)
        assert result["valid"] is True

    def test_wrong_dir(self, tmp_path):
        file_path = tmp_path / "fix" / "doc.md"
        file_path.parent.mkdir()
        file_path.write_text("content")
        result = validate_classification(file_path, "feature", tmp_path)
        assert result["valid"] is False


class TestAddCustomCategory:
    def test_add_new(self, tmp_path):
        custom = tmp_path / ".categories.json"
        result = add_custom_category(custom, "my_cat", ["kw1", "kw2"])
        assert result["name"] == "my_cat"
        loaded = load_custom_categories(custom)
        assert "my_cat" in loaded

    def test_update_existing(self, tmp_path):
        custom = tmp_path / ".categories.json"
        add_custom_category(custom, "my_cat", ["kw1"])
        add_custom_category(custom, "my_cat", ["kw2"])
        loaded = load_custom_categories(custom)
        assert loaded["my_cat"] == ["kw2"]


class TestClassifyTool:
    def test_classify_existing(self, mock_settings, sample_md_file):
        result = classify_document_tool(sample_md_file)
        assert result["suggested_category"] == "feature"
        assert result["current_category"] == "feature"
        assert result["matches"] is True


class TestGetCategoriesTool:
    def test_returns_all(self, mock_settings):
        result = get_categories()
        assert result["total"] >= 19
        assert "feature" in result["categories"]


class TestAddCustomCategoryTool:
    def test_add(self, mock_settings, tmp_root):
        result = add_custom_category_tool("test_cat", ["test_kw"])
        assert result["name"] == "test_cat"


class TestValidateClassificationTool:
    def test_valid(self, mock_settings, sample_md_file):
        result = validate_classification_tool(sample_md_file)
        assert "valid" in result


class TestReclassifyDocument:
    def test_reclassify(self, mock_settings, sample_md_file):
        result = reclassify_document(sample_md_file, "fix")
        assert result["moved"] is True
        assert "fix" in result["new_path"]
