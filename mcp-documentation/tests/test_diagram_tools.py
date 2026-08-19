"""Tests para Diagram Tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_documentation.tools.diagram_tools import (
    create_mermaid_diagram,
    create_plantuml_diagram,
    embed_diagram_in_md,
    list_diagrams,
)


class TestCreateMermaidDiagram:
    def test_create(self, mock_settings, tmp_root):
        result = create_mermaid_diagram(
            "Architecture",
            "graph TD\n    A[Start] --> B[End]",
        )
        assert result["created"] is True
        assert result["format"] == "mmd"
        assert Path(result["path"]).exists()
        content = Path(result["path"]).read_text()
        assert "graph TD" in content

    def test_short_definition_raises(self, mock_settings, tmp_root):
        with pytest.raises(ValueError, match="10 caracteres"):
            create_mermaid_diagram("Test", "short")


class TestCreatePlantumlDiagram:
    def test_create_with_start_end(self, mock_settings, tmp_root):
        result = create_plantuml_diagram(
            "Sequence",
            "@startuml\nA -> B\n@enduml",
        )
        assert result["created"] is True
        assert result["format"] == "puml"

    def test_create_without_start_end(self, mock_settings, tmp_root):
        result = create_plantuml_diagram(
            "Sequence",
            "A -> B\nB -> C",
        )
        content = Path(result["path"]).read_text()
        assert "@startuml" in content
        assert "@enduml" in content


class TestEmbedDiagramInMd:
    def test_embed_at_end(self, mock_settings, tmp_root):
        md = tmp_root / "doc.md"
        md.write_text("---\ntitle: Test\n---\n# Test\n\nContent.", encoding="utf-8")
        diag = create_mermaid_diagram("Test", "graph TD\n    A --> B")
        result = embed_diagram_in_md(str(md), diag["path"])
        assert result["embedded"] is True
        content = md.read_text()
        assert "```mermaid" in content

    def test_embed_with_caption(self, mock_settings, tmp_root):
        md = tmp_root / "doc.md"
        md.write_text("# Test\n\nContent.", encoding="utf-8")
        diag = create_mermaid_diagram("Test", "graph TD\n    A --> B")
        result = embed_diagram_in_md(str(md), diag["path"], caption="My Diagram")
        content = md.read_text()
        assert "My Diagram" in content


class TestListDiagrams:
    def test_list(self, mock_settings, tmp_root):
        create_mermaid_diagram("A", "graph TD\n    A --> B")
        create_plantuml_diagram("B", "A -> B")
        result = list_diagrams()
        assert len(result) == 2

    def test_list_empty(self, mock_settings, tmp_root):
        result = list_diagrams()
        assert len(result) == 0
