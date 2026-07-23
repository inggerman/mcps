"""Tests para mcp-terraform."""

from __future__ import annotations

import shutil
from pathlib import Path

from mcp_terraform.tools.tf_tools import tf_run


def test_tf_mock(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda x: None)
    res = tf_run(tmp_path, "plan")
    assert res["mode"] == "mock"
    assert "Plan: 1 to add" in res["output"]
