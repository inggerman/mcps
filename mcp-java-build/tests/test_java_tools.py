"""Tests para mcp-java-build."""

from __future__ import annotations

import shutil
from pathlib import Path

from mcp_java_build.tools.java_tools import (
    java_gradle_cmd,
    java_maven_cmd,
)


def test_java_maven_mock(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda x: None)
    res = java_maven_cmd(tmp_path, "clean install")
    assert res["mode"] == "mock"
    assert "BUILD SUCCESS" in res["output"]


def test_java_gradle_mock(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda x: None)
    res = java_gradle_cmd(tmp_path, "build")
    assert res["mode"] == "mock"
    assert "BUILD SUCCESSFUL" in res["output"]
