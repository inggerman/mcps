"""Tests para mcp-best-practices."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from mcp_best_practices.tools.bp_tools import (
    update_project_state,
    update_servers_reference,
)


@pytest.fixture
def fake_project(tmp_path: Path) -> Path:
    # Simular pyproject.toml
    (tmp_path / "pyproject.toml").write_text('version = "1.2.3"\n', encoding="utf-8")

    # Simular claude config
    cfg = {
        "mcpServers": {
            "mcp-test1": {"command": "node", "args": ["index.js"], "env": {"TOKEN": "secret123"}}
        }
    }
    (tmp_path / "claude_desktop_config.json").write_text(json.dumps(cfg), encoding="utf-8")

    # Simular algunos servidores
    (tmp_path / "mcp-test1").mkdir()
    (tmp_path / "mcp-test2").mkdir()
    (tmp_path / "not-a-server").mkdir()

    return tmp_path


def test_update_project_state(fake_project: Path) -> None:
    docs = fake_project / "docs"
    res = update_project_state(fake_project, docs)
    assert res["servers_found"] == 2

    content = (docs / "project-state.md").read_text(encoding="utf-8")
    assert "1.2.3" in content
    assert "mcp-test1" in content


def test_update_servers_reference(fake_project: Path) -> None:
    docs = fake_project / "docs"
    res = update_servers_reference(fake_project, docs)
    assert res["servers_documented"] == 1

    content = (docs / "servers-reference.md").read_text(encoding="utf-8")
    assert "mcp-test1" in content
    assert "********" in content  # Token censurado
    assert "secret123" not in content
