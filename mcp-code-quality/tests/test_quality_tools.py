"""Tests para mcp-code-quality."""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_code_quality.tools.quality_tools import (
    run_format,
    run_lint,
)
from mcp_shared.errors import ValidationError


@pytest.fixture
def fake_project(tmp_path: Path) -> Path:
    # Crear un proyecto python básico
    (tmp_path / "test_module.py").write_text("def foo():\n  pass\n", encoding="utf-8")
    return tmp_path


def test_run_lint_success(fake_project: Path) -> None:
    # Como no sabemos qué herramientas hay, usamos python -c pass
    # (Comando falso de lint que siempre pasa)
    result = run_lint(fake_project, linter_cmd="python -c pass")
    assert result["success"] is True


def test_run_lint_failure(fake_project: Path) -> None:
    # Escribir código python inválido
    bad_file = fake_project / "bad.py"
    bad_file.write_text("def foo(", encoding="utf-8")

    result = run_lint(fake_project, linter_cmd="python -m py_compile", target="bad.py")
    assert result["success"] is False
    assert "SyntaxError" in result["output"]


def test_run_format(fake_project: Path) -> None:
    # Comando eco simulando formateo
    # Nota: Windows usa 'echo' nativo que podría tener comillas, etc. Usaremos python -c
    result = run_format(fake_project, formatter_cmd="python -c \"print('Formatted')\"")
    assert result["success"] is True
    assert "Formatted" in result["output"]


def test_invalid_command(fake_project: Path) -> None:
    with pytest.raises(ValidationError, match="No se pudo ejecutar"):
        run_lint(fake_project, linter_cmd="thiscommanddoesnotexist_123")
