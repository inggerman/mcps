"""
Lógica de mcp-agent-runner.

Proporciona integración con n8n y ejecución local de scripts asíncronos.
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any

import httpx
from mcp_shared.errors import McpError


async def agent_trigger_webhook(
    webhook_url: str,
    payload: dict[str, Any],
    auth_token: str = ""
) -> dict[str, Any]:
    """Dispara un webhook HTTP (ej. n8n) para iniciar un workflow de agente."""
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(webhook_url, json=payload, headers=headers)

            resp.raise_for_status()

            try:
                data = resp.json()
            except ValueError:
                data = {"raw_text": resp.text}

            return {
                "status": "success",
                "status_code": resp.status_code,
                "response": data
            }
    except httpx.HTTPStatusError as exc:
        raise McpError(f"HTTP Error {exc.response.status_code} llamando a webhook: {exc.response.text}") from exc
    except Exception as exc:
        raise McpError(f"Error llamando a webhook: {exc}") from exc


def agent_run_local(project_path: Path, script_path: str, args: str) -> dict[str, Any]:
    """Ejecuta un script local que representa un sub-agente (ej. python subagent.py)."""
    target = project_path / script_path
    if not target.exists():
        raise McpError(f"El script local no existe: {target}")

    try:
        # Se asume python por defecto para simplificar
        cmd = ["python", str(target), *shlex.split(args)]

        # En la realidad, esto podría ser Popen para no bloquear, pero FastMCP es async
        # Usaremos run con timeout corto (simulación) o se debería usar asyncio.create_subprocess_exec
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=60
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "stdout": result.stdout[:1000],
            "stderr": result.stderr[:1000]
        }
    except subprocess.TimeoutExpired as exc:
        raise McpError("El sub-agente local excedió el tiempo máximo de ejecución.") from exc
    except Exception as exc:
        raise McpError(f"Fallo al ejecutar sub-agente: {exc}") from exc


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------

import asyncio
import json as _json
import time
import uuid


def agent_list_scripts(project_path: Path) -> dict[str, Any]:
    """Lista scripts Python disponibles en el proyecto."""
    scripts = list(project_path.rglob("*.py"))
    return {"count": len(scripts), "scripts": [str(s.relative_to(project_path)) for s in scripts]}


def agent_status(job_id: str) -> dict[str, Any]:
    """Consulta el estado de un job por ID (mock)."""
    if not job_id.strip():
        raise McpError("job_id no puede estar vacio.")
    return {"job_id": job_id, "status": "running", "progress": 50, "message": "Job en progreso (mock)."}


def agent_cancel(job_id: str) -> dict[str, Any]:
    """Cancela un job por ID (mock)."""
    if not job_id.strip():
        raise McpError("job_id no puede estar vacio.")
    return {"job_id": job_id, "status": "cancelled", "message": "Job cancelado (mock)."}


def agent_logs(job_id: str, lines: int = 50) -> dict[str, Any]:
    """Obtiene logs de un job (mock)."""
    if not job_id.strip():
        raise McpError("job_id no puede estar vacio.")
    return {"job_id": job_id, "lines": lines, "logs": f"[mock] Log lines for job {job_id}"}


def agent_results(job_id: str) -> dict[str, Any]:
    """Obtiene resultados de un job completado (mock)."""
    if not job_id.strip():
        raise McpError("job_id no puede estar vacio.")
    return {"job_id": job_id, "status": "completed", "results": {"output": "mock result data"}}


def agent_create_task(name: str, description: str, script_path: str) -> dict[str, Any]:
    """Crea una nueva tarea de agente (mock)."""
    if not name.strip():
        raise McpError("name no puede estar vacio.")
    task_id = str(uuid.uuid4())
    return {"task_id": task_id, "name": name, "description": description, "script": script_path, "status": "created"}


def agent_list_tasks() -> dict[str, Any]:
    """Lista tareas de agentes (mock)."""
    return {"tasks": [], "count": 0, "message": "No hay tareas (mock)."}


def agent_delete_task(task_id: str) -> dict[str, Any]:
    """Elimina una tarea por ID (mock)."""
    if not task_id.strip():
        raise McpError("task_id no puede estar vacio.")
    return {"task_id": task_id, "status": "deleted", "message": "Tarea eliminada (mock)."}


async def agent_trigger_n8n_workflow(workflow_id: str, payload: dict[str, Any], base_url: str, auth_token: str = "") -> dict[str, Any]:
    """Dispara un workflow especifico de n8n."""
    if not workflow_id.strip():
        raise McpError("workflow_id no puede estar vacio.")
    webhook_url = f"{base_url.rstrip('/')}/{workflow_id}"
    return await agent_trigger_webhook(webhook_url, payload, auth_token)


def agent_run_batch(project_path: Path, scripts: list[str], args: str = "") -> dict[str, Any]:
    """Ejecuta multiples scripts en secuencia."""
    results = []
    for script in scripts:
        try:
            result = agent_run_local(project_path, script, args)
            results.append({"script": script, "status": result["status"], "stdout": result.get("stdout", "")})
        except Exception as exc:
            results.append({"script": script, "status": "error", "error": str(exc)})
    return {"batch_size": len(scripts), "results": results}


def agent_health_check(base_url: str) -> dict[str, Any]:
    """Verifica salud del servicio de agentes (n8n)."""
    try:
        response = httpx.get(f"{base_url.rstrip('/')}/healthz", timeout=10)
        return {"status_code": response.status_code, "healthy": response.status_code == 200}
    except Exception as exc:
        return {"status_code": 0, "healthy": False, "error": str(exc)[:100]}


def agent_get_config() -> dict[str, Any]:
    """Retorna la configuracion actual del agent runner."""
    return {
        "webhook_base_url": "http://localhost:5678/webhook",
        "has_auth_token": False,
        "project_path": ".",
        "max_timeout": 60,
    }


def agent_run_with_timeout(project_path: Path, script_path: str, args: str, timeout: int = 30) -> dict[str, Any]:
    """Ejecuta un script local con timeout personalizado."""
    target = project_path / script_path
    if not target.exists():
        raise McpError(f"El script local no existe: {target}")
    try:
        cmd = ["python", str(target), *shlex.split(args)]
        result = subprocess.run(cmd, cwd=str(project_path), capture_output=True, text=True, timeout=timeout)
        return {
            "status": "success" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "stdout": result.stdout[:1000],
            "stderr": result.stderr[:1000],
            "timeout": timeout,
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "timeout": timeout, "message": f"Script excedio timeout de {timeout}s"}
    except Exception as exc:
        raise McpError(f"Fallo al ejecutar script: {exc}") from exc
