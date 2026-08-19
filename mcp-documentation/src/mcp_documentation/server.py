"""Servidor MCP Documentation — experto en gestión de documentación.

50 tools en 8 grupos: lectura, escritura, transformación, clasificación,
indexación/búsqueda, sesiones, diagramas, investigaciones.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData

from mcp_documentation import __version__
from mcp_documentation.config import settings
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

# Tools imports
from mcp_documentation.tools.doc_read_tools import (
    get_document_metadata,
    get_document_summary,
    get_document_toc,
    get_documents_by_category,
    get_documents_by_tag,
    get_recent_documents,
    list_documents,
    read_document,
    read_document_section,
    search_in_document,
)
from mcp_documentation.tools.doc_write_tools import (
    add_tags,
    append_to_document,
    create_document,
    create_from_template,
    delete_document,
    move_document,
    update_document,
    update_frontmatter,
)
from mcp_documentation.tools.doc_transform_tools import (
    html_to_markdown,
    json_to_yaml,
    markdown_to_html,
    markdown_to_plain_text,
    merge_documents,
    xml_to_yaml,
    yaml_to_json,
)
from mcp_documentation.tools.doc_classify_tools import (
    add_custom_category_tool,
    classify_document_tool,
    get_categories,
    reclassify_document,
    validate_classification_tool,
)
from mcp_documentation.tools.doc_index_tools import (
    get_index_stats_tool,
    index_documents_tool,
    rebuild_index_tool,
    search_documents_tool,
    suggest_similar_documents_tool,
)
from mcp_documentation.tools.session_tools import (
    detect_problems_tool,
    end_session_tool,
    generate_session_report_tool,
    get_session_history_tool,
    log_session_event_tool,
    start_session_tool,
    suggest_solutions_tool,
    track_change_tool,
)
from mcp_documentation.tools.diagram_tools import (
    create_mermaid_diagram,
    create_plantuml_diagram,
    embed_diagram_in_md,
    list_diagrams,
)
from mcp_documentation.tools.investigation_tools import (
    add_evidence,
    close_investigation,
    create_investigation,
)
from mcp_documentation.tools.versioning_tools import (
    compare_versions_tool,
    get_audit_log_tool,
    get_document_history_tool,
    restore_document_version_tool,
)
from mcp_documentation.tools.health_tools import (
    get_metrics_tool,
    health_check_tool,
)
from mcp_documentation.tools.backup_tools import (
    backup_documents_tool,
    export_documents_tool,
    list_backups_tool,
    restore_backup_tool,
)

logger = setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name=settings.mcp_server_name,
)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[None]:
    log.info("mcp-documentation starting", version=__version__, root=str(settings.root_path))
    yield
    log.info("mcp-documentation stopping")


mcp = FastMCP(
    name="mcp-documentation",
    instructions=(
        "Servidor MCP experto en documentación, escritura y lectura. "
        "Gestiona documentación técnica en formato .md, .yaml, .xml, .json, .docx, .pdf, .mmd, .puml.\n"
        "Clasifica automáticamente: feature, fix, hotfix, spike, bitacora, investigation, "
        "information, insumos, architecture, runbook, guide, tutorial, inventory, analysis, "
        "forensic, reference, troubleshooting, deployment, decision (ADR).\n"
        "TODO documento creado debe incluir timestamp ISO 8601 en frontmatter.\n"
        "Path base configurable (DOC_ROOT_PATH), default C:/mcp-doc/.\n"
        "Herramientas: 59 tools en 11 grupos: lectura, escritura, transformación, "
        "clasificación, indexación/búsqueda, sesiones, diagramas, investigaciones, "
        "versionado+audit, health+metrics, backup+export.\n"
        "PATRÓN DE SESIÓN: 1) start_session → 2) log_session_event/track_change durante trabajo "
        "→ 3) detect_problems/suggest_solutions → 4) end_session (genera bitacora auto).\n"
        "VERSIONADO: cada update/append/delete guarda snapshot automático en .versions/. "
        "Audit log en .audit.log registra todas las operaciones.\n"
        "BACKUP: backup_documents crea ZIP completo, export_documents filtra por categoría/directorio."
    ),
    lifespan=lifespan,
)


def _handle(func, *args, **kwargs) -> Any:
    """Ejecuta una función de tool y maneja errores MCP."""
    try:
        return func(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en tool", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ===========================================================================
# Grupo 1: Doc Read Tools (10)
# ===========================================================================

@mcp.tool(name="read_document", description="Lee cualquier documento soportado (.md, .yaml, .xml, .txt, .json). Retorna contenido, metadata y frontmatter.")
def tool_read_document(path: str) -> dict[str, Any]:
    log.info("read_document llamado", path=path)
    return _handle(read_document, path)


@mcp.tool(name="read_document_section", description="Lee una sección específica de un documento por heading. Retorna contenido, nivel y líneas.")
def tool_read_document_section(path: str, heading: str, case_sensitive: bool = False) -> dict[str, Any] | None:
    log.info("read_document_section llamado", path=path, heading=heading)
    return _handle(read_document_section, path, heading, case_sensitive)


@mcp.tool(name="list_documents", description="Lista documentos en un directorio con metadata: tamaño, fecha, tipo, clasificación, tags.")
def tool_list_documents(directory: str = "", recursive: bool = True) -> list[dict[str, Any]]:
    log.info("list_documents llamado", directory=directory)
    return _handle(list_documents, directory, recursive)


@mcp.tool(name="get_document_metadata", description="Extrae metadata completa: frontmatter, timestamp, tamaño, clasificación, tags, autor.")
def tool_get_document_metadata(path: str) -> dict[str, Any]:
    log.info("get_document_metadata llamado", path=path)
    return _handle(get_document_metadata, path)


@mcp.tool(name="search_in_document", description="Búsqueda texto dentro de un documento con contexto y número de línea.")
def tool_search_in_document(path: str, query: str, case_sensitive: bool = False) -> list[dict[str, Any]]:
    log.info("search_in_document llamado", path=path, query=query)
    return _handle(search_in_document, path, query, case_sensitive)


@mcp.tool(name="get_document_summary", description="Resumen automático: título, word count, headings, primer párrafo.")
def tool_get_document_summary(path: str, max_words: int = 100) -> dict[str, Any]:
    log.info("get_document_summary llamado", path=path)
    return _handle(get_document_summary, path, max_words)


@mcp.tool(name="get_document_toc", description="Genera tabla de contenidos desde headings del documento.")
def tool_get_document_toc(path: str, max_depth: int = 3) -> str:
    log.info("get_document_toc llamado", path=path)
    return _handle(get_document_toc, path, max_depth)


@mcp.tool(name="get_recent_documents", description="Lista documentos ordenados por timestamp (más recientes primero).")
def tool_get_recent_documents(limit: int = 20, directory: str = "") -> list[dict[str, Any]]:
    log.info("get_recent_documents llamado", limit=limit)
    return _handle(get_recent_documents, limit, directory)


@mcp.tool(name="get_documents_by_category", description="Filtra documentos por clasificación (feature, fix, bitacora, etc.).")
def tool_get_documents_by_category(category: str) -> list[dict[str, Any]]:
    log.info("get_documents_by_category llamado", category=category)
    return _handle(get_documents_by_category, category)


@mcp.tool(name="get_documents_by_tag", description="Filtra documentos por tag específico en frontmatter.")
def tool_get_documents_by_tag(tag: str) -> list[dict[str, Any]]:
    log.info("get_documents_by_tag llamado", tag=tag)
    return _handle(get_documents_by_tag, tag)


# ===========================================================================
# Grupo 2: Doc Write Tools (8)
# ===========================================================================

@mcp.tool(name="create_document", description="Crea documento nuevo con frontmatter obligatorio (title, type, project, tags, timestamp, status, author). Auto-clasifica en directorio correcto.")
def tool_create_document(
    title: str,
    content: str,
    doc_type: str = "information",
    project: str = "",
    tags: list[str] | None = None,
    author: str = "unknown",
    status: str = "draft",
    filename: str = "",
    directory: str = "",
) -> dict[str, Any]:
    log.info("create_document llamado", title=title, doc_type=doc_type)
    return _handle(create_document, title, content, doc_type, project, tags, author, status, filename, directory)


@mcp.tool(name="update_document", description="Actualiza contenido de documento existente, actualiza timestamp automáticamente.")
def tool_update_document(path: str, content: str, update_timestamp: bool = True) -> dict[str, Any]:
    log.info("update_document llamado", path=path)
    return _handle(update_document, path, content, update_timestamp)


@mcp.tool(name="append_to_document", description="Añade contenido al final de un documento existente.")
def tool_append_to_document(path: str, content: str, separator: str = "\n\n") -> dict[str, Any]:
    log.info("append_to_document llamado", path=path)
    return _handle(append_to_document, path, content, separator)


@mcp.tool(name="update_frontmatter", description="Actualiza campos específicos del frontmatter sin tocar el body.")
def tool_update_frontmatter(path: str, updates: dict[str, Any]) -> dict[str, Any]:
    log.info("update_frontmatter llamado", path=path)
    return _handle(update_frontmatter, path, updates)


@mcp.tool(name="add_tags", description="Añade tags al frontmatter de un documento.")
def tool_add_tags(path: str, tags: list[str]) -> dict[str, Any]:
    log.info("add_tags llamado", path=path, tags=tags)
    return _handle(add_tags, path, tags)


@mcp.tool(name="delete_document", description="Elimina un documento del filesystem.")
def tool_delete_document(path: str) -> dict[str, Any]:
    log.info("delete_document llamado", path=path)
    return _handle(delete_document, path)


@mcp.tool(name="create_from_template", description="Crea documento desde plantilla predefinida (feature, fix, hotfix, spike, bitacora, investigation, decision, runbook).")
def tool_create_from_template(
    template_type: str,
    title: str,
    project: str = "",
    tags: list[str] | None = None,
    author: str = "unknown",
    filename: str = "",
) -> dict[str, Any]:
    log.info("create_from_template llamado", template_type=template_type, title=title)
    return _handle(create_from_template, template_type, title, project, tags, author, filename)


@mcp.tool(name="move_document", description="Mueve documento a otra clasificación/directorio, actualiza frontmatter.")
def tool_move_document(path: str, new_category: str, new_filename: str = "") -> dict[str, Any]:
    log.info("move_document llamado", path=path, new_category=new_category)
    return _handle(move_document, path, new_category, new_filename)


# ===========================================================================
# Grupo 3: Doc Transform Tools (7)
# ===========================================================================

@mcp.tool(name="markdown_to_html", description="Convierte Markdown a HTML completo con CSS. Soporta tablas, code blocks, imágenes.")
def tool_markdown_to_html(path_or_text: str, is_path: bool = True) -> str:
    log.info("markdown_to_html llamado")
    return _handle(markdown_to_html, path_or_text, is_path)


@mcp.tool(name="html_to_markdown", description="Convierte HTML a Markdown limpio.")
def tool_html_to_markdown(html_text: str) -> str:
    log.info("html_to_markdown llamado")
    return _handle(html_to_markdown, html_text)


@mcp.tool(name="markdown_to_plain_text", description="Extrae texto plano sin markup de un Markdown.")
def tool_markdown_to_plain_text(path_or_text: str, is_path: bool = True) -> str:
    log.info("markdown_to_plain_text llamado")
    return _handle(markdown_to_plain_text, path_or_text, is_path)


@mcp.tool(name="yaml_to_json", description="Convierte YAML a JSON.")
def tool_yaml_to_json(path_or_text: str, is_path: bool = True) -> str:
    log.info("yaml_to_json llamado")
    return _handle(yaml_to_json, path_or_text, is_path)


@mcp.tool(name="json_to_yaml", description="Convierte JSON a YAML.")
def tool_json_to_yaml(path_or_text: str, is_path: bool = True) -> str:
    log.info("json_to_yaml llamado")
    return _handle(json_to_yaml, path_or_text, is_path)


@mcp.tool(name="xml_to_yaml", description="Convierte XML a YAML.")
def tool_xml_to_yaml(path_or_text: str, is_path: bool = True) -> str:
    log.info("xml_to_yaml llamado")
    return _handle(xml_to_yaml, path_or_text, is_path)


@mcp.tool(name="merge_documents", description="Combina múltiples archivos en uno solo con separador.")
def tool_merge_documents(files: list[str], separator: str = "\n\n---\n\n") -> str:
    log.info("merge_documents llamado", file_count=len(files))
    return _handle(merge_documents, files, separator)


# ===========================================================================
# Grupo 4: Doc Classify Tools (5)
# ===========================================================================

@mcp.tool(name="classify_document", description="Analiza contenido y sugiere/auto-asigna clasificación usando heurísticas de keywords.")
def tool_classify_document(path: str) -> dict[str, Any]:
    log.info("classify_document llamado", path=path)
    return _handle(classify_document_tool, path)


@mcp.tool(name="get_categories", description="Lista todas las categorías disponibles (core + extended + custom).")
def tool_get_categories() -> dict[str, Any]:
    log.info("get_categories llamado")
    return _handle(get_categories)


@mcp.tool(name="add_custom_category", description="Añade categoría custom al archivo .categories.json.")
def tool_add_custom_category(name: str, keywords: list[str]) -> dict[str, Any]:
    log.info("add_custom_category llamado", name=name)
    return _handle(add_custom_category_tool, name, keywords)


@mcp.tool(name="validate_classification", description="Valida que un documento esté en el directorio correcto según su tipo.")
def tool_validate_classification(path: str) -> dict[str, Any]:
    log.info("validate_classification llamado", path=path)
    return _handle(validate_classification_tool, path)


@mcp.tool(name="reclassify_document", description="Reclassifica un documento: mueve archivo, actualiza frontmatter y directorio.")
def tool_reclassify_document(path: str, new_category: str) -> dict[str, Any]:
    log.info("reclassify_document llamado", path=path, new_category=new_category)
    return _handle(reclassify_document, path, new_category)


# ===========================================================================
# Grupo 5: Doc Index Tools (5)
# ===========================================================================

@mcp.tool(name="index_documents", description="Indexa todos los documentos en root_path usando SQLite FTS5. Crea/actualiza índice.")
def tool_index_documents(directory: str = "") -> dict[str, Any]:
    log.info("index_documents llamado")
    return _handle(index_documents_tool, directory)


@mcp.tool(name="search_documents", description="Búsqueda full-text con ranking BM25 sobre el índice. Retorna path, título, snippet, score.")
def tool_search_documents(query: str, limit: int = 20, category: str | None = None) -> list[dict[str, Any]]:
    log.info("search_documents llamado", query=query)
    return _handle(search_documents_tool, query, limit, category)


@mcp.tool(name="get_index_stats", description="Estadísticas del índice: total documentos, por categoría, por tipo, tamaño índice.")
def tool_get_index_stats() -> dict[str, Any]:
    log.info("get_index_stats llamado")
    return _handle(get_index_stats_tool)


@mcp.tool(name="rebuild_index", description="Reconstruye el índice desde cero. Útil después de cambios masivos.")
def tool_rebuild_index() -> dict[str, Any]:
    log.info("rebuild_index llamado")
    return _handle(rebuild_index_tool)


@mcp.tool(name="suggest_similar_documents", description="Dado un documento, encuentra similares por contenido y tags.")
def tool_suggest_similar_documents(path: str, limit: int = 5) -> list[dict[str, Any]]:
    log.info("suggest_similar_documents llamado", path=path)
    return _handle(suggest_similar_documents_tool, path, limit)


# ===========================================================================
# Grupo 6: Session Tools (8)
# ===========================================================================

@mcp.tool(name="start_session", description="Inicia tracking de sesión: crea estructura con ID, timestamp, contexto inicial.")
def tool_start_session(project: str = "", context: str = "", agent: str = "unknown") -> dict[str, Any]:
    log.info("start_session llamado", project=project)
    return _handle(start_session_tool, project, context, agent)


@mcp.tool(name="log_session_event", description="Registra evento durante sesión (problem, solution, change, decision, note).")
def tool_log_session_event(
    session_id: str,
    event_type: str,
    description: str,
    severity: str = "low",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    log.info("log_session_event llamado", session_id=session_id, event_type=event_type)
    return _handle(log_session_event_tool, session_id, event_type, description, severity, metadata)


@mcp.tool(name="detect_problems", description="Analiza eventos de sesión e identifica patrones de problemas (errores recurrentes, bloqueos).")
def tool_detect_problems(session_id: str) -> dict[str, Any]:
    log.info("detect_problems llamado", session_id=session_id)
    return _handle(detect_problems_tool, session_id)


@mcp.tool(name="suggest_solutions", description="Basado en problemas detectados, sugiere soluciones desde historial de documentación.")
def tool_suggest_solutions(session_id: str) -> dict[str, Any]:
    log.info("suggest_solutions llamado", session_id=session_id)
    return _handle(suggest_solutions_tool, session_id)


@mcp.tool(name="track_change", description="Registra un cambio durante la sesión (archivo, descripción, tipo: add/modify/delete).")
def tool_track_change(session_id: str, file_path: str, change_type: str, description: str = "") -> dict[str, Any]:
    log.info("track_change llamado", session_id=session_id, file_path=file_path)
    return _handle(track_change_tool, session_id, file_path, change_type, description)


@mcp.tool(name="end_session", description="Cierra sesión: genera bitácora automática con resumen, problemas, soluciones, cambios.")
def tool_end_session(session_id: str, summary: str = "") -> dict[str, Any]:
    log.info("end_session llamado", session_id=session_id)
    return _handle(end_session_tool, session_id, summary)


@mcp.tool(name="get_session_history", description="Historial de sesiones anteriores con filtros por fecha, proyecto, tipo.")
def tool_get_session_history(limit: int = 20, project: str | None = None) -> list[dict[str, Any]]:
    log.info("get_session_history llamado", limit=limit)
    return _handle(get_session_history_tool, limit, project)


@mcp.tool(name="generate_session_report", description="Genera reporte Markdown completo de una sesión específica.")
def tool_generate_session_report(session_id: str) -> str:
    log.info("generate_session_report llamado", session_id=session_id)
    return _handle(generate_session_report_tool, session_id)


# ===========================================================================
# Grupo 7: Diagram Tools (4)
# ===========================================================================

@mcp.tool(name="create_mermaid_diagram", description="Crea diagrama Mermaid desde texto (.mmd). Soporta flowchart, sequence, class, state, ER.")
def tool_create_mermaid_diagram(title: str, definition: str, filename: str = "") -> dict[str, Any]:
    log.info("create_mermaid_diagram llamado", title=title)
    return _handle(create_mermaid_diagram, title, definition, filename)


@mcp.tool(name="create_plantuml_diagram", description="Crea diagrama PlantUML desde texto (.puml).")
def tool_create_plantuml_diagram(title: str, definition: str, filename: str = "") -> dict[str, Any]:
    log.info("create_plantuml_diagram llamado", title=title)
    return _handle(create_plantuml_diagram, title, definition, filename)


@mcp.tool(name="embed_diagram_in_md", description="Embebe diagrama en archivo Markdown con code block apropiado.")
def tool_embed_diagram_in_md(md_path: str, diagram_path: str, caption: str = "", position: str = "end") -> dict[str, Any]:
    log.info("embed_diagram_in_md llamado", md_path=md_path)
    return _handle(embed_diagram_in_md, md_path, diagram_path, caption, position)


@mcp.tool(name="list_diagrams", description="Lista todos los diagramas en el directorio de diagrams con metadata.")
def tool_list_diagrams() -> list[dict[str, Any]]:
    log.info("list_diagrams llamado")
    return _handle(list_diagrams)


# ===========================================================================
# Grupo 8: Investigation Tools (3)
# ===========================================================================

@mcp.tool(name="create_investigation", description="Crea documento de investigación con estructura: hipótesis, evidencia, conclusiones.")
def tool_create_investigation(
    title: str,
    hypothesis: str,
    project: str = "",
    tags: list[str] | None = None,
    author: str = "unknown",
) -> dict[str, Any]:
    log.info("create_investigation llamado", title=title)
    return _handle(create_investigation, title, hypothesis, project, tags, author)


@mcp.tool(name="add_evidence", description="Añade evidencia a una investigación existente (tipo: log, screenshot, code, reference, test, observation).")
def tool_add_evidence(path: str, evidence_type: str, description: str, reference: str = "") -> dict[str, Any]:
    log.info("add_evidence llamado", path=path, evidence_type=evidence_type)
    return _handle(add_evidence, path, evidence_type, description, reference)


@mcp.tool(name="close_investigation", description="Cierra investigación: status=resolved/unresolved/partial, conclusiones, lecciones aprendidas.")
def tool_close_investigation(path: str, status: str, conclusions: str, lessons: str = "") -> dict[str, Any]:
    log.info("close_investigation llamado", path=path, status=status)
    return _handle(close_investigation, path, status, conclusions, lessons)


# ===========================================================================
# Grupo 9: Versioning + Audit Tools (4)
# ===========================================================================

@mcp.tool(name="get_document_history", description="Retorna historial completo de versiones de un documento: snapshots, fechas, tamaños.")
def tool_get_document_history(path: str) -> list[dict[str, Any]]:
    log.info("get_document_history llamado", path=path)
    return _handle(get_document_history_tool, path)


@mcp.tool(name="restore_document_version", description="Restaura una versión específica de un documento (guarda snapshot actual antes de restaurar).")
def tool_restore_document_version(path: str, version: int) -> dict[str, Any]:
    log.info("restore_document_version llamado", path=path, version=version)
    return _handle(restore_document_version_tool, path, version)


@mcp.tool(name="compare_versions", description="Compara dos versiones de un documento y retorna diff unificado.")
def tool_compare_versions(path: str, version_a: int, version_b: int) -> dict[str, Any]:
    log.info("compare_versions llamado", path=path, a=version_a, b=version_b)
    return _handle(compare_versions_tool, path, version_a, version_b)


@mcp.tool(name="get_audit_log", description="Consulta el audit log con filtros: action (create/update/delete/version_saved/...), target (file path).")
def tool_get_audit_log(limit: int = 50, action: str = "", target: str = "") -> list[dict[str, Any]]:
    log.info("get_audit_log llamado", limit=limit, action=action)
    return _handle(get_audit_log_tool, limit, action or None, target or None)


# ===========================================================================
# Grupo 10: Health + Metrics Tools (2)
# ===========================================================================

@mcp.tool(name="health_check", description="Verifica salud del servidor: filesystem, índice FTS5, documentos, sesiones, versiones, audit log.")
def tool_health_check() -> dict[str, Any]:
    log.info("health_check llamado")
    return _handle(health_check_tool)


@mcp.tool(name="get_metrics", description="Retorna métricas en formato Prometheus text exposition (docs_total, sessions, versions, audit, health).")
def tool_get_metrics() -> str:
    log.info("get_metrics llamado")
    return _handle(get_metrics_tool)


# ===========================================================================
# Grupo 11: Backup + Export Tools (3)
# ===========================================================================

@mcp.tool(name="backup_documents", description="Crea backup ZIP completo del document store. Incluye versiones y audit log por defecto.")
def tool_backup_documents(include_versions: bool = True, include_audit: bool = True) -> dict[str, Any]:
    log.info("backup_documents llamado", include_versions=include_versions)
    return _handle(backup_documents_tool, include_versions, include_audit)


@mcp.tool(name="restore_backup", description="Restaura documentos desde un backup ZIP. Acepta path absoluto o nombre relativo a .backups/.")
def tool_restore_backup(backup_file: str) -> dict[str, Any]:
    log.info("restore_backup llamado", backup_file=backup_file)
    return _handle(restore_backup_tool, backup_file)


@mcp.tool(name="export_documents", description="Exporta documentos a ZIP con filtros opcionales por categoría o directorio.")
def tool_export_documents(output_path: str = "", category: str = "", directory: str = "") -> dict[str, Any]:
    log.info("export_documents llamado", category=category, directory=directory)
    return _handle(export_documents_tool, output_path, category, directory)


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
