"""Tests para mcp-design-patterns."""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_design_patterns.tools.dp_tools import (
    analyze_code_patterns,
    suggest_design_pattern,
)
from mcp_shared.errors import FileNotFoundError


@pytest.fixture
def sample_py_file(tmp_path: Path) -> Path:
    f = tmp_path / "sample.py"
    # Un método con muchos argumentos y un god object
    code = """
class GodObject:
    def m1(self): pass
    def m2(self): pass
    def m3(self): pass
    def m4(self): pass
    def m5(self): pass
    def m6(self): pass
    def m7(self): pass
    def m8(self): pass
    def m9(self): pass
    def m10(self): pass
    def m11(self): pass

def long_args_func(a, b, c, d, e, f, g):
    pass
"""
    f.write_text(code, encoding="utf-8")
    return f


def test_analyze_code_patterns(sample_py_file: Path) -> None:
    res = analyze_code_patterns(sample_py_file)
    assert res["antipatterns_found"] == 2
    types = [ap["type"] for ap in res["antipatterns"]]
    assert "God Object" in types
    assert "Too Many Arguments" in types


def test_analyze_code_patterns_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        analyze_code_patterns(tmp_path / "missing.py")


def test_suggest_design_pattern() -> None:
    res = suggest_design_pattern("necesito una single instance")
    assert res["pattern"] == "Singleton"

    res = suggest_design_pattern("tengo eventos a los que suscribirse")
    assert res["pattern"] == "Observer"
