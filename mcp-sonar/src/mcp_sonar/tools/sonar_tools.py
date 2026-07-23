"""
Lógica de mcp-sonar.

Envuelve la ejecución de sonar-scanner o llamadas a su API.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from mcp_shared.errors import McpError


def sonar_scan(project_path: Path, host_url: str, api_token: str) -> dict[str, Any]:
    """Ejecuta sonar-scanner si está disponible, o retorna datos mock."""
    sonar_bin = shutil.which("sonar-scanner")

    if not sonar_bin:
        # Mock mode
        return {
            "mode": "mock",
            "status": "success",
            "metrics": {
                "coverage": "85.4%",
                "bugs": 0,
                "vulnerabilities": 0,
                "code_smells": 12,
                "technical_debt_ratio": "1.2%"
            },
            "message": "sonar-scanner no encontrado. Retornando métricas simuladas."
        }

    try:
        args = [sonar_bin, f"-Dsonar.host.url={host_url}"]
        if api_token:
            args.append(f"-Dsonar.login={api_token}")

        result = subprocess.run(
            args,
            cwd=str(project_path),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise McpError(f"Error en sonar-scanner: {result.stderr}")

        return {
            "mode": "real",
            "status": "success",
            "output": result.stdout[:1000] + "..."
        }
    except Exception as exc:
        raise McpError(f"Fallo al ejecutar SonarQube scan: {exc}") from exc


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------

import json as _json

import httpx


def _api_get(host_url: str, api_token: str, endpoint: str, params: dict | None = None) -> dict[str, Any]:
    """Llamada GET a la API de SonarQube."""
    if not host_url:
        raise McpError("host_url no configurado.")
    headers = {}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    response = httpx.get(
        f"{host_url.rstrip('/')}/api/{endpoint}",
        params=params or {},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def sonar_components_search(host_url: str, api_token: str, query: str) -> dict[str, Any]:
    """Busca componentes en SonarQube."""
    if not query.strip():
        raise McpError("query no puede estar vacio.")
    return _api_get(host_url, api_token, "components/search", {"q": query})


def sonar_issues_search(host_url: str, api_token: str, project_key: str) -> dict[str, Any]:
    """Busca issues en un proyecto."""
    if not project_key.strip():
        raise McpError("project_key no puede estar vacio.")
    return _api_get(host_url, api_token, "issues/search", {"componentKeys": project_key})


def sonar_measures_component(host_url: str, api_token: str, component: str, metric_keys: str) -> dict[str, Any]:
    """Obtiene medidas de un componente."""
    if not component.strip() or not metric_keys.strip():
        raise McpError("component y metric_keys no pueden estar vacios.")
    return _api_get(host_url, api_token, "measures/component", {"component": component, "metricKeys": metric_keys})


def sonar_measures_history(host_url: str, api_token: str, component: str, metrics: str) -> dict[str, Any]:
    """Obtiene historico de medidas."""
    if not component.strip() or not metrics.strip():
        raise McpError("component y metrics no pueden estar vacios.")
    return _api_get(host_url, api_token, "measures/search_history", {"component": component, "metrics": metrics})


def sonar_qualitygates_list(host_url: str, api_token: str) -> dict[str, Any]:
    """Lista quality gates."""
    return _api_get(host_url, api_token, "qualitygates/list")


def sonar_qualitygates_status(host_url: str, api_token: str, project_key: str) -> dict[str, Any]:
    """Obtiene el estado del quality gate de un proyecto."""
    if not project_key.strip():
        raise McpError("project_key no puede estar vacio.")
    return _api_get(host_url, api_token, "qualitygates/project_status", {"projectKey": project_key})


def sonar_rules_search(host_url: str, api_token: str, language: str = "", q: str = "") -> dict[str, Any]:
    """Busca reglas en SonarQube."""
    params: dict[str, Any] = {}
    if language:
        params["languages"] = language
    if q:
        params["q"] = q
    return _api_get(host_url, api_token, "rules/search", params)


def sonar_languages_list(host_url: str, api_token: str) -> dict[str, Any]:
    """Lista lenguajes soportados."""
    return _api_get(host_url, api_token, "languages/list")


def sonar_projects_search(host_url: str, api_token: str, q: str = "") -> dict[str, Any]:
    """Busca proyectos en SonarQube."""
    params: dict[str, Any] = {}
    if q:
        params["q"] = q
    return _api_get(host_url, api_token, "projects/search", params)


def sonar_project_create(host_url: str, api_token: str, name: str, key: str) -> dict[str, Any]:
    """Crea un proyecto en SonarQube."""
    if not name.strip() or not key.strip():
        raise McpError("name y key no pueden estar vacios.")
    if not api_token:
        raise McpError("api_token requerido para crear proyectos.")
    response = httpx.post(
        f"{host_url.rstrip('/')}/api/projects/create",
        data={"name": name, "project": key},
        headers={"Authorization": f"Bearer {api_token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def sonar_project_delete(host_url: str, api_token: str, key: str) -> dict[str, Any]:
    """Elimina un proyecto en SonarQube."""
    if not key.strip():
        raise McpError("key no puede estar vacio.")
    if not api_token:
        raise McpError("api_token requerido para eliminar proyectos.")
    response = httpx.post(
        f"{host_url.rstrip('/')}/api/projects/delete",
        data={"project": key},
        headers={"Authorization": f"Bearer {api_token}"},
        timeout=30,
    )
    response.raise_for_status()
    return {"status": "deleted", "key": key}


def sonar_hotspots_search(host_url: str, api_token: str, project_key: str) -> dict[str, Any]:
    """Busca hotspots de seguridad."""
    if not project_key.strip():
        raise McpError("project_key no puede estar vacio.")
    return _api_get(host_url, api_token, "hotspots/search", {"projectKey": project_key})


def sonar_health(host_url: str, api_token: str) -> dict[str, Any]:
    """Verifica el estado de salud de SonarQube."""
    try:
        response = httpx.get(
            f"{host_url.rstrip('/')}/api/system/status",
            headers={"Authorization": f"Bearer {api_token}"} if api_token else {},
            timeout=10,
        )
        return {"status_code": response.status_code, "body": response.json()}
    except Exception as exc:
        return {"status_code": 0, "error": str(exc)[:100]}


def sonar_qualityprofiles_list(host_url: str, api_token: str, language: str = "") -> dict[str, Any]:
    """Lista quality profiles disponibles."""
    params: dict[str, Any] = {}
    if language:
        params["language"] = language
    return _api_get(host_url, api_token, "qualityprofiles/search", params)
