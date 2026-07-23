"""
Lógica de mcp-snyk.

Ejecuta comandos simulados o reales de Snyk CLI.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from mcp_shared.errors import McpError


def snyk_test(project_path: Path, api_token: str) -> dict[str, Any]:
    """Ejecuta snyk test en el proyecto."""
    snyk_bin = shutil.which("snyk")

    if not snyk_bin:
        # Modo fallback/mock si no está snyk instalado
        return {
            "mode": "mock",
            "status": "success",
            "vulnerabilities": [
                {
                    "title": "Mock Vulnerability: Cross-Site Scripting (XSS)",
                    "severity": "high",
                    "package": "express",
                    "version": "4.17.1",
                }
            ],
            "message": "Snyk CLI no encontrado. Retornando datos mock."
        }

    env = None
    if api_token:
        import os
        env = os.environ.copy()
        env["SNYK_TOKEN"] = api_token

    try:
        result = subprocess.run(
            [snyk_bin, "test", "--json"],
            cwd=str(project_path),
            capture_output=True,
            text=True,
            env=env
        )

        # Snyk test returns 0 if no vulns, 1 if vulns found, 2 for error
        if result.returncode > 1 and not result.stdout.strip():
            raise McpError(f"Error ejecutando snyk: {result.stderr}")

        data = json.loads(result.stdout)
        # Snyk json can be an array (multi-project) or dict
        if isinstance(data, dict):
            data = [data]

        vulns = []
        for project in data:
            for v in project.get("vulnerabilities", []):
                vulns.append({
                    "title": v.get("title"),
                    "severity": v.get("severity"),
                    "package": v.get("packageName"),
                    "version": v.get("version"),
                })

        return {
            "mode": "real",
            "status": "success",
            "vulnerabilities": vulns
        }
    except Exception as exc:
        raise McpError(f"Fallo en snyk test: {exc}") from exc


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def _run_snyk(project_path: Path, args: list[str], api_token: str) -> dict[str, Any]:
    snyk_bin = shutil.which("snyk")
    if not snyk_bin:
        return {"mode": "mock", "status": "success", "output": f"Mock snyk {' '.join(args)}", "message": "Snyk CLI no encontrado."}
    import os
    env = os.environ.copy()
    if api_token:
        env["SNYK_TOKEN"] = api_token
    try:
        result = subprocess.run([snyk_bin, *args], cwd=str(project_path), capture_output=True, text=True, env=env)
        return {"mode": "real", "status": "success" if result.returncode <= 1 else "error", "output": result.stdout[:2000], "error": result.stderr[:1000] if result.stderr else None}
    except Exception as exc:
        raise McpError(f"Fallo en snyk: {exc}") from exc


def snyk_auth(api_token: str) -> dict[str, Any]:
    """Autentica con Snyk usando el API token."""
    if not api_token.strip():
        raise McpError("API token no puede estar vacio.")
    snyk_bin = shutil.which("snyk")
    if not snyk_bin:
        return {"mode": "mock", "status": "success", "message": "Snyk CLI no encontrado. Mock auth."}
    try:
        import os
        env = os.environ.copy()
        env["SNYK_TOKEN"] = api_token
        result = subprocess.run([snyk_bin, "auth", api_token], capture_output=True, text=True, env=env)
        return {"mode": "real", "status": "success" if result.returncode == 0 else "error", "output": result.stdout[:500]}
    except Exception as exc:
        raise McpError(f"Fallo en snyk auth: {exc}") from exc


def snyk_monitor(project_path: Path, api_token: str) -> dict[str, Any]:
    """Ejecuta snyk monitor para registrar el proyecto."""
    return _run_snyk(project_path, ["monitor", "--json"], api_token)


def snyk_code_test(project_path: Path, api_token: str) -> dict[str, Any]:
    """Ejecuta snyk code test para SAST."""
    return _run_snyk(project_path, ["code", "test", "--json"], api_token)


def snyk_iac_test(project_path: Path, api_token: str) -> dict[str, Any]:
    """Ejecuta snyk iac test para Infraestructura como Código."""
    return _run_snyk(project_path, ["iac", "test", "--json"], api_token)


def snyk_container_test(image: str, api_token: str) -> dict[str, Any]:
    """Ejecuta snyk container test para imagenes Docker."""
    if not image.strip():
        raise McpError("image no puede estar vacio.")
    snyk_bin = shutil.which("snyk")
    if not snyk_bin:
        return {"mode": "mock", "status": "success", "image": image, "vulnerabilities": [], "message": "Snyk CLI no encontrado."}
    import os
    env = os.environ.copy()
    if api_token:
        env["SNYK_TOKEN"] = api_token
    try:
        result = subprocess.run([snyk_bin, "container", "test", image, "--json"], capture_output=True, text=True, env=env)
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        vulns = data.get("vulnerabilities", [])
        return {"mode": "real", "status": "success", "image": image, "vulnerabilities": vulns}
    except Exception as exc:
        raise McpError(f"Fallo en snyk container test: {exc}") from exc


def snyk_ignore(project_path: Path, issue_id: str, api_token: str) -> dict[str, Any]:
    """Ignora una vulnerabilidad especifica por issue ID."""
    if not issue_id.strip():
        raise McpError("issue_id no puede estar vacio.")
    return _run_snyk(project_path, ["ignore", issue_id], api_token)


def snyk_policy(project_path: Path, api_token: str) -> dict[str, Any]:
    """Muestra el .snyk policy file."""
    return _run_snyk(project_path, ["policy", "--json"], api_token)


def snyk_projects(api_token: str) -> dict[str, Any]:
    """Lista proyectos de Snyk."""
    snyk_bin = shutil.which("snyk")
    if not snyk_bin:
        return {"mode": "mock", "status": "success", "projects": [], "message": "Snyk CLI no encontrado."}
    import os
    env = os.environ.copy()
    if api_token:
        env["SNYK_TOKEN"] = api_token
    try:
        result = subprocess.run([snyk_bin, "projects", "--json"], capture_output=True, text=True, env=env)
        data = json.loads(result.stdout) if result.stdout.strip() else {"projects": []}
        return {"mode": "real", "status": "success", "projects": data.get("projects", [])}
    except Exception as exc:
        raise McpError(f"Fallo en snyk projects: {exc}") from exc


def snyk_org_list(api_token: str) -> dict[str, Any]:
    """Lista organizaciones de Snyk."""
    snyk_bin = shutil.which("snyk")
    if not snyk_bin:
        return {"mode": "mock", "status": "success", "orgs": [], "message": "Snyk CLI no encontrado."}
    import os
    env = os.environ.copy()
    if api_token:
        env["SNYK_TOKEN"] = api_token
    try:
        result = subprocess.run([snyk_bin, "orgs", "--json"], capture_output=True, text=True, env=env)
        data = json.loads(result.stdout) if result.stdout.strip() else {"orgs": []}
        return {"mode": "real", "status": "success", "orgs": data.get("orgs", [])}
    except Exception as exc:
        raise McpError(f"Fallo en snyk orgs: {exc}") from exc


def snyk_test_severity_filter(project_path: Path, severity: str, api_token: str) -> dict[str, Any]:
    """Ejecuta snyk test filtrando por severidad."""
    if severity not in {"low", "medium", "high", "critical"}:
        raise McpError("severity debe ser: low, medium, high o critical.")
    return _run_snyk(project_path, ["test", "--severity-threshold=" + severity, "--json"], api_token)


def snyk_test_file(file_path: Path, api_token: str) -> dict[str, Any]:
    """Ejecuta snyk test en un archivo especifico."""
    if not file_path.exists():
        raise McpError(f"Archivo no encontrado: {file_path}")
    return _run_snyk(file_path.parent, ["test", "--file=" + file_path.name, "--json"], api_token)


def snyk_dependency_tree(project_path: Path, api_token: str) -> dict[str, Any]:
    """Muestra el arbol de dependencias."""
    return _run_snyk(project_path, ["test", "--print-deps", "--json"], api_token)


def snyk_wizard(project_path: Path, api_token: str) -> dict[str, Any]:
    """Ejecuta snyk wizard para crear .snyk policy file."""
    return _run_snyk(project_path, ["wizard"], api_token)


def snyk_log4shell(project_path: Path, api_token: str) -> dict[str, Any]:
    """Ejecuta snyk test para detectar Log4Shell."""
    return _run_snyk(project_path, ["test", "--log4shell", "--json"], api_token)
