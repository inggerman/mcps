"""Tests para mcp-project-memory tools."""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_project_memory.tools.memory_tools import (
    add_pending_task,
    complete_pending_task,
    export_memory_snapshot,
    generate_project_brief,
    get_component_map,
    get_decisions_history,
    get_project_state,
    get_session_history,
    initialize_project,
    record_decision,
    search_memory,
    snapshot_session,
    sync_from_filesystem,
    update_component_status,
)
from mcp_shared.errors import NotFoundError, ValidationError


@pytest.fixture
def memory_path(tmp_path: Path) -> Path:
    """Ruta temporal de memoria para tests."""
    return tmp_path / ".ai-memory" / "project_memory.json"


# ---------------------------------------------------------------------------
# Tests de inicialización
# ---------------------------------------------------------------------------


def test_initialize_project(memory_path: Path) -> None:
    result = initialize_project(
        memory_path,
        project_name="mcps",
        description="Framework de servidores MCP",
        tech_stack=["Python", "FastMCP", "Docker"],
        invariants=["La lógica de negocio nunca importa de fastmcp"],
    )
    assert result["name"] == "mcps"
    assert "Python" in result["tech_stack"]
    assert memory_path.exists()


def test_initialize_project_invalid_name(memory_path: Path) -> None:
    with pytest.raises(ValidationError):
        initialize_project(memory_path, project_name="x", description="desc")


def test_initialize_project_idempotent(memory_path: Path) -> None:
    initialize_project(memory_path, project_name="v1", description="primera")
    snapshot_session(memory_path, "sesión de prueba inicial", [], agent="test")
    # Segunda inicialización no debe borrar sesiones
    initialize_project(memory_path, project_name="v2", description="segunda")
    sessions = get_session_history(memory_path)
    assert len(sessions) == 1  # sesión preservada


# ---------------------------------------------------------------------------
# Tests de estado del proyecto
# ---------------------------------------------------------------------------


def test_get_project_state_empty(memory_path: Path) -> None:
    state = get_project_state(memory_path)
    assert "components" in state
    assert "pending_tasks" in state
    assert "stats" in state
    assert state["stats"]["total_components"] == 0


def test_get_project_state_with_data(memory_path: Path) -> None:
    initialize_project(memory_path, "mcps", "Framework MCP")
    update_component_status(memory_path, "mcp-tabular", "ready", version="1.0.0", tools=8)
    add_pending_task(memory_path, "Agregar CI/CD", priority="high")
    state = get_project_state(memory_path)
    assert state["stats"]["total_components"] == 1
    assert state["stats"]["pending_tasks_count"] == 1


# ---------------------------------------------------------------------------
# Tests de componentes
# ---------------------------------------------------------------------------


def test_update_component_status(memory_path: Path) -> None:
    result = update_component_status(
        memory_path, "mcp-tabular", "ready", version="1.0.0", tools=8, port=8001
    )
    assert result["mcp-tabular"]["status"] == "ready"
    assert result["mcp-tabular"]["version"] == "1.0.0"


def test_update_component_status_invalid(memory_path: Path) -> None:
    with pytest.raises(ValidationError):
        update_component_status(memory_path, "mcp-tabular", "unknown_status")


def test_get_component_map(memory_path: Path) -> None:
    update_component_status(memory_path, "mcp-calendar", "ready", version="1.0.0")
    update_component_status(memory_path, "mcp-markdown", "draft", version="0.5.0")
    components = get_component_map(memory_path)
    assert "mcp-calendar" in components
    assert "mcp-markdown" in components
    assert components["mcp-calendar"]["status"] == "ready"


# ---------------------------------------------------------------------------
# Tests de decisiones
# ---------------------------------------------------------------------------


def test_record_decision(memory_path: Path) -> None:
    decision = record_decision(
        memory_path,
        title="FastMCP como framework base",
        rationale="Es el framework más maduro y con mejor DX para FastAPI-style MCP.",
        alternatives_rejected=["mcp-python-sdk vanilla", "custom protocol"],
        tags=["arquitectura"],
    )
    assert decision["id"] == "DEC-0001"
    assert decision["status"] == "active"


def test_record_decision_invalid(memory_path: Path) -> None:
    with pytest.raises(ValidationError):
        record_decision(memory_path, title="OK", rationale="corto")


def test_get_decisions_history_filter(memory_path: Path) -> None:
    record_decision(memory_path, "Decision uno", "Justificación suficientemente larga")
    record_decision(memory_path, "Decision dos", "Otra justificación suficientemente larga")
    all_decisions = get_decisions_history(memory_path)
    assert len(all_decisions) == 2
    active = get_decisions_history(memory_path, status_filter="active")
    assert len(active) == 2


def test_get_decisions_history_invalid_filter(memory_path: Path) -> None:
    with pytest.raises(ValidationError):
        get_decisions_history(memory_path, status_filter="invalid")


# ---------------------------------------------------------------------------
# Tests de tareas
# ---------------------------------------------------------------------------


def test_add_and_complete_task(memory_path: Path) -> None:
    task = add_pending_task(memory_path, "Implementar CI/CD", priority="high")
    assert task["id"] == "TASK-0001"
    assert task["status"] == "pending"

    completed = complete_pending_task(memory_path, "TASK-0001", "Pipeline creado en GitHub Actions")
    assert completed["status"] == "completed"
    assert "completed_at" in completed

    # Ya no debe estar en pendientes
    state = get_project_state(memory_path)
    assert state["stats"]["pending_tasks_count"] == 0
    assert state["stats"]["completed_tasks_count"] == 1


def test_complete_nonexistent_task(memory_path: Path) -> None:
    with pytest.raises(NotFoundError):
        complete_pending_task(memory_path, "TASK-9999")


def test_add_task_invalid_priority(memory_path: Path) -> None:
    with pytest.raises(ValidationError):
        add_pending_task(memory_path, "Tarea", priority="urgent")


# ---------------------------------------------------------------------------
# Tests de sesiones
# ---------------------------------------------------------------------------


def test_snapshot_session(memory_path: Path) -> None:
    result = snapshot_session(
        memory_path,
        summary="Se implementó mcp-project-memory con 15 tools",
        changes_made=["mcp-project-memory/src/...", "pyproject.toml"],
        decisions_taken=1,
        tasks_completed=2,
        agent="claude-sonnet-4-5",
    )
    assert result["session_id"] == "SES-0001"
    assert result["status"] == "saved"


def test_snapshot_session_invalid_summary(memory_path: Path) -> None:
    with pytest.raises(ValidationError):
        snapshot_session(memory_path, summary="corto", changes_made=[])


def test_get_session_history_ordered(memory_path: Path) -> None:
    snapshot_session(memory_path, "Primera sesión de trabajo", [], agent="agent-1")
    snapshot_session(memory_path, "Segunda sesión de trabajo", [], agent="agent-2")
    history = get_session_history(memory_path, limit=10)
    assert len(history) == 2
    assert history[0]["id"] == "SES-0002"  # más reciente primero


# ---------------------------------------------------------------------------
# Tests de búsqueda
# ---------------------------------------------------------------------------


def test_search_memory(memory_path: Path) -> None:
    record_decision(memory_path, "FastMCP como framework base", "Es el mejor para MCP")
    add_pending_task(memory_path, "Agregar FastMCP tests")
    results = search_memory(memory_path, "FastMCP")
    assert len(results["decisions"]) >= 1
    assert len(results["tasks"]) >= 1


def test_search_memory_short_query(memory_path: Path) -> None:
    with pytest.raises(ValidationError):
        search_memory(memory_path, "x")


# ---------------------------------------------------------------------------
# Tests de sincronización con filesystem
# ---------------------------------------------------------------------------


def test_sync_from_filesystem(memory_path: Path, tmp_path: Path) -> None:
    # Crear directorios simulando servidores MCP
    (tmp_path / "mcp-test-a").mkdir()
    (tmp_path / "mcp-test-b").mkdir()
    (tmp_path / "shared").mkdir()  # no debe detectarse

    result = sync_from_filesystem(memory_path, tmp_path)
    assert "mcp-test-a" in result["detected_on_filesystem"]
    assert "mcp-test-b" in result["detected_on_filesystem"]
    assert "shared" not in result["detected_on_filesystem"]
    assert result["new_components_added"] == ["mcp-test-a", "mcp-test-b"]


# ---------------------------------------------------------------------------
# Tests de export
# ---------------------------------------------------------------------------


def test_export_memory_snapshot(memory_path: Path) -> None:
    initialize_project(memory_path, "mcps", "Test project")
    snapshot = export_memory_snapshot(memory_path)
    assert "project" in snapshot
    assert "_meta" in snapshot
    assert snapshot["project"]["name"] == "mcps"


# ---------------------------------------------------------------------------
# Tests de generate_project_brief
# ---------------------------------------------------------------------------


def test_generate_project_brief(memory_path: Path) -> None:
    initialize_project(memory_path, "mcps", "Framework de servidores MCP", ["Python", "Docker"])
    update_component_status(memory_path, "mcp-tabular", "ready", "1.0.0")
    add_pending_task(memory_path, "Agregar CI/CD", priority="high")
    brief = generate_project_brief(memory_path)
    assert "mcps" in brief
    assert "mcp-tabular" in brief
    assert "CI/CD" in brief
    assert brief.startswith("#")
