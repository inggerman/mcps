"""Resources de solo lectura para mcp-project-memory.

Expone metadatos, guias y consejos sobre la memoria del proyecto
como URIs accesibles para el modelo a traves de `@mcp.resource`.
"""

from __future__ import annotations

import json

from mcp_project_memory.config import settings


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


def project_memory_configuration() -> str:
    """Configuracion actual del servidor project-memory."""
    return json.dumps(
        {
            "project_name": settings.project_name,
            "memory_dir": str(settings.memory_dir),
            "memory_file": settings.memory_file,
            "auto_sync": settings.auto_sync,
            "max_sessions": settings.max_sessions,
        },
        indent=2,
        ensure_ascii=False,
    )


def memory_schema_reference() -> str:
    """Estructura del archivo JSON de memoria."""
    return (
        "# Estructura de project_memory.json\n\n"
        "```json\n"
        "{\n"
        "  \"_meta\": { \"schema_version\": \"1.0\", \"created_at\": \"...\", \"last_updated\": \"...\" },\n"
        "  \"project\": { \"name\": \"...\", \"description\": \"...\", \"tech_stack\": [] },\n"
        "  \"components\": { \"mcp-tabular\": { \"status\": \"ready\", \"version\": \"1.0.0\", ... } },\n"
        "  \"decisions\": [ { \"id\": \"DEC-0001\", \"title\": \"...\", \"rationale\": \"...\", \"status\": \"active\" } ],\n"
        "  \"pending_tasks\": [ { \"id\": \"TASK-0001\", \"title\": \"...\", \"priority\": \"high\" } ],\n"
        "  \"completed_tasks\": [ { \"id\": \"TASK-0001\", \"title\": \"...\", \"resolution\": \"...\" } ],\n"
        "  \"invariants\": [ \"La logica de negocio nunca importa de fastmcp\" ],\n"
        "  \"sessions\": [ { \"id\": \"SES-0001\", \"summary\": \"...\", \"changes_made\": [] } ],\n"
        "  \"last_session\": { \"id\": \"SES-0001\", ... }\n"
        "}\n"
        "```"
    )


def component_statuses_reference() -> str:
    """Estados validos para componentes."""
    return (
        "# Estados de componentes\n\n"
        "| Estado | Descripcion | Emoji |\n"
        "|--------|-------------|-------|\n"
        "| draft | En desarrollo | 🚧 |\n"
        "| ready | Listo para produccion | ✅ |\n"
        "| deprecated | Obsoleto | ❌ |"
    )


def task_priorities_reference() -> str:
    """Prioridades validas para tareas."""
    return (
        "# Prioridades de tareas\n\n"
        "| Prioridad | Descripcion | Emoji |\n"
        "|-----------|-------------|-------|\n"
        "| high | Urgente, bloquea progreso | 🔴 |\n"
        "| medium | Importante pero no bloqueante | 🟡 |\n"
        "| low | Mejora opcional | 🟢 |"
    )


def decision_statuses_reference() -> str:
    """Estados validos para decisiones."""
    return (
        "# Estados de decisiones\n\n"
        "| Estado | Descripcion |\n"
        "|--------|-------------|\n"
        "| active | Decision vigente |\n"
        "| superseded | Reemplazada por otra decision |\n"
        "| rejected | Descartada |\n"
        "\n"
        "Usa get_decisions_history(status_filter='active') para filtrar."
    )


def session_workflow_guide() -> str:
    """Guia del flujo de trabajo por sesion."""
    return (
        "# Flujo de trabajo por sesion\n\n"
        "## Inicio de sesion\n"
        "1. Llama get_project_state() para recuperar el contexto completo\n"
        "2. Revisa las tareas pendientes y decisiones activas\n"
        "3. Usa generate_project_brief() si necesitas un resumen ejecutivo\n\n"
        "## Durante la sesion\n"
        "- Usa record_decision() para decisiones importantes\n"
        "- Usa add_pending_task() para nuevas tareas\n"
        "- Usa update_component_status() al cambiar componentes\n"
        "- Usa complete_pending_task() al terminar tareas\n\n"
        "## Fin de sesion\n"
        "1. Llama snapshot_session() con un resumen de lo hecho\n"
        "2. Incluye changes_made (lista de archivos/componentes modificados)\n"
        "3. Especifica decisions_taken y tasks_completed"
    )


def memory_best_practices() -> str:
    """Mejores practicas para la memoria del proyecto."""
    return (
        "# Mejores practicas de memoria\n\n"
        "- Llama get_project_state() al inicio de cada sesion\n"
        "- Llama snapshot_session() al finalizar cada sesion\n"
        "- Registra decisiones importantes con record_decision()\n"
        "- Manten las invariantes actualizadas con initialize_project()\n"
        "- Usa search_memory() para buscar texto en toda la memoria\n"
        "- Usa diff_state() para comparar el estado actual con una sesion anterior\n"
        "- Usa sync_from_filesystem() para detectar nuevos componentes automaticamente"
    )


def memory_search_tips() -> str:
    """Consejos de busqueda en la memoria."""
    return (
        "# Busqueda en memoria\n\n"
        "- search_memory(query) busca en decisiones, tareas, sesiones e invariantes\n"
        "- La busqueda es case-insensitive\n"
        "- El query debe tener al menos 2 caracteres\n"
        "- Los resultados se agrupan por categoria\n"
        "- Usa diff_state(session_id) para ver cambios desde una sesion especifica"
    )


def common_memory_workflows() -> str:
    """Flujos de trabajo comunes con la memoria."""
    return (
        "# Flujos comunes\n\n"
        "- **Iniciar**: get_project_state()\n"
        "- **Brief**: generate_project_brief()\n"
        "- **Componentes**: get_component_map()\n"
        "- **Decisiones**: get_decisions_history(status_filter='active')\n"
        "- **Sesiones**: get_session_history(limit=10)\n"
        "- **Buscar**: search_memory('docker')\n"
        "- **Comparar**: diff_state('SES-0003')\n"
        "- **Exportar**: export_memory_snapshot()\n"
        "- **Snapshot**: snapshot_session(summary, changes_made)\n"
        "- **Componente**: update_component_status('mcp-tabular', 'ready')\n"
        "- **Decision**: record_decision(title, rationale)\n"
        "- **Tarea**: add_pending_task(title, priority='high')\n"
        "- **Completar**: complete_pending_task('TASK-0001')\n"
        "- **Inicializar**: initialize_project(name, description)\n"
        "- **Sincronizar**: sync_from_filesystem(project_root)"
    )


def memory_error_codes() -> str:
    """Codigos de error comunes del servidor project-memory."""
    return json.dumps(
        {
            "errors": [
                {"code": "NOT_FOUND", "description": "Recurso no encontrado (sesion, tarea, etc.)"},
                {"code": "VALIDATION_ERROR", "description": "Parametros invalidos o fuera de rango"},
                {"code": "FILE_ERROR", "description": "No se pudo leer o escribir el archivo de memoria"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def memory_file_format() -> str:
    """Formato del archivo de memoria."""
    return (
        "# Formato del archivo de memoria\n\n"
        "- Ubicacion: configurada por MEMORY_DIR y MEMORY_FILE\n"
        "- Formato: JSON con indentacion de 2 espacios\n"
        "- Encoding: UTF-8\n"
        "- Schema version: 1.0\n"
        "- El archivo se crea automaticamente al inicializar el proyecto\n"
        "- Es seguro para control de versiones (recomendado commit del archivo)"
    )


def invariant_guide() -> str:
    """Guia de invariantes del proyecto."""
    return (
        "# Invariantes del proyecto\n\n"
        "Las invariantes son reglas que nunca deben violarse.\n"
        "Se definen al inicializar el proyecto con initialize_project().\n"
        "Ejemplos:\n"
        "- 'La logica de negocio nunca importa de fastmcp'\n"
        "- 'Todos los servidores deben correr como non-root en Docker'\n"
        "- 'Las credenciales nunca se hardcodean'\n"
        "- 'Cada MCP debe tener tests con cobertura > 80%'"
    )


def example_get_project_state() -> str:
    """Ejemplo de obtencion del estado del proyecto."""
    return (
        "# Ejemplo: get_project_state\n\n"
        "```\n"
        "get_project_state()\n"
        "```\n"
        "Retorna: project, components, active_decisions, pending_tasks, invariants, "
        "last_session, recent_sessions, stats"
    )


def example_snapshot_session() -> str:
    """Ejemplo de snapshot de sesion."""
    return (
        "# Ejemplo: snapshot_session\n\n"
        "```\n"
        "snapshot_session(\n"
        "    summary='Implemente recursos y tools para mcp-markdown',\n"
        "    changes_made=['resources.py', 'markdown_tools.py', 'server.py'],\n"
        "    decisions_taken=1,\n"
        "    tasks_completed=2,\n"
        "    agent='cascade'\n"
        ")\n"
        "```\n"
        "Retorna: session_id, date, status"
    )


def example_record_decision() -> str:
    """Ejemplo de registro de decision."""
    return (
        "# Ejemplo: record_decision\n\n"
        "```\n"
        "record_decision(\n"
        "    title='Usar FastMCP como framework base',\n"
        "    rationale='FastMCP proporciona decoradores simples y soporte stdio/http',\n"
        "    alternatives_rejected=['mcp-python-sdk', 'implementacion custom'],\n"
        "    tags=['arquitectura', 'framework']\n"
        ")\n"
        "```\n"
        "Retorna: id, date, title, rationale, alternatives_rejected, tags, status"
    )
