"""Tools para el frontend COVAF (CovafAlternativosFront — Vue 3 + Module Federation).

Cobertura: rutas, módulos, servicios, MFE config, búsqueda de código.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from mcp_shared.errors import McpError

# Rutas del frontend (observado en src/router/index.js).
KNOWN_ROUTES = [
    {"path": "", "name": "Inicio", "component": "WelcomeComponent.vue"},
    {"path": "instrumentos", "name": "Instrumentos", "component": "InstrumentosView.vue"},
    {"path": "validacionsiefores", "name": "Validación Siefores", "component": "ValidacionSieforesView.vue"},
    {"path": "cartasconfirmacion", "name": "Cartas Confirmación", "component": "CartasConfirmacionView.vue"},
    {"path": "monitor", "name": "Monitor", "component": "MonitorKendoView.vue"},
    {"path": "matriz", "name": "Matriz", "component": "MatrizKendoView.vue"},
    {"path": "calculadora", "name": "Calculadora", "component": "CalculadoraView.vue"},
    {"path": "regulatorio0343", "name": "Sistema 0343", "component": "Sistema0343View.vue"},
    {"path": "auditor", "name": "Auditor Externo", "component": "AuditorExtView.vue"},
    {"path": "entidades", "name": "Entidades", "component": "EntidadesView.vue"},
    {"path": "divisas", "name": "Divisas", "component": "DivisasView.vue"},
    {"path": "fiduciario", "name": "Fiduciario", "component": "FiduciarioView.vue"},
    {"path": "paises", "name": "Países", "component": "PaisesView.vue"},
    {"path": "valuador", "name": "Valuador", "component": "ValuadorInView.vue"},
    {"path": "wizard", "name": "Wizard", "component": "WizardView.vue"},
    {"path": "prospectos", "name": "Prospectos DRIA", "component": "V2Layout.vue", "children": [
        {"path": "dashboard", "component": "V2DashboardView.vue"},
        {"path": "documentos", "component": "V2DocumentsView.vue"},
        {"path": "carga", "component": "V2UploadView.vue"},
        {"path": "revision", "component": "V2ReviewView.vue"},
    ]},
]

# Módulos de catálogos maestros.
CATALOG_MODULES = [
    "auditor", "clasificacion", "concepto", "divisas", "entidades", "estatus",
    "estrategia", "fiduciario", "paises", "representante", "sectorial",
    "sectorestrategia", "tickerreuters", "tipoproyecto", "tipoinstrumento",
    "tipocoinversionista", "valuador",
]


def _resolve_front_path(workspace: Path, relative: Path) -> Path:
    full = workspace / relative
    if not full.exists():
        raise McpError(f"Frontend no encontrado en {full}")
    return full


def front_list_routes(workspace: Path, front_path: Path) -> dict[str, Any]:
    """Lista las rutas del frontend Vue (CovafAlternativosFront)."""
    _resolve_front_path(workspace, front_path)
    return {
        "base_path": "/covafalternativos",
        "routes": KNOWN_ROUTES,
        "count": len(KNOWN_ROUTES),
        "catalog_modules": CATALOG_MODULES,
    }


def front_list_modules(workspace: Path, front_path: Path) -> dict[str, Any]:
    """Lista los módulos/páginas del frontend Vue."""
    full = _resolve_front_path(workspace, front_path)
    views = full / "src/views"
    components = full / "src/components"
    modules: list[dict[str, Any]] = []
    if views.exists():
        for f in views.glob("*.vue"):
            modules.append({
                "name": f.stem,
                "type": "view",
                "path": str(f.relative_to(full)),
            })
    if components.exists():
        for d in components.iterdir():
            if d.is_dir():
                modules.append({
                    "name": d.name,
                    "type": "component_group",
                    "path": str(d.relative_to(full)),
                })
    return {"modules": modules, "count": len(modules)}


def front_list_services(workspace: Path, front_path: Path) -> dict[str, Any]:
    """Lista los servicios API del frontend Vue."""
    full = _resolve_front_path(workspace, front_path)
    services_dir = full / "src/service"
    services: list[dict[str, Any]] = []
    if services_dir.exists():
        for f in services_dir.iterdir():
            if f.is_file() and f.suffix in (".js", ".ts"):
                services.append({
                    "name": f.stem,
                    "path": str(f.relative_to(full)),
                })
    return {"services": services, "count": len(services)}


def front_search_code(
    workspace: Path, front_path: Path, pattern: str, max_results: int = 20
) -> dict[str, Any]:
    """Busca un patrón (regex) en el código del frontend Vue."""
    full = _resolve_front_path(workspace, front_path)
    matches: list[dict[str, Any]] = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as exc:
        raise McpError(f"Regex inválido: {exc}") from exc
    src = full / "src"
    if not src.exists():
        return {"matches": [], "count": 0, "error": "src/ no existe"}
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix not in (".vue", ".js", ".ts"):
            continue
        if len(matches) >= max_results:
            break
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if regex.search(line):
                matches.append({
                    "file": str(f.relative_to(full)),
                    "line": i,
                    "text": line.strip()[:200],
                })
                if len(matches) >= max_results:
                    break
    return {"matches": matches, "count": len(matches)}


def front_get_mfe_config(workspace: Path, front_path: Path) -> dict[str, Any]:
    """Retorna la configuración de Module Federation del frontend."""
    full = _resolve_front_path(workspace, front_path)
    vue_config = full / "vue.config.js"
    config_text = ""
    if vue_config.exists():
        try:
            config_text = vue_config.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            pass
    # Extraer info del MFE
    mfe_info: dict[str, Any] = {
        "name": "covafalternativos",
        "filename": "remoteEntry.covafjs",
        "exposes": [],
        "remotes": [],
    }
    if "ModuleFederationPlugin" in config_text:
        # Heurística: buscar exposes
        exposes_match = re.search(r"exposes\s*:\s*\{([^}]+)\}", config_text, re.DOTALL)
        if exposes_match:
            for m in re.finditer(r"['\"]([^'\"]+)['\"]\s*:\s*['\"]([^'\"]+)['\"]", exposes_match.group(1)):
                mfe_info["exposes"].append({"name": m.group(1), "path": m.group(2)})
    return {
        "mfe": mfe_info,
        "framework": "Vue 3.2.47",
        "build_tool": "@vue/cli-service 5.0.0",
        "ui_libs": ["primevue", "ant-design-vue", "kendo-vue"],
        "auth": "@covaf/login-cognito-lib",
    }
