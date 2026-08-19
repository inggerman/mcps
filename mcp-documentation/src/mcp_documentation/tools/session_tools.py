"""Session Tools — 8 herramientas para tracking de sesiones."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp_documentation.config import settings
from mcp_documentation.session_tracker import (
    detect_problems as _detect_problems,
    end_session as _end_session,
    generate_session_report as _generate_report,
    get_session_history as _get_history,
    log_session_event as _log_event,
    start_session as _start_session,
    suggest_solutions as _suggest_solutions,
    track_change as _track_change,
)


def start_session_tool(project: str = "", context: str = "", agent: str = "unknown") -> dict[str, Any]:
    """Inicia tracking de sesión: crea estructura con ID, timestamp, contexto inicial."""
    return _start_session(settings.root_path, project, context, agent)


def log_session_event_tool(
    session_id: str,
    event_type: str,
    description: str,
    severity: str = "low",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Registra evento durante sesión (problem, solution, change, decision, note)."""
    return _log_session_event(settings.root_path, session_id, event_type, description, severity, metadata)


def detect_problems_tool(session_id: str) -> dict[str, Any]:
    """Analiza eventos de sesión e identifica patrones de problemas."""
    return _detect_problems(settings.root_path, session_id)


def suggest_solutions_tool(session_id: str) -> dict[str, Any]:
    """Basado en problemas detectados, sugiere soluciones desde historial de documentación."""
    return _suggest_solutions(settings.root_path, session_id)


def track_change_tool(
    session_id: str,
    file_path: str,
    change_type: str,
    description: str = "",
) -> dict[str, Any]:
    """Registra un cambio durante la sesión (archivo, descripción, tipo: add/modify/delete)."""
    return _track_change(settings.root_path, session_id, file_path, change_type, description)


def end_session_tool(session_id: str, summary: str = "") -> dict[str, Any]:
    """Cierra sesión: genera bitácora automática con resumen, problemas, soluciones, cambios."""
    return _end_session(settings.root_path, session_id, summary)


def get_session_history_tool(limit: int = 20, project: str | None = None) -> list[dict[str, Any]]:
    """Historial de sesiones anteriores con filtros por fecha, proyecto, tipo."""
    return _get_history(settings.root_path, limit, project)


def generate_session_report_tool(session_id: str) -> str:
    """Genera reporte Markdown completo de una sesión específica."""
    return _generate_report(settings.root_path, session_id)
