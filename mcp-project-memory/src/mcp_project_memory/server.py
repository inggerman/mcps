"""
Servidor FastMCP para mcp-project-memory.

Expone 15 herramientas para mantener memoria persistente del proyecto
y permitir que agentes de IA retomen el contexto en cualquier sesión.

Transporte: stdio (Claude Desktop, Cursor) o streamable-http (Docker).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_project_memory import __version__
from mcp_project_memory.config import settings
from mcp_project_memory.tools.memory_tools import (
    add_invariant,
    add_pending_task,
    complete_pending_task,
    diff_state,
    export_memory_snapshot,
    generate_project_brief,
    get_completed_tasks,
    get_component_map,
    get_decisions_history,
    get_invariants,
    get_memory_stats,
    get_pending_tasks,
    get_project_state,
    get_session_history,
    initialize_project,
    record_decision,
    search_memory,
    snapshot_session,
    sync_from_filesystem,
    update_component_status,
)
from mcp_project_memory import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-project-memory",
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Ciclo de vida del servidor: crea directorio de memoria si no existe."""
    structlog.contextvars.bind_contextvars(server_name="mcp-project-memory")
    memory_path = settings.memory_path
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        "mcp-project-memory iniciando",
        version=__version__,
        memory_path=str(memory_path),
        project_name=settings.project_name,
    )
    yield
    logger.info("mcp-project-memory detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-project-memory",
    instructions=(
        "Servidor MCP para mantener memoria persistente del proyecto entre sesiones de IA. "
        "Llama get_project_state al inicio de cada sesión para recuperar el contexto completo. "
        "Llama snapshot_session al finalizar para guardar lo realizado. "
        "Usa record_decision para registrar decisiones arquitectónicas importantes. "
        "Usa add_pending_task/complete_pending_task para gestionar el backlog."
    ),
    lifespan=lifespan,
)

# Ruta de memoria resuelta una vez (usada por todos los tools)
_MEMORY_PATH: Path = settings.memory_path


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Wrapper de manejo de errores estándar del proyecto."""
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__, error=str(exc))
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Tools de lectura
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_project_state",
    description=(
        "Retorna el estado completo del proyecto: componentes, decisiones activas, "
        "tareas pendientes, invariantes y resumen de la última sesión. "
        "LLAMA ESTE TOOL AL INICIO DE CADA SESIÓN para recuperar el contexto completo."
    ),
)
def tool_get_project_state() -> dict[str, Any]:
    logger.info("get_project_state llamado")
    return _handle(get_project_state, _MEMORY_PATH)


@mcp.tool(
    name="generate_project_brief",
    description=(
        "Genera un resumen ejecutivo del proyecto en Markdown. "
        "Ideal para iniciar una nueva sesión con un agente que no tiene contexto previo."
    ),
)
def tool_generate_project_brief() -> str:
    logger.info("generate_project_brief llamado")
    return _handle(generate_project_brief, _MEMORY_PATH)


@mcp.tool(
    name="get_component_map",
    description=(
        "Retorna el mapa de todos los componentes del proyecto "
        "con su estado, versión, número de tools y descripción."
    ),
)
def tool_get_component_map() -> dict[str, Any]:
    logger.info("get_component_map llamado")
    return _handle(get_component_map, _MEMORY_PATH)


@mcp.tool(
    name="get_decisions_history",
    description=(
        "Retorna el historial de decisiones de arquitectura y diseño. "
        "Parámetro opcional status_filter: 'active', 'superseded' o 'rejected'."
    ),
)
def tool_get_decisions_history(status_filter: str | None = None) -> list[dict[str, Any]]:
    logger.info("get_decisions_history llamado", status_filter=status_filter)
    return _handle(get_decisions_history, _MEMORY_PATH, status_filter)


@mcp.tool(
    name="get_session_history",
    description=(
        "Retorna el historial de sesiones de trabajo registradas, "
        "ordenadas de más reciente a más antigua. "
        "Parámetro limit: máximo de sesiones a retornar (default 20)."
    ),
)
def tool_get_session_history(limit: int = 20) -> list[dict[str, Any]]:
    logger.info("get_session_history llamado", limit=limit)
    return _handle(get_session_history, _MEMORY_PATH, limit)


@mcp.tool(
    name="search_memory",
    description=(
        "Búsqueda de texto en toda la memoria del proyecto: "
        "decisiones, tareas, sesiones e invariantes. "
        "Parámetro query: texto a buscar (mínimo 2 caracteres)."
    ),
)
def tool_search_memory(query: str) -> dict[str, list[dict[str, Any]]]:
    logger.info("search_memory llamado", query=query)
    return _handle(search_memory, _MEMORY_PATH, query)


@mcp.tool(
    name="diff_state",
    description=(
        "Compara el estado actual del proyecto con el estado al finalizar "
        "una sesión anterior. Muestra componentes nuevos, decisiones tomadas "
        "y tareas completadas desde esa sesión. "
        "Parámetro session_id: ID de la sesión a comparar (ej: 'SES-0003')."
    ),
)
def tool_diff_state(session_id: str) -> dict[str, Any]:
    logger.info("diff_state llamado", session_id=session_id)
    return _handle(diff_state, _MEMORY_PATH, session_id)


@mcp.tool(
    name="export_memory_snapshot",
    description=(
        "Exporta toda la memoria del proyecto como JSON estructurado. "
        "Útil para backup, migración o inspección completa del estado."
    ),
)
def tool_export_memory_snapshot() -> dict[str, Any]:
    logger.info("export_memory_snapshot llamado")
    return _handle(export_memory_snapshot, _MEMORY_PATH)


# ---------------------------------------------------------------------------
# Tools de escritura
# ---------------------------------------------------------------------------


@mcp.tool(
    name="snapshot_session",
    description=(
        "Guarda un snapshot de la sesión de trabajo actual. "
        "LLAMA ESTE TOOL AL FINALIZAR CADA SESIÓN para preservar el contexto. "
        "Parámetros: summary (resumen de lo hecho), changes_made (lista de archivos/componentes "
        "modificados), decisions_taken (int), tasks_completed (int), agent (nombre del agente)."
    ),
)
def tool_snapshot_session(
    summary: str,
    changes_made: list[str],
    decisions_taken: int = 0,
    tasks_completed: int = 0,
    agent: str = "unknown",
) -> dict[str, Any]:
    logger.info("snapshot_session llamado", agent=agent, changes=len(changes_made))
    return _handle(
        snapshot_session,
        _MEMORY_PATH,
        summary,
        changes_made,
        decisions_taken,
        tasks_completed,
        agent,
    )


@mcp.tool(
    name="update_component_status",
    description=(
        "Actualiza o registra un componente del proyecto. "
        "Parámetros: component_name (ej: 'mcp-tabular'), "
        "status ('draft'|'ready'|'deprecated'), "
        "version (ej: '1.0.0'), description (str), tools (int), port (int)."
    ),
)
def tool_update_component_status(
    component_name: str,
    status: str,
    version: str | None = None,
    description: str | None = None,
    tools: int | None = None,
    port: int | None = None,
) -> dict[str, Any]:
    logger.info("update_component_status llamado", component=component_name, status=status)
    return _handle(
        update_component_status,
        _MEMORY_PATH,
        component_name,
        status,
        version,
        description,
        tools,
        port,
    )


@mcp.tool(
    name="record_decision",
    description=(
        "Registra una decisión de arquitectura o diseño con su justificación. "
        "Parámetros: title (título conciso), rationale (justificación), "
        "alternatives_rejected (lista de alternativas descartadas), "
        "tags (lista de etiquetas)."
    ),
)
def tool_record_decision(
    title: str,
    rationale: str,
    alternatives_rejected: list[str] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    logger.info("record_decision llamado", title=title)
    return _handle(record_decision, _MEMORY_PATH, title, rationale, alternatives_rejected, tags)


@mcp.tool(
    name="add_pending_task",
    description=(
        "Agrega una tarea pendiente al backlog del proyecto. "
        "Parámetros: title (descripción corta), context (detalles), "
        "priority ('high'|'medium'|'low')."
    ),
)
def tool_add_pending_task(
    title: str,
    context: str = "",
    priority: str = "medium",
) -> dict[str, Any]:
    logger.info("add_pending_task llamado", title=title, priority=priority)
    return _handle(add_pending_task, _MEMORY_PATH, title, context, priority)


@mcp.tool(
    name="complete_pending_task",
    description=(
        "Marca una tarea pendiente como completada. "
        "Parámetros: task_id (ej: 'TASK-0001'), resolution (cómo se resolvió)."
    ),
)
def tool_complete_pending_task(
    task_id: str,
    resolution: str = "",
) -> dict[str, Any]:
    logger.info("complete_pending_task llamado", task_id=task_id)
    return _handle(complete_pending_task, _MEMORY_PATH, task_id, resolution)


@mcp.tool(
    name="initialize_project",
    description=(
        "Inicializa o actualiza los datos base del proyecto en la memoria. "
        "Idempotente: no borra sesiones ni decisiones existentes. "
        "Parámetros: project_name, description, tech_stack (lista), "
        "invariants (reglas que nunca deben violarse)."
    ),
)
def tool_initialize_project(
    project_name: str,
    description: str,
    tech_stack: list[str] | None = None,
    invariants: list[str] | None = None,
) -> dict[str, Any]:
    logger.info("initialize_project llamado", project_name=project_name)
    return _handle(
        initialize_project, _MEMORY_PATH, project_name, description, tech_stack, invariants
    )


@mcp.tool(
    name="sync_from_filesystem",
    description=(
        "Escanea el filesystem del proyecto y registra automáticamente "
        "los directorios 'mcp-*' detectados como componentes en la memoria. "
        "No elimina componentes existentes. "
        "Parámetro project_root: ruta raíz del proyecto (default: directorio actual)."
    ),
)
def tool_sync_from_filesystem(project_root: str = ".") -> dict[str, Any]:
    root = Path(project_root).resolve()
    logger.info("sync_from_filesystem llamado", project_root=str(root))
    return _handle(sync_from_filesystem, _MEMORY_PATH, root)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="get_pending_tasks",
    description="Retorna las tareas pendientes, opcionalmente filtradas por prioridad.",
)
def tool_get_pending_tasks(priority: str | None = None) -> list[dict[str, Any]]:
    logger.info("get_pending_tasks llamado", priority=priority)
    return _handle(get_pending_tasks, _MEMORY_PATH, priority)


@mcp.tool(
    name="get_completed_tasks",
    description="Retorna las tareas completadas, mas recientes primero.",
)
def tool_get_completed_tasks(limit: int = 50) -> list[dict[str, Any]]:
    logger.info("get_completed_tasks llamado", limit=limit)
    return _handle(get_completed_tasks, _MEMORY_PATH, limit)


@mcp.tool(
    name="get_invariants",
    description="Retorna la lista de invariantes del proyecto.",
)
def tool_get_invariants() -> list[str]:
    logger.info("get_invariants llamado")
    return _handle(get_invariants, _MEMORY_PATH)


@mcp.tool(
    name="add_invariant",
    description="Agrega una invariante al proyecto.",
)
def tool_add_invariant(invariant: str) -> dict[str, Any]:
    logger.info("add_invariant llamado")
    return _handle(add_invariant, _MEMORY_PATH, invariant)


@mcp.tool(
    name="get_memory_stats",
    description="Retorna estadisticas resumidas de la memoria del proyecto.",
)
def tool_get_memory_stats() -> dict[str, Any]:
    logger.info("get_memory_stats llamado")
    return _handle(get_memory_stats, _MEMORY_PATH)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("project-memory://configuration")
def res_config() -> str:
    return res.project_memory_configuration()


@mcp.resource("project-memory://schema-reference")
def res_schema() -> str:
    return res.memory_schema_reference()


@mcp.resource("project-memory://component-statuses")
def res_statuses() -> str:
    return res.component_statuses_reference()


@mcp.resource("project-memory://task-priorities")
def res_priorities() -> str:
    return res.task_priorities_reference()


@mcp.resource("project-memory://decision-statuses")
def res_decision_statuses() -> str:
    return res.decision_statuses_reference()


@mcp.resource("project-memory://session-workflow")
def res_workflow() -> str:
    return res.session_workflow_guide()


@mcp.resource("project-memory://best-practices")
def res_best_practices() -> str:
    return res.memory_best_practices()


@mcp.resource("project-memory://search-tips")
def res_search_tips() -> str:
    return res.memory_search_tips()


@mcp.resource("project-memory://common-workflows")
def res_workflows() -> str:
    return res.common_memory_workflows()


@mcp.resource("project-memory://error-codes")
def res_errors() -> str:
    return res.memory_error_codes()


@mcp.resource("project-memory://file-format")
def res_file_format() -> str:
    return res.memory_file_format()


@mcp.resource("project-memory://invariant-guide")
def res_invariant_guide() -> str:
    return res.invariant_guide()


@mcp.resource("project-memory://examples/get-project-state")
def res_example_state() -> str:
    return res.example_get_project_state()


@mcp.resource("project-memory://examples/snapshot-session")
def res_example_snapshot() -> str:
    return res.example_snapshot_session()


@mcp.resource("project-memory://examples/record-decision")
def res_example_decision() -> str:
    return res.example_record_decision()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
