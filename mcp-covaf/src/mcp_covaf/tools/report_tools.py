"""Tools de reportes para COVAF.

Genera resúmenes, lista hallazgos, verifica salud, formatea reportes para el
equipo COVAF.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp_shared.errors import McpError


def report_get_health(workspace: Path, docs_path: Path) -> dict[str, Any]:
    """Retorna el estado de salud documentado de COVAF desde STATE.md."""
    full = workspace / docs_path / "STATE.md"
    if not full.exists():
        raise McpError(f"STATE.md no encontrado en {full}")
    try:
        text = full.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        raise McpError(f"Error leyendo STATE: {exc}") from exc
    # Extraer frontmatter
    health: dict[str, Any] = {"timestamp": datetime.now(UTC).isoformat()}
    if text.startswith("---"):
        end = text.find("---", 3)
        if end > 0:
            fm = text[3:end].strip()
            for line in fm.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    health[k.strip()] = v.strip()
    # Contar etiquetas de evidencia
    health["observed_count"] = text.lower().count("observed")
    health["declared_count"] = text.lower().count("declared")
    health["unverified_count"] = text.lower().count("unverified")
    health["historical_count"] = text.lower().count("historical")
    return health


def report_list_findings(workspace: Path, docs_path: Path) -> dict[str, Any]:
    """Lista los hallazgos de seguridad documentados de COVAF."""
    full = workspace / docs_path / "SECURITY-FINDINGS.md"
    if not full.exists():
        return {"findings": [], "count": 0, "note": "SECURITY-FINDINGS.md no existe"}
    try:
        text = full.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        raise McpError(f"Error leyendo findings: {exc}") from exc
    findings: list[dict[str, Any]] = []
    for line in text.splitlines():
        if line.startswith("##") or line.startswith("- **"):
            findings.append({"line": line.strip()})
    return {"findings": findings, "count": len(findings)}


def report_generate_summary(
    workspace: Path,
    docs_path: Path,
    component_key: str | None = None,
) -> dict[str, Any]:
    """Genera un resumen ejecutivo del estado de COVAF o un componente."""
    from mcp_covaf.tools.lifecycle_tools import COMPONENTS, lifecycle_get_status
    status = lifecycle_get_status(workspace)
    health = report_get_health(workspace, docs_path)
    summary: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "workspace": str(workspace),
        "components_total": status["count"],
        "components_status": status["components"],
        "documentation_health": {
            "observed": health.get("observed_count", 0),
            "declared": health.get("declared_count", 0),
            "unverified": health.get("unverified_count", 0),
            "historical": health.get("historical_count", 0),
        },
    }
    if component_key:
        comp = next((c for c in COMPONENTS if c["key"] == component_key), None)
        if comp:
            summary["focus_component"] = comp
    return summary


def report_format_for_team(
    workspace: Path,
    docs_path: Path,
    report_type: str = "status",
    component_key: str | None = None,
) -> dict[str, Any]:
    """Formatea un reporte para envío al equipo COVAF.

    Tipos: status (resumen), security (hallazgos), lifecycle (ciclo de vida),
    bugs (bugs conocidos).
    """
    if report_type == "status":
        data = report_generate_summary(workspace, docs_path, component_key)
        formatted = _format_status_report(data)
    elif report_type == "security":
        data = report_list_findings(workspace, docs_path)
        formatted = _format_security_report(data)
    elif report_type == "lifecycle":
        from mcp_covaf.tools.lifecycle_tools import lifecycle_list_components
        data = lifecycle_list_components(workspace)
        formatted = _format_lifecycle_report(data)
    else:
        raise McpError(f"Tipo de reporte no soportado: {report_type}")
    return {
        "report_type": report_type,
        "component": component_key,
        "formatted_text": formatted,
        "data": data,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _format_status_report(data: dict[str, Any]) -> str:
    lines = [
        "# Reporte de Estado COVAF",
        f"Generado: {data['generated_at']}",
        "",
        "## Componentes",
    ]
    for c in data.get("components_status", []):
        emoji = {"clean": "OK", "dirty": "MOD", "missing": "MISS",
                 "no_git": "NOGIT", "unverified": "?"}.get(c.get("status", "?"), "?")
        lines.append(f"- [{emoji}] {c['name']} ({c['key']}): {c.get('status', '?')}")
    lines.extend([
        "",
        "## Documentación",
        f"- Observed: {data['documentation_health']['observed']}",
        f"- Declared: {data['documentation_health']['declared']}",
        f"- Unverified: {data['documentation_health']['unverified']}",
        f"- Historical: {data['documentation_health']['historical']}",
    ])
    return "\n".join(lines)


def _format_security_report(data: dict[str, Any]) -> str:
    lines = [
        "# Reporte de Seguridad COVAF",
        f"Hallazgos: {data.get('count', 0)}",
        "",
    ]
    for f in data.get("findings", []):
        lines.append(f"- {f['line']}")
    return "\n".join(lines)


def _format_lifecycle_report(data: dict[str, Any]) -> str:
    lines = [
        "# Ciclo de Vida COVAF",
        f"Componentes: {data.get('count', 0)}",
        "",
    ]
    for c in data.get("components", []):
        exists = "OK" if c.get("exists") else "MISS"
        lines.append(f"- [{exists}] {c['name']} ({c['key']}) — {c.get('language', '?')}")
    return "\n".join(lines)
