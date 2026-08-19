"""Tests para Doc Transform Tools."""

from __future__ import annotations

import json

import pytest
import yaml

from mcp_documentation.tools.doc_transform_tools import (
    html_to_markdown,
    json_to_yaml,
    markdown_to_html,
    markdown_to_plain_text,
    merge_documents,
    xml_to_yaml,
    yaml_to_json,
)


class TestMarkdownToHtml:
    def test_from_text(self, mock_settings):
        html = markdown_to_html("# Hello\n\nContent with **bold**.", is_path=False)
        assert "<html" in html
        assert "<h1>Hello</h1>" in html or "Hello" in html
        assert "<strong>bold</strong>" in html

    def test_from_file(self, mock_settings, sample_md_file):
        html = markdown_to_html(sample_md_file)
        assert "<html" in html


class TestHtmlToMarkdown:
    def test_basic_conversion(self, mock_settings):
        html = "<h1>Title</h1><p>Paragraph with <strong>bold</strong>.</p>"
        md = html_to_markdown(html)
        assert "# Title" in md
        assert "**bold**" in md


class TestMarkdownToPlainText:
    def test_strips_markup(self, mock_settings):
        md = "# Title\n\n**bold** and _italic_ and `code`."
        plain = markdown_to_plain_text(md, is_path=False)
        assert "#" not in plain
        assert "*" not in plain
        assert "bold" in plain
        assert "italic" in plain


class TestYamlToJson:
    def test_from_text(self, mock_settings):
        y = "name: test\nversion: 1.0"
        result = yaml_to_json(y, is_path=False)
        data = json.loads(result)
        assert data["name"] == "test"
        assert data["version"] == "1.0"

    def test_from_file(self, mock_settings, sample_yaml_file):
        result = yaml_to_json(sample_yaml_file)
        data = json.loads(result)
        assert data["database"]["host"] == "localhost"


class TestJsonToYaml:
    def test_from_text(self, mock_settings):
        j = '{"name": "test", "version": "1.0.0"}'
        result = json_to_yaml(j, is_path=False)
        data = yaml.safe_load(result)
        assert data["name"] == "test"


class TestXmlToYaml:
    def test_from_text(self, mock_settings):
        x = "<root><name>test</name></root>"
        result = xml_to_yaml(x, is_path=False)
        data = yaml.safe_load(result)
        assert data["root"]["name"] == "test"

    def test_from_file(self, mock_settings, sample_xml_file):
        result = xml_to_yaml(sample_xml_file)
        data = yaml.safe_load(result)
        assert data["root"]["name"] == "test"


class TestMergeDocuments:
    def test_merge_two(self, mock_settings, tmp_root):
        f1 = tmp_root / "a.md"
        f2 = tmp_root / "b.md"
        f1.write_text("---\ntitle: A\n---\n# A\n\nContent A.", encoding="utf-8")
        f2.write_text("---\ntitle: B\n---\n# B\n\nContent B.", encoding="utf-8")
        result = merge_documents([str(f1), str(f2)])
        assert "Content A" in result
        assert "Content B" in result
        assert "---" in result
