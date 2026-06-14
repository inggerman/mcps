"""Tests para mcp-architecture."""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_architecture.tools.arch_tools import (
    analyze_dependencies,
    analyze_solid_heuristics,
    get_project_tree,
)
from mcp_shared.errors import FileNotFoundError, ValidationError


@pytest.fixture
def fake_project(tmp_path: Path) -> Path:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text(
        "import os\nfrom datetime import datetime\ndef hello(a, b, c, d, e, f):\n    pass\n",
        encoding="utf-8",
    )

    # Archivo con clase grande
    class_code = "class GodObject:\n"
    for i in range(15):
        class_code += f"    def method_{i}(self):\n        pass\n"
    (src_dir / "god.py").write_text(class_code, encoding="utf-8")

    return tmp_path


def test_get_project_tree(fake_project: Path) -> None:
    tree = get_project_tree(fake_project)
    assert "src" in tree
    assert "main.py" in tree
    assert "god.py" in tree


def test_analyze_dependencies(fake_project: Path) -> None:
    result = analyze_dependencies(fake_project, "src/main.py")
    assert "os" in result["absolute_imports"]
    assert any(im["module"] == "datetime" for im in result["from_imports"])
    assert result["total_dependencies"] == 2


def test_analyze_solid_heuristics_healthy(fake_project: Path) -> None:
    result = analyze_solid_heuristics(fake_project, "src/main.py")
    # Tiene una función con 6 argumentos -> TOO_MANY_ARGS
    assert result["is_healthy"] is False
    assert len(result["warnings"]) == 1
    assert result["warnings"][0]["type"] == "TOO_MANY_ARGS"


def test_analyze_solid_heuristics_god_object(fake_project: Path) -> None:
    result = analyze_solid_heuristics(fake_project, "src/god.py")
    assert result["is_healthy"] is False
    assert result["warnings"][0]["type"] == "SRP_WARNING"


def test_invalid_file(fake_project: Path) -> None:
    with pytest.raises(FileNotFoundError):
        analyze_dependencies(fake_project, "does_not_exist.py")

    (fake_project / "test.txt").write_text("test")
    with pytest.raises(ValidationError):
        analyze_dependencies(fake_project, "test.txt")
