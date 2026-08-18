"""Tools de ArgoCD: list apps, sync status, force sync, diffs, history, rollback."""

from __future__ import annotations

from typing import Any

import httpx

from mcp_argocd.config import settings
from mcp_shared.errors import ApiAuthenticationError, McpError, NetworkError, NotFoundError


def _client() -> httpx.Client:
    headers = {"Content-Type": "application/json"}
    if settings.api_token:
        headers["Authorization"] = f"Bearer {settings.api_token}"
    return httpx.Client(
        base_url=settings.api_url,
        headers=headers,
        timeout=settings.default_timeout,
        verify=False,
    )


def list_apps(project: str | None = None) -> list[dict[str, Any]]:
    """Lista todas las aplicaciones de ArgoCD, opcionalmente filtradas por proyecto."""
    try:
        with _client() as client:
            params: dict[str, Any] = {}
            if project:
                params["project"] = project
            resp = client.get("/api/v1/applications", params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            return [
                {
                    "name": a.get("metadata", {}).get("name", ""),
                    "project": a.get("spec", {}).get("project", ""),
                    "sync_status": a.get("status", {}).get("sync", {}).get("status", ""),
                    "health_status": a.get("status", {}).get("health", {}).get("status", ""),
                    "target_revision": a.get("status", {}).get("sync", {}).get("revision", ""),
                }
                for a in items
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"ArgoCD API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.api_url, reason=str(exc)) from exc


def get_app_status(app_name: str) -> dict[str, Any]:
    """Obtiene el estado detallado de una aplicación de ArgoCD."""
    try:
        with _client() as client:
            resp = client.get(f"/api/v1/applications/{app_name}")
            resp.raise_for_status()
            a = resp.json()
            return {
                "name": a.get("metadata", {}).get("name", ""),
                "project": a.get("spec", {}).get("project", ""),
                "sync_status": a.get("status", {}).get("sync", {}).get("status", ""),
                "health_status": a.get("status", {}).get("health", {}).get("status", ""),
                "health_message": a.get("status", {}).get("health", {}).get("message", ""),
                "target_revision": a.get("status", {}).get("sync", {}).get("revision", ""),
                "source": a.get("spec", {}).get("source", {}),
                "destination": a.get("spec", {}).get("destination", {}),
                "resources": a.get("status", {}).get("resources", []),
                "conditions": a.get("status", {}).get("conditions", []),
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="application", identifier=app_name) from exc
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"ArgoCD API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.api_url, reason=str(exc)) from exc


def sync_app(app_name: str, revision: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Fuerza la sincronización de una aplicación de ArgoCD."""
    if not settings.allow_sync and not dry_run:
        raise McpError("Sync no permitido. Establece ARGOCD_ALLOW_SYNC=true para habilitar.")
    try:
        with _client() as client:
            payload: dict[str, Any] = {"name": app_name, "dryRun": dry_run}
            if revision:
                payload["revision"] = revision
            resp = client.post(f"/api/v1/applications/{app_name}/sync", json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="application", identifier=app_name) from exc
        raise McpError(f"ArgoCD API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.api_url, reason=str(exc)) from exc


def get_app_diff(app_name: str, revision: str | None = None) -> dict[str, Any]:
    """Obtiene el diff entre el estado deseado y el actual de una aplicación."""
    try:
        with _client() as client:
            params: dict[str, Any] = {}
            if revision:
                params["revision"] = revision
            resp = client.get(f"/api/v1/applications/{app_name}/managed-resources", params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="application", identifier=app_name) from exc
        raise McpError(f"ArgoCD API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.api_url, reason=str(exc)) from exc


def get_app_history(app_name: str) -> list[dict[str, Any]]:
    """Obtiene el historial de sincronizaciones de una aplicación."""
    try:
        with _client() as client:
            resp = client.get(f"/api/v1/applications/{app_name}/history")
            resp.raise_for_status()
            return resp.json().get("history", [])
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="application", identifier=app_name) from exc
        raise McpError(f"ArgoCD API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.api_url, reason=str(exc)) from exc


def rollback_app(app_name: str, revision_index: int) -> dict[str, Any]:
    """Hace rollback de una aplicación a una revisión anterior del historial."""
    if not settings.allow_rollback:
        raise McpError("Rollback no permitido. Establece ARGOCD_ALLOW_ROLLBACK=true para habilitar.")
    try:
        with _client() as client:
            payload = {"name": app_name, "revision": revision_index}
            resp = client.post(f"/api/v1/applications/{app_name}/rollback", json=payload)
            resp.raise_for_status()
            return {"status": "rollback initiated", "app": app_name, "revision_index": revision_index}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="application", identifier=app_name) from exc
        raise McpError(f"ArgoCD API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=settings.api_url, reason=str(exc)) from exc
