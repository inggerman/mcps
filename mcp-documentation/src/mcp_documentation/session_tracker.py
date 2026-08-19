"""Session tracker para documentación de interacciones.

Gestiona el ciclo de vida de sesiones: start → events → detect problems → end.
Genera bitácoras automáticas al cerrar sesiones.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp_shared.errors import NotFoundError, ValidationError


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sessions_dir(root_path: Path) -> Path:
    return root_path / "sessions"


def _session_path(root_path: Path, session_id: str) -> Path:
    return _sessions_dir(root_path) / f"{session_id}.json"


def _load_session(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise NotFoundError(resource="session", identifier=path.stem)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValidationError(
            field="session_file",
            message=f"No se pudo leer el archivo de sesión: {exc}",
        ) from exc


def _save_session(path: Path, session: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(session, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def start_session(
    root_path: Path,
    project: str = "",
    context: str = "",
    agent: str = "unknown",
) -> dict[str, Any]:
    """Inicia una nueva sesión de tracking.

    Returns:
        Dict con session_id y metadatos.
    """
    now = datetime.now(UTC)
    session_id = f"SES-{now.strftime('%Y%m%d-%H%M%S')}-{now.microsecond % 1000:03d}"

    session = {
        "session_id": session_id,
        "started_at": _now_iso(),
        "ended_at": None,
        "project": project,
        "context": context,
        "agent": agent,
        "events": [],
        "problems_detected": [],
        "solutions_suggested": [],
        "changes_tracked": [],
        "bitacora_path": None,
    }

    path = _session_path(root_path, session_id)
    _save_session(path, session)
    return {"session_id": session_id, "started_at": session["started_at"], "status": "active"}


def log_session_event(
    root_path: Path,
    session_id: str,
    event_type: str,
    description: str,
    severity: str = "low",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Registra un evento durante la sesión.

    Args:
        event_type: problem, solution, change, decision, note
        severity: high, medium, low
    """
    valid_types = ("problem", "solution", "change", "decision", "note")
    if event_type not in valid_types:
        raise ValidationError(
            field="event_type",
            message=f"Tipos válidos: {', '.join(valid_types)}.",
        )
    valid_severities = ("high", "medium", "low")
    if severity not in valid_severities:
        raise ValidationError(
            field="severity",
            message=f"Severidades válidas: {', '.join(valid_severities)}.",
        )
    if not description or len(description.strip()) < 3:
        raise ValidationError(
            field="description",
            message="La descripción debe tener al menos 3 caracteres.",
        )

    path = _session_path(root_path, session_id)
    session = _load_session(path)

    event = {
        "timestamp": _now_iso(),
        "type": event_type,
        "description": description.strip(),
        "severity": severity,
        "metadata": metadata or {},
    }
    session["events"].append(event)

    if event_type == "problem":
        session["problems_detected"].append(event)
    elif event_type == "solution":
        session["solutions_suggested"].append(event)
    elif event_type == "change":
        session["changes_tracked"].append(event)

    _save_session(path, session)
    return {"event": event, "total_events": len(session["events"])}


def detect_problems(
    root_path: Path,
    session_id: str,
) -> dict[str, Any]:
    """Analiza eventos de sesión e identifica patrones de problemas.

    Detecta:
    - Problemas recurrentes (misma descripción > 1 vez)
    - Problemas de severidad high sin solución
    - Bloqueos (problemas seguidos sin solución)
    """
    path = _session_path(root_path, session_id)
    session = _load_session(path)

    problems = [e for e in session["events"] if e["type"] == "problem"]
    solutions = [e for e in session["events"] if e["type"] == "solution"]

    patterns: list[dict[str, Any]] = []

    # Problemas recurrentes
    desc_count: dict[str, int] = {}
    for p in problems:
        key = p["description"].lower()[:100]
        desc_count[key] = desc_count.get(key, 0) + 1
    for desc, count in desc_count.items():
        if count > 1:
            patterns.append({
                "type": "recurring",
                "description": f"Problema recurrente ({count} veces): {desc[:80]}",
                "severity": "medium",
            })

    # Problemas high sin solución
    high_problems = [p for p in problems if p["severity"] == "high"]
    if len(solutions) < len(high_problems):
        unsolved = len(high_problems) - len(solutions)
        patterns.append({
            "type": "unsolved_high",
            "description": f"{unsolved} problema(s) de severidad alta sin solución",
            "severity": "high",
        })

    # Bloqueos: últimos 3 eventos son problems sin solution intercalada
    if len(session["events"]) >= 3:
        last_events = session["events"][-3:]
        if all(e["type"] == "problem" for e in last_events):
            patterns.append({
                "type": "blockage",
                "description": "Posible bloqueo: 3+ problemas consecutivos sin solución",
                "severity": "high",
            })

    return {
        "session_id": session_id,
        "total_problems": len(problems),
        "total_solutions": len(solutions),
        "patterns_detected": patterns,
    }


def suggest_solutions(
    root_path: Path,
    session_id: str,
) -> dict[str, Any]:
    """Basado en problemas detectados, sugiere soluciones desde historial.

    Busca en sesiones anteriores problemas similares y sus soluciones.
    """
    path = _session_path(root_path, session_id)
    session = _load_session(path)

    problems = [e for e in session["events"] if e["type"] == "problem"]
    if not problems:
        return {"suggestions": [], "message": "No hay problemas registrados en esta sesión."}

    suggestions: list[dict[str, Any]] = []

    sessions_dir = _sessions_dir(root_path)
    if sessions_dir.exists():
        for sf in sessions_dir.glob("*.json"):
            if sf.stem == session_id:
                continue
            try:
                prev = json.loads(sf.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            prev_problems = [e for e in prev.get("events", []) if e["type"] == "problem"]
            prev_solutions = [e for e in prev.get("events", []) if e["type"] == "solution"]

            for pp in prev_problems:
                for curr_p in problems:
                    curr_desc = curr_p["description"].lower()[:60]
                    prev_desc = pp["description"].lower()[:60]
                    if curr_desc and prev_desc and (
                        curr_desc in prev_desc or prev_desc in curr_desc
                    ):
                        for ps in prev_solutions:
                            suggestions.append({
                                "problem": curr_p["description"][:100],
                                "suggested_solution": ps["description"][:200],
                                "source_session": prev.get("session_id", sf.stem),
                            })

    return {
        "session_id": session_id,
        "total_suggestions": len(suggestions),
        "suggestions": suggestions[:10],
    }


def track_change(
    root_path: Path,
    session_id: str,
    file_path: str,
    change_type: str,
    description: str = "",
) -> dict[str, Any]:
    """Registra un cambio durante la sesión.

    Args:
        change_type: add, modify, delete
    """
    valid_types = ("add", "modify", "delete")
    if change_type not in valid_types:
        raise ValidationError(
            field="change_type",
            message=f"Tipos válidos: {', '.join(valid_types)}.",
        )

    return log_session_event(
        root_path,
        session_id,
        "change",
        description or f"{change_type}: {file_path}",
        severity="low",
        metadata={"file": file_path, "change_type": change_type},
    )


def end_session(
    root_path: Path,
    session_id: str,
    summary: str = "",
) -> dict[str, Any]:
    """Cierra sesión y genera bitácora automática.

    Returns:
        Dict con session_id, bitacora_path, stats.
    """
    path = _session_path(root_path, session_id)
    session = _load_session(path)

    if session.get("ended_at"):
        raise ValidationError(
            field="session",
            message="La sesión ya está cerrada.",
        )

    session["ended_at"] = _now_iso()

    problems = [e for e in session["events"] if e["type"] == "problem"]
    solutions = [e for e in session["events"] if e["type"] == "solution"]
    changes = [e for e in session["events"] if e["type"] == "change"]
    decisions = [e for e in session["events"] if e["type"] == "decision"]

    # Generar bitácora en Markdown
    bitacora_dir = root_path / "bitacoras"
    bitacora_dir.mkdir(parents=True, exist_ok=True)
    bitacora_name = f"bitacora-{session_id}.md"
    bitacora_path = bitacora_dir / bitacora_name

    lines: list[str] = [
        "---",
        f'title: "Bitácora {session_id}"',
        "type: bitacora",
        f'project: {session.get("project", "unknown")}',
        f'tags: [session, bitacora, {session.get("project", "")}]'.rstrip(", ]") + "]",
        f'timestamp: {session["ended_at"]}',
        "status: active",
        f'author: {session.get("agent", "unknown")}',
        "---",
        "",
        f"# Bitácora {session_id}",
        "",
        f"**Inicio:** {session['started_at']}",
        f"**Fin:** {session['ended_at']}",
        f"**Proyecto:** {session.get('project', 'N/A')}",
        f"**Contexto:** {session.get('context', 'N/A')}",
        "",
    ]

    if summary:
        lines += ["## Resumen", "", summary, ""]

    if problems:
        lines += ["## Problemas Detectados", ""]
        for p in problems:
            lines.append(f"- **[{p['severity'].upper()}]** {p['description']}")
        lines.append("")

    if solutions:
        lines += ["## Soluciones Aplicadas", ""]
        for s in solutions:
            lines.append(f"- {s['description']}")
        lines.append("")

    if changes:
        lines += ["## Cambios Realizados", ""]
        for c in changes:
            meta = c.get("metadata", {})
            lines.append(f"- **{meta.get('change_type', 'change')}** `{meta.get('file', '?')}` — {c['description']}")
        lines.append("")

    if decisions:
        lines += ["## Decisiones Tomadas", ""]
        for d in decisions:
            lines.append(f"- {d['description']}")
        lines.append("")

    lines += ["## Estadísticas", ""]
    lines.append(f"- Total eventos: {len(session['events'])}")
    lines.append(f"- Problemas: {len(problems)}")
    lines.append(f"- Soluciones: {len(solutions)}")
    lines.append(f"- Cambios: {len(changes)}")
    lines.append(f"- Decisiones: {len(decisions)}")

    bitacora_path.write_text("\n".join(lines), encoding="utf-8")
    session["bitacora_path"] = str(bitacora_path)

    _save_session(path, session)

    return {
        "session_id": session_id,
        "ended_at": session["ended_at"],
        "bitacora_path": str(bitacora_path),
        "stats": {
            "total_events": len(session["events"]),
            "problems": len(problems),
            "solutions": len(solutions),
            "changes": len(changes),
            "decisions": len(decisions),
        },
    }


def get_session_history(
    root_path: Path,
    limit: int = 20,
    project_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Retorna historial de sesiones anteriores."""
    if limit < 1 or limit > 1000:
        raise ValidationError(field="limit", message="El límite debe estar entre 1 y 1000.")

    sessions_dir = _sessions_dir(root_path)
    if not sessions_dir.exists():
        return []

    sessions: list[dict[str, Any]] = []
    for sf in sorted(sessions_dir.glob("*.json"), reverse=True):
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if project_filter and data.get("project") != project_filter:
            continue
        sessions.append({
            "session_id": data.get("session_id", sf.stem),
            "started_at": data.get("started_at"),
            "ended_at": data.get("ended_at"),
            "project": data.get("project"),
            "total_events": len(data.get("events", [])),
            "bitacora_path": data.get("bitacora_path"),
        })
        if len(sessions) >= limit:
            break

    return sessions


def generate_session_report(
    root_path: Path,
    session_id: str,
) -> str:
    """Genera reporte Markdown completo de una sesión específica."""
    path = _session_path(root_path, session_id)
    session = _load_session(path)

    lines: list[str] = [
        f"# Reporte de Sesión {session_id}",
        "",
        f"**Fecha inicio:** {session.get('started_at', 'N/A')}",
        f"**Fecha fin:** {session.get('ended_at', 'Activa')}",
        f"**Proyecto:** {session.get('project', 'N/A')}",
        f"**Contexto:** {session.get('context', 'N/A')}",
        f"**Agente:** {session.get('agent', 'N/A')}",
        "",
    ]

    events = session.get("events", [])
    if events:
        lines += ["## Eventos", "", "| Timestamp | Tipo | Severidad | Descripción |", "|-----------|------|-----------|-------------|"]
        for e in events:
            lines.append(
                f"| {e.get('timestamp', '')} | {e.get('type', '')} | {e.get('severity', '')} | {e.get('description', '')[:80]} |"
            )
        lines.append("")

    problems = [e for e in events if e["type"] == "problem"]
    solutions = [e for e in events if e["type"] == "solution"]
    changes = [e for e in events if e["type"] == "change"]

    lines += ["## Resumen", ""]
    lines.append(f"- Total eventos: {len(events)}")
    lines.append(f"- Problemas: {len(problems)}")
    lines.append(f"- Soluciones: {len(solutions)}")
    lines.append(f"- Cambios: {len(changes)}")
    lines.append(f"- Bitácora: {session.get('bitacora_path', 'No generada')}")

    return "\n".join(lines)
