"""
Lógica de negocio de mcp-project-memory.

Implementa las operaciones de lectura/escritura de la memoria persistente
del proyecto. Sin dependencias de MCP ni FastMCP — 100% testeable.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp_shared.errors import NotFoundError, ValidationError

# ---------------------------------------------------------------------------
# Modelos internos (dicts tipados)
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Retorna el timestamp actual en ISO 8601 UTC."""
    return datetime.now(UTC).isoformat()


def _load_memory(memory_path: Path) -> dict[str, Any]:
    """Carga el archivo de memoria. Retorna estructura vacía si no existe."""
    if not memory_path.exists():
        return _empty_memory()
    try:
        with memory_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise ValidationError(
            field="memory_file",
            message=f"No se pudo leer el archivo de memoria: {exc}",
        ) from exc


def _save_memory(memory_path: Path, memory: dict[str, Any]) -> None:
    """Persiste la memoria en disco. Crea el directorio si no existe."""
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory["_meta"]["last_updated"] = _now_iso()
    try:
        with memory_path.open("w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise ValidationError(
            field="memory_file",
            message=f"No se pudo escribir el archivo de memoria: {exc}",
        ) from exc


def _empty_memory() -> dict[str, Any]:
    """Retorna la estructura base de una memoria vacía."""
    return {
        "_meta": {
            "schema_version": "1.0",
            "created_at": _now_iso(),
            "last_updated": _now_iso(),
        },
        "project": {
            "name": "unknown",
            "description": "",
            "tech_stack": [],
        },
        "components": {},
        "decisions": [],
        "pending_tasks": [],
        "completed_tasks": [],
        "invariants": [],
        "sessions": [],
        "last_session": None,
    }


# ---------------------------------------------------------------------------
# Tools de lectura
# ---------------------------------------------------------------------------


def get_project_state(memory_path: Path) -> dict[str, Any]:
    """
    Retorna el estado completo del proyecto.

    Este es el punto de entrada que un agente de IA debe llamar
    al inicio de cada sesión para recuperar el contexto completo.

    Retorna:
        Dict con: project, components, decisions activas, tareas pendientes,
        invariantes, última sesión y un resumen de sesiones recientes.
    """
    memory = _load_memory(memory_path)
    # Filtrar solo decisiones activas y tareas pendientes para el resumen de inicio
    active_decisions = [d for d in memory.get("decisions", []) if d.get("status") == "active"]
    pending = memory.get("pending_tasks", [])
    recent_sessions = memory.get("sessions", [])[-5:]  # últimas 5 sesiones

    return {
        "project": memory.get("project", {}),
        "components": memory.get("components", {}),
        "active_decisions": active_decisions,
        "pending_tasks": pending,
        "invariants": memory.get("invariants", []),
        "last_session": memory.get("last_session"),
        "recent_sessions": recent_sessions,
        "stats": {
            "total_components": len(memory.get("components", {})),
            "total_decisions": len(memory.get("decisions", [])),
            "pending_tasks_count": len(pending),
            "completed_tasks_count": len(memory.get("completed_tasks", [])),
            "total_sessions": len(memory.get("sessions", [])),
        },
    }


def get_component_map(memory_path: Path) -> dict[str, Any]:
    """
    Retorna el mapa completo de componentes del proyecto.

    Retorna:
        Dict con todos los componentes y sus metadatos (status, version, tools, descripción).
    """
    memory = _load_memory(memory_path)
    return memory.get("components", {})


def get_decisions_history(
    memory_path: Path,
    status_filter: str | None = None,
) -> list[dict[str, Any]]:
    """
    Retorna el historial de decisiones de arquitectura/diseño.

    Args:
        memory_path: Ruta al archivo de memoria.
        status_filter: Filtra por status ('active', 'superseded', 'rejected'). None = todos.

    Retorna:
        Lista de decisiones ordenadas por fecha descendente.
    """
    memory = _load_memory(memory_path)
    decisions = memory.get("decisions", [])
    if status_filter:
        if status_filter not in ("active", "superseded", "rejected"):
            raise ValidationError(
                field="status_filter",
                message="Valores válidos: 'active', 'superseded', 'rejected'.",
            )
        decisions = [d for d in decisions if d.get("status") == status_filter]
    return sorted(decisions, key=lambda d: d.get("date", ""), reverse=True)


def get_session_history(
    memory_path: Path,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Retorna el historial de sesiones registradas.

    Args:
        memory_path: Ruta al archivo de memoria.
        limit: Máximo de sesiones a retornar (más recientes primero).

    Retorna:
        Lista de sesiones ordenadas por fecha descendente.
    """
    if limit < 1 or limit > 1000:
        raise ValidationError(field="limit", message="El límite debe estar entre 1 y 1000.")
    memory = _load_memory(memory_path)
    sessions = memory.get("sessions", [])
    return list(reversed(sessions[-limit:]))


def generate_project_brief(memory_path: Path) -> str:
    """
    Genera un resumen ejecutivo del proyecto en Markdown.

    Diseñado para ser el primer mensaje que un agente lee al iniciar
    una nueva sesión cuando no tiene contexto previo.

    Retorna:
        String en formato Markdown con el resumen completo del proyecto.
    """
    memory = _load_memory(memory_path)
    project = memory.get("project", {})
    components = memory.get("components", {})
    decisions = [d for d in memory.get("decisions", []) if d.get("status") == "active"]
    pending = memory.get("pending_tasks", [])
    last_session = memory.get("last_session")
    invariants = memory.get("invariants", [])

    lines: list[str] = [
        f"# {project.get('name', 'Proyecto')} — Brief de Sesión",
        f"*Generado: {_now_iso()}*",
        "",
        "## Descripción",
        project.get("description", "Sin descripción."),
        "",
    ]

    if project.get("tech_stack"):
        lines += ["## Stack Tecnológico", ", ".join(project["tech_stack"]), ""]

    lines += ["## Componentes", ""]
    if components:
        for name, comp in components.items():
            status_emoji = {"ready": "✅", "draft": "🚧", "deprecated": "❌"}.get(
                comp.get("status", ""), "❓"
            )
            lines.append(
                f"- {status_emoji} **{name}** v{comp.get('version', '?')} — "
                f"{comp.get('description', '')} | {comp.get('tools', '?')} tools"
            )
    else:
        lines.append("_Sin componentes registrados._")

    lines += ["", "## Decisiones Activas", ""]
    if decisions:
        for d in decisions[:10]:
            lines.append(f"- **[{d['id']}]** {d['title']} _{d.get('date', '')}_ ")
    else:
        lines.append("_Sin decisiones registradas._")

    lines += ["", "## Tareas Pendientes", ""]
    if pending:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_pending = sorted(
            pending, key=lambda t: priority_order.get(t.get("priority", "low"), 2)
        )
        for t in sorted_pending[:10]:
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(t.get("priority", "low"), "⚪")
            lines.append(f"- {emoji} **[{t['id']}]** {t['title']}")
    else:
        lines.append("_Sin tareas pendientes._")

    if invariants:
        lines += ["", "## Invariantes del Proyecto", ""]
        for inv in invariants:
            lines.append(f"- {inv}")

    if last_session:
        lines += [
            "",
            "## Última Sesión",
            f"- **Fecha:** {last_session.get('date', 'desconocida')}",
            f"- **Resumen:** {last_session.get('summary', 'Sin resumen.')}",
            f"- **Cambios:** {', '.join(last_session.get('changes_made', [])[:5]) or 'Ninguno registrado.'}",
        ]

    return "\n".join(lines)


def search_memory(
    memory_path: Path,
    query: str,
) -> dict[str, list[dict[str, Any]]]:
    """
    Búsqueda simple de texto en toda la memoria del proyecto.

    Args:
        memory_path: Ruta al archivo de memoria.
        query: Texto a buscar (case-insensitive).

    Retorna:
        Dict con resultados agrupados por categoría (decisions, tasks, sessions, invariants).
    """
    if not query or len(query) < 2:
        raise ValidationError(
            field="query", message="La consulta debe tener al menos 2 caracteres."
        )

    memory = _load_memory(memory_path)
    q = query.lower()
    results: dict[str, list[dict[str, Any]]] = {
        "decisions": [],
        "tasks": [],
        "sessions": [],
        "invariants": [],
    }

    for d in memory.get("decisions", []):
        if q in json.dumps(d, ensure_ascii=False).lower():
            results["decisions"].append(d)

    for t in memory.get("pending_tasks", []) + memory.get("completed_tasks", []):
        if q in json.dumps(t, ensure_ascii=False).lower():
            results["tasks"].append(t)

    for s in memory.get("sessions", []):
        if q in json.dumps(s, ensure_ascii=False).lower():
            results["sessions"].append(s)

    for inv in memory.get("invariants", []):
        if q in inv.lower():
            results["invariants"].append({"text": inv})

    return results


def diff_state(
    memory_path: Path,
    session_id: str,
) -> dict[str, Any]:
    """
    Compara el estado actual con el estado al finalizar una sesión anterior.

    Args:
        memory_path: Ruta al archivo de memoria.
        session_id: ID de la sesión contra la que comparar.

    Retorna:
        Dict con componentes nuevos, decisiones nuevas, tareas completadas desde esa sesión.
    """
    memory = _load_memory(memory_path)
    sessions = memory.get("sessions", [])
    target_session = next((s for s in sessions if s.get("id") == session_id), None)
    if not target_session:
        raise NotFoundError(resource="session", identifier=session_id)

    session_date = target_session.get("date", "")

    new_decisions = [d for d in memory.get("decisions", []) if d.get("date", "") > session_date]
    completed_since = [
        t for t in memory.get("completed_tasks", []) if t.get("completed_at", "") > session_date
    ]
    snapshot_components = target_session.get("components_snapshot", {})
    current_components = memory.get("components", {})
    new_components = [k for k in current_components if k not in snapshot_components]
    changed_components = [
        k
        for k, v in current_components.items()
        if k in snapshot_components and v.get("version") != snapshot_components[k].get("version")
    ]

    return {
        "compared_to_session": session_id,
        "session_date": session_date,
        "new_components": new_components,
        "changed_components": changed_components,
        "new_decisions": new_decisions,
        "completed_tasks_since": completed_since,
    }


# ---------------------------------------------------------------------------
# Tools de escritura
# ---------------------------------------------------------------------------


def snapshot_session(
    memory_path: Path,
    summary: str,
    changes_made: list[str],
    decisions_taken: int = 0,
    tasks_completed: int = 0,
    agent: str = "unknown",
) -> dict[str, Any]:
    """
    Guarda un snapshot de la sesión actual.

    Debe llamarse al finalizar una sesión de trabajo para que
    el agente pueda retomar el contexto en la próxima sesión.

    Args:
        memory_path: Ruta al archivo de memoria.
        summary: Resumen textual de lo que se hizo en la sesión.
        changes_made: Lista de archivos/componentes modificados.
        decisions_taken: Número de decisiones registradas en esta sesión.
        tasks_completed: Número de tareas completadas en esta sesión.
        agent: Identificador del agente que realizó la sesión.

    Retorna:
        Dict con el ID asignado a la sesión y metadatos.
    """
    if not summary or len(summary.strip()) < 10:
        raise ValidationError(
            field="summary", message="El resumen debe tener al menos 10 caracteres."
        )

    memory = _load_memory(memory_path)
    sessions = memory.setdefault("sessions", [])

    session_id = f"SES-{len(sessions) + 1:04d}"
    now = _now_iso()

    session = {
        "id": session_id,
        "date": now,
        "summary": summary.strip(),
        "changes_made": changes_made,
        "decisions_taken": decisions_taken,
        "tasks_completed": tasks_completed,
        "agent": agent,
        "components_snapshot": dict(memory.get("components", {})),
    }

    sessions.append(session)
    memory["last_session"] = session

    _save_memory(memory_path, memory)
    return {"session_id": session_id, "date": now, "status": "saved"}


def update_component_status(
    memory_path: Path,
    component_name: str,
    status: str,
    version: str | None = None,
    description: str | None = None,
    tools: int | None = None,
    port: int | None = None,
) -> dict[str, Any]:
    """
    Actualiza o registra un componente del proyecto en la memoria.

    Args:
        memory_path: Ruta al archivo de memoria.
        component_name: Nombre del componente (ej: 'mcp-tabular').
        status: Estado del componente: 'draft', 'ready', 'deprecated'.
        version: Versión del componente (ej: '1.0.0').
        description: Descripción breve del componente.
        tools: Número de tools que expone.
        port: Puerto HTTP en modo streamable-http.

    Retorna:
        Dict con el componente actualizado.
    """
    valid_statuses = ("draft", "ready", "deprecated")
    if status not in valid_statuses:
        raise ValidationError(
            field="status",
            message=f"Status válidos: {', '.join(valid_statuses)}.",
        )

    memory = _load_memory(memory_path)
    components = memory.setdefault("components", {})

    existing = components.get(component_name, {})
    updated = {
        **existing,
        "status": status,
        "last_updated": _now_iso(),
    }
    if version is not None:
        updated["version"] = version
    if description is not None:
        updated["description"] = description
    if tools is not None:
        updated["tools"] = tools
    if port is not None:
        updated["port"] = port

    components[component_name] = updated
    _save_memory(memory_path, memory)
    return {component_name: updated}


def record_decision(
    memory_path: Path,
    title: str,
    rationale: str,
    alternatives_rejected: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """
    Registra una decisión de arquitectura o diseño en la memoria.

    Args:
        memory_path: Ruta al archivo de memoria.
        title: Título conciso de la decisión (ej: 'FastMCP como framework base').
        rationale: Justificación detallada de la decisión.
        alternatives_rejected: Alternativas que se evaluaron y se descartaron.
        tags: Etiquetas para categorizar (ej: ['arquitectura', 'seguridad']).

    Retorna:
        Dict con el ID asignado y los datos de la decisión.
    """
    if not title or len(title.strip()) < 5:
        raise ValidationError(field="title", message="El título debe tener al menos 5 caracteres.")
    if not rationale or len(rationale.strip()) < 10:
        raise ValidationError(
            field="rationale", message="El razonamiento debe tener al menos 10 caracteres."
        )

    memory = _load_memory(memory_path)
    decisions = memory.setdefault("decisions", [])

    decision_id = f"DEC-{len(decisions) + 1:04d}"
    decision = {
        "id": decision_id,
        "date": _now_iso(),
        "title": title.strip(),
        "rationale": rationale.strip(),
        "alternatives_rejected": alternatives_rejected or [],
        "tags": tags or [],
        "status": "active",
    }
    decisions.append(decision)
    _save_memory(memory_path, memory)
    return decision


def add_pending_task(
    memory_path: Path,
    title: str,
    context: str = "",
    priority: str = "medium",
) -> dict[str, Any]:
    """
    Agrega una tarea pendiente a la memoria del proyecto.

    Args:
        memory_path: Ruta al archivo de memoria.
        title: Descripción corta de la tarea.
        context: Contexto adicional o detalles de implementación.
        priority: Prioridad de la tarea: 'high', 'medium', 'low'.

    Retorna:
        Dict con el ID asignado y los datos de la tarea.
    """
    valid_priorities = ("high", "medium", "low")
    if priority not in valid_priorities:
        raise ValidationError(
            field="priority",
            message=f"Prioridades válidas: {', '.join(valid_priorities)}.",
        )
    if not title or len(title.strip()) < 3:
        raise ValidationError(field="title", message="El título debe tener al menos 3 caracteres.")

    memory = _load_memory(memory_path)
    tasks = memory.setdefault("pending_tasks", [])
    all_tasks = tasks + memory.get("completed_tasks", [])

    task_id = f"TASK-{len(all_tasks) + 1:04d}"
    task = {
        "id": task_id,
        "title": title.strip(),
        "context": context.strip(),
        "priority": priority,
        "created_at": _now_iso(),
        "status": "pending",
    }
    tasks.append(task)
    _save_memory(memory_path, memory)
    return task


def complete_pending_task(
    memory_path: Path,
    task_id: str,
    resolution: str = "",
) -> dict[str, Any]:
    """
    Marca una tarea pendiente como completada.

    Args:
        memory_path: Ruta al archivo de memoria.
        task_id: ID de la tarea a completar (ej: 'TASK-0001').
        resolution: Descripción de cómo se resolvió la tarea.

    Retorna:
        Dict con la tarea completada.
    """
    memory = _load_memory(memory_path)
    pending = memory.setdefault("pending_tasks", [])
    completed = memory.setdefault("completed_tasks", [])

    task = next((t for t in pending if t["id"] == task_id), None)
    if not task:
        raise NotFoundError(resource="pending_task", identifier=task_id)

    pending.remove(task)
    task["status"] = "completed"
    task["completed_at"] = _now_iso()
    task["resolution"] = resolution.strip()
    completed.append(task)
    _save_memory(memory_path, memory)
    return task


def initialize_project(
    memory_path: Path,
    project_name: str,
    description: str,
    tech_stack: list[str] | None = None,
    invariants: list[str] | None = None,
) -> dict[str, Any]:
    """
    Inicializa (o reinicializa) la memoria del proyecto con datos base.

    Idempotente: si la memoria ya existe, actualiza los campos provistos
    sin eliminar decisiones, tareas ni sesiones existentes.

    Args:
        memory_path: Ruta al archivo de memoria.
        project_name: Nombre del proyecto.
        description: Descripción del proyecto.
        tech_stack: Lista de tecnologías del stack.
        invariants: Reglas invariantes del proyecto (nunca deben violarse).

    Retorna:
        Dict con los datos del proyecto inicializados.
    """
    if not project_name or len(project_name.strip()) < 2:
        raise ValidationError(
            field="project_name", message="El nombre debe tener al menos 2 caracteres."
        )

    memory = _load_memory(memory_path)
    memory["project"] = {
        "name": project_name.strip(),
        "description": description.strip(),
        "tech_stack": tech_stack or [],
    }
    if invariants is not None:
        memory["invariants"] = [i.strip() for i in invariants if i.strip()]

    _save_memory(memory_path, memory)
    return memory["project"]


def sync_from_filesystem(
    memory_path: Path,
    project_root: Path,
) -> dict[str, Any]:
    """
    Escanea el filesystem del proyecto y sincroniza los componentes detectados.

    Detecta directorios que siguen el patrón 'mcp-*' y los registra/actualiza
    en la memoria como componentes con status 'draft' si no existen.
    No elimina componentes existentes en la memoria.

    Args:
        memory_path: Ruta al archivo de memoria.
        project_root: Directorio raíz del proyecto.

    Retorna:
        Dict con lista de componentes nuevos detectados y total de componentes.
    """
    if not project_root.exists():
        raise NotFoundError(resource="project_root", identifier=str(project_root))

    memory = _load_memory(memory_path)
    components = memory.setdefault("components", {})

    # Detectar directorios mcp-*
    detected = []
    new_components = []
    for entry in sorted(project_root.iterdir()):
        if entry.is_dir() and entry.name.startswith("mcp-") and not entry.name.startswith("."):
            detected.append(entry.name)
            if entry.name not in components:
                # Intenta leer la versión del pyproject.toml
                pyproject = entry / "pyproject.toml"
                version = "0.1.0"
                if pyproject.exists():
                    content = pyproject.read_text(encoding="utf-8")
                    for line in content.splitlines():
                        if line.strip().startswith("version"):
                            version = line.split("=")[1].strip().strip('"')
                            break

                components[entry.name] = {
                    "status": "draft",
                    "version": version,
                    "description": "Servidor MCP detectado automáticamente",
                    "tools": 0,
                    "last_updated": _now_iso(),
                }
                new_components.append(entry.name)

    _save_memory(memory_path, memory)
    return {
        "detected_on_filesystem": detected,
        "new_components_added": new_components,
        "total_components": len(components),
    }


def export_memory_snapshot(memory_path: Path) -> dict[str, Any]:
    """
    Exporta toda la memoria del proyecto tal como está en disco.

    Retorna:
        El contenido completo del archivo de memoria como dict.
    """
    return _load_memory(memory_path)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def get_pending_tasks(memory_path: Path, priority: str | None = None) -> list[dict[str, Any]]:
    """Retorna las tareas pendientes, opcionalmente filtradas por prioridad."""
    memory = _load_memory(memory_path)
    tasks = memory.get("pending_tasks", [])
    if priority:
        valid = ("high", "medium", "low")
        if priority not in valid:
            raise ValidationError(
                field="priority", message=f"Prioridades validas: {', '.join(valid)}."
            )
        tasks = [t for t in tasks if t.get("priority") == priority]
    priority_order = {"high": 0, "medium": 1, "low": 2}
    return sorted(tasks, key=lambda t: priority_order.get(t.get("priority", "low"), 2))


def get_completed_tasks(memory_path: Path, limit: int = 50) -> list[dict[str, Any]]:
    """Retorna las tareas completadas, mas recientes primero."""
    if limit < 1 or limit > 1000:
        raise ValidationError(field="limit", message="El limite debe estar entre 1 y 1000.")
    memory = _load_memory(memory_path)
    tasks = memory.get("completed_tasks", [])
    return list(reversed(tasks[-limit:]))


def get_invariants(memory_path: Path) -> list[str]:
    """Retorna la lista de invariantes del proyecto."""
    memory = _load_memory(memory_path)
    return memory.get("invariants", [])


def add_invariant(memory_path: Path, invariant: str) -> dict[str, Any]:
    """Agrega una invariante al proyecto."""
    if not invariant or len(invariant.strip()) < 5:
        raise ValidationError(
            field="invariant", message="La invariante debe tener al menos 5 caracteres."
        )
    memory = _load_memory(memory_path)
    invariants = memory.setdefault("invariants", [])
    text = invariant.strip()
    if text not in invariants:
        invariants.append(text)
        _save_memory(memory_path, memory)
    return {"invariants": invariants, "added": text}


def get_memory_stats(memory_path: Path) -> dict[str, Any]:
    """Retorna estadisticas resumidas de la memoria del proyecto."""
    memory = _load_memory(memory_path)
    components = memory.get("components", {})
    by_status: dict[str, int] = {}
    for c in components.values():
        s = c.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
    decisions = memory.get("decisions", [])
    active_decisions = sum(1 for d in decisions if d.get("status") == "active")
    pending = memory.get("pending_tasks", [])
    completed = memory.get("completed_tasks", [])
    sessions = memory.get("sessions", [])
    return {
        "total_components": len(components),
        "components_by_status": by_status,
        "total_decisions": len(decisions),
        "active_decisions": active_decisions,
        "pending_tasks": len(pending),
        "completed_tasks": len(completed),
        "total_sessions": len(sessions),
        "invariants_count": len(memory.get("invariants", [])),
        "last_updated": memory.get("_meta", {}).get("last_updated"),
    }
