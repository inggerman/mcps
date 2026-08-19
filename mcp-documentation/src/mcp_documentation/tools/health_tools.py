"""Health Tools — 2 herramientas para health check y métricas."""

from __future__ import annotations

from mcp_documentation.config import settings
from mcp_documentation.health import get_metrics as _get_metrics
from mcp_documentation.health import health_check as _health_check


def health_check_tool() -> dict:
    """Verifica salud del servidor: filesystem, índice FTS5, documentos, sesiones, versiones, audit log."""
    return _health_check(settings.root_path, settings.resolved_index_path)


def get_metrics_tool() -> str:
    """Retorna métricas en formato Prometheus text exposition (docs_total, sessions, versions, audit, health)."""
    return _get_metrics(settings.root_path, settings.resolved_index_path)
