"""Tests para mcp-sonar."""

from __future__ import annotations

import shutil
from pathlib import Path

from mcp_sonar.tools.sonar_tools import sonar_scan


def test_sonar_mock(tmp_path: Path, monkeypatch) -> None:
    # Simular que sonar-scanner no existe
    monkeypatch.setattr(shutil, "which", lambda x: None)

    res = sonar_scan(tmp_path, "http://local", "")
    assert res["mode"] == "mock"
    assert res["status"] == "success"
    assert "coverage" in res["metrics"]
    assert res["metrics"]["code_smells"] == 12
