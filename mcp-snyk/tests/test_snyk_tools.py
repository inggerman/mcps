"""Tests para mcp-snyk."""

from __future__ import annotations

import shutil
from pathlib import Path

from mcp_snyk.tools.snyk_tools import snyk_test


def test_snyk_mock(tmp_path: Path, monkeypatch) -> None:
    # Simular que snyk no existe para forzar el mock
    monkeypatch.setattr(shutil, "which", lambda x: None)

    res = snyk_test(tmp_path, "")
    assert res["mode"] == "mock"
    assert res["status"] == "success"
    assert len(res["vulnerabilities"]) == 1
    assert "Cross-Site Scripting" in res["vulnerabilities"][0]["title"]
