"""Tests para mcp-git tools."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from mcp_git.tools.git_tools import (
    confirm_commit,
    get_git_log,
    get_git_status,
    git_add,
    git_branch,
    git_reset,
    prepare_commit,
)
from mcp_shared.errors import NotFoundError, ValidationError


@pytest.fixture
def repo_path(tmp_path: Path) -> Path:
    """Crea un repositorio git temporal para pruebas."""
    # Inicializar git
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)

    # Crear un primer commit
    test_file = tmp_path / "README.md"
    test_file.write_text("Init", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=str(tmp_path), check=True)

    return tmp_path


def test_get_git_status(repo_path: Path) -> None:
    status = get_git_status(repo_path)
    assert status["is_clean"] is True
    assert "main" in status["branch"] or "master" in status["branch"]

    # Hacer un cambio
    (repo_path / "README.md").write_text("Modified", encoding="utf-8")
    status = get_git_status(repo_path)
    assert status["is_clean"] is False
    assert len(status["changes"]) == 1
    assert "M" in status["changes"][0]["state"]
    assert status["changes"][0]["file"] == "README.md"


def test_git_add_and_reset(repo_path: Path) -> None:
    (repo_path / "new_file.txt").write_text("Hello", encoding="utf-8")

    # Add
    result = git_add(repo_path, ["new_file.txt"])
    assert "new_file.txt" in result
    status = get_git_status(repo_path)
    assert status["changes"][0]["state"] == "A "

    # Reset
    result = git_reset(repo_path)
    assert "removieron" in result
    status = get_git_status(repo_path)
    assert status["changes"][0]["state"] == "??"


def test_commit_flow(repo_path: Path) -> None:
    # 1. Modificar y agregar al stage
    (repo_path / "README.md").write_text("Modified", encoding="utf-8")
    git_add(repo_path, ["README.md"])

    # 2. Preparar commit
    prep = prepare_commit(repo_path, "Update readme")
    assert prep["status"] == "pending_confirmation"
    assert "token" in prep
    assert prep["staged_diff"] != ""
    token = prep["token"]

    # 3. Confirmar
    conf = confirm_commit(repo_path, token)
    assert conf["status"] == "success"
    assert "commit_hash" in conf

    # Verificar log
    log = get_git_log(repo_path)
    assert "Update readme" in log


def test_prepare_commit_empty_stage(repo_path: Path) -> None:
    # Sin cambios en stage
    with pytest.raises(ValidationError, match="No hay cambios en el stage"):
        prepare_commit(repo_path, "Empty")


def test_confirm_invalid_token(repo_path: Path) -> None:
    with pytest.raises(NotFoundError):
        confirm_commit(repo_path, "INVALID-TOKEN")


def test_git_branch(repo_path: Path) -> None:
    result = git_branch(repo_path, "feature-1", create=True)
    assert "feature-1" in result

    status = get_git_status(repo_path)
    assert "feature-1" in status["branch"]
