"""Tools de n8n: workflows, webhooks, executions, activate."""

from __future__ import annotations

from typing import Any

import httpx

from mcp_n8n.config import settings
from mcp_shared.errors import ApiAuthenticationError, McpError, NotFoundError


def _client() -> httpx.Client:
    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["X-N8N-API-KEY"] = settings.api_key
    return httpx.Client(
        base_url=settings.api_url,
        headers=headers,
        timeout=settings.default_timeout,
        verify=False,
    )


def list_workflows() -> list[dict[str, Any]]:
    """Lista todos los workflows de n8n."""
    try:
        with _client() as client:
            resp = client.get("/workflows")
            resp.raise_for_status()
            data = resp.json()
            workflows = data.get("data", data) if isinstance(data, dict) else data
            return [
                {
                    "id": w.get("id"),
                    "name": w.get("name", ""),
                    "active": w.get("active", False),
                    "nodes": len(w.get("nodes", [])),
                    "created_at": w.get("createdAt", ""),
                    "updated_at": w.get("updatedAt", ""),
                }
                for w in workflows
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"n8n API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_workflow(workflow_id: str) -> dict[str, Any]:
    """Obtiene los detalles de un workflow de n8n."""
    try:
        with _client() as client:
            resp = client.get(f"/workflows/{workflow_id}")
            resp.raise_for_status()
            w = resp.json()
            return {
                "id": w.get("id"),
                "name": w.get("name", ""),
                "active": w.get("active", False),
                "nodes": w.get("nodes", []),
                "connections": w.get("connections", {}),
                "settings": w.get("settings", {}),
                "created_at": w.get("createdAt", ""),
                "updated_at": w.get("updatedAt", ""),
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="workflow", identifier=workflow_id) from exc
        raise McpError(f"n8n API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def trigger_webhook(webhook_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dispara un webhook de n8n."""
    try:
        url = f"{settings.webhook_base_url}/{webhook_id}"
        resp = httpx.post(url, json=data or {}, timeout=settings.default_timeout, verify=False)
        return {
            "webhook_id": webhook_id,
            "status_code": resp.status_code,
            "response": resp.text[:2000] if resp.text else "",
        }
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def list_executions(limit: int = 20) -> list[dict[str, Any]]:
    """Lista las ejecuciones recientes de n8n."""
    try:
        with _client() as client:
            resp = client.get("/executions", params={"limit": limit})
            resp.raise_for_status()
            data = resp.json()
            execs = data.get("data", data) if isinstance(data, dict) else data
            return [
                {
                    "id": e.get("id"),
                    "workflow_id": e.get("workflowId", ""),
                    "status": e.get("status", ""),
                    "mode": e.get("mode", ""),
                    "started_at": e.get("startedAt", ""),
                    "stopped_at": e.get("stoppedAt", ""),
                    "finished": e.get("finished", False),
                }
                for e in execs
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"n8n API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_execution_detail(execution_id: str) -> dict[str, Any]:
    """Obtiene los detalles de una ejecución de n8n."""
    try:
        with _client() as client:
            resp = client.get(f"/executions/{execution_id}")
            resp.raise_for_status()
            e = resp.json()
            return {
                "id": e.get("id"),
                "workflow_id": e.get("workflowId", ""),
                "status": e.get("status", ""),
                "mode": e.get("mode", ""),
                "started_at": e.get("startedAt", ""),
                "stopped_at": e.get("stoppedAt", ""),
                "finished": e.get("finished", False),
                "data": e.get("data", {}),
                "error": e.get("error"),
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="execution", identifier=execution_id) from exc
        raise McpError(f"n8n API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def activate_workflow(workflow_id: str, active: bool = True) -> dict[str, Any]:
    """Activa o desactiva un workflow de n8n."""
    if not settings.allow_activate:
        raise McpError("Activación no permitida. Establece N8N_ALLOW_ACTIVATE=true para habilitar.")
    try:
        with _client() as client:
            resp = client.patch(f"/workflows/{workflow_id}", json={"active": active})
            resp.raise_for_status()
            return {"workflow_id": workflow_id, "active": active, "status": "updated"}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="workflow", identifier=workflow_id) from exc
        raise McpError(f"n8n API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc
