"""Tools de Plane: projects, cycles, modules, issues, states, labels.

API reference: https://docs.plane.so/api-reference/
Plane API v1 usa rutas con workspace slug: /workspaces/{slug}/projects/{project_id}/...
"""

from __future__ import annotations

from typing import Any

import httpx

from mcp_plane.config import settings
from mcp_shared.errors import ApiAuthenticationError, McpError, NotFoundError


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


def _workspace() -> str:
    if not settings.workspace_slug:
        raise McpError("Workspace no configurado. Establece PLANE_WORKSPACE_SLUG.")
    return settings.workspace_slug


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


def list_projects(limit: int = 50) -> list[dict[str, Any]]:
    """Lista los proyectos del workspace."""
    try:
        with _client() as client:
            resp = client.get(f"/workspaces/{_workspace()}/projects", params={"limit": limit})
            resp.raise_for_status()
            data = resp.json()
            projects = data if isinstance(data, list) else data.get("results", [])
            return [
                {
                    "id": p.get("id"),
                    "name": p.get("name", ""),
                    "identifier": p.get("identifier", ""),
                    "description": p.get("description", ""),
                    "state": p.get("state", ""),
                    "created_at": p.get("created_at", ""),
                    "updated_at": p.get("updated_at", ""),
                }
                for p in projects
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"Plane API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


# ---------------------------------------------------------------------------
# Cycles (sprints)
# ---------------------------------------------------------------------------


def list_cycles(project_id: str) -> list[dict[str, Any]]:
    """Lista los cycles (sprints) de un proyecto."""
    try:
        with _client() as client:
            resp = client.get(f"/workspaces/{_workspace()}/projects/{project_id}/cycles")
            resp.raise_for_status()
            data = resp.json()
            cycles = data if isinstance(data, list) else data.get("results", [])
            return [
                {
                    "id": c.get("id"),
                    "name": c.get("name", ""),
                    "description": c.get("description", ""),
                    "start_date": c.get("start_date", ""),
                    "end_date": c.get("end_date", ""),
                    "is_active": c.get("is_active", False),
                    "is_favorite": c.get("is_favorite", False),
                    "created_at": c.get("created_at", ""),
                    "updated_at": c.get("updated_at", ""),
                }
                for c in cycles
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="project", identifier=project_id) from exc
        raise McpError(f"Plane API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


# ---------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------


def list_modules(project_id: str) -> list[dict[str, Any]]:
    """Lista los modules de un proyecto."""
    try:
        with _client() as client:
            resp = client.get(f"/workspaces/{_workspace()}/projects/{project_id}/modules")
            resp.raise_for_status()
            data = resp.json()
            modules = data if isinstance(data, list) else data.get("results", [])
            return [
                {
                    "id": m.get("id"),
                    "name": m.get("name", ""),
                    "description": m.get("description", ""),
                    "status": m.get("status", ""),
                    "start_date": m.get("start_date", ""),
                    "target_date": m.get("target_date", ""),
                    "created_at": m.get("created_at", ""),
                    "updated_at": m.get("updated_at", ""),
                }
                for m in modules
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="project", identifier=project_id) from exc
        raise McpError(f"Plane API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------


def list_issues(
    project_id: str,
    state: str | None = None,
    cycle_id: str | None = None,
    module_id: str | None = None,
    assignee: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Lista los issues de un proyecto con filtros opcionales."""
    try:
        params: dict[str, Any] = {"limit": limit}
        if state:
            params["state"] = state
        if assignee:
            params["assignee"] = assignee
        with _client() as client:
            path = f"/workspaces/{_workspace()}/projects/{project_id}/issues"
            if cycle_id:
                path = f"{path}?cycle={cycle_id}"
            resp = client.get(path, params=params)
            resp.raise_for_status()
            data = resp.json()
            issues = data if isinstance(data, list) else data.get("results", [])
            return [
                {
                    "id": i.get("id"),
                    "name": i.get("name", ""),
                    "sequence_id": i.get("sequence_id"),
                    "state": i.get("state", ""),
                    "priority": i.get("priority", ""),
                    "assignees": i.get("assignees", []) or [],
                    "labels": i.get("labels", []) or [],
                    "cycle": i.get("cycle", ""),
                    "module": i.get("module", ""),
                    "created_at": i.get("created_at", ""),
                    "updated_at": i.get("updated_at", ""),
                }
                for i in issues
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="project", identifier=project_id) from exc
        raise McpError(f"Plane API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_issue(project_id: str, issue_id: str) -> dict[str, Any]:
    """Obtiene el detalle de un issue."""
    try:
        with _client() as client:
            resp = client.get(
                f"/workspaces/{_workspace()}/projects/{project_id}/issues/{issue_id}"
            )
            resp.raise_for_status()
            i = resp.json()
            return {
                "id": i.get("id"),
                "name": i.get("name", ""),
                "description_html": i.get("description_html", ""),
                "description_stripped": i.get("description_stripped", ""),
                "sequence_id": i.get("sequence_id"),
                "state": i.get("state", ""),
                "priority": i.get("priority", ""),
                "assignees": i.get("assignees", []) or [],
                "labels": i.get("labels", []) or [],
                "cycle": i.get("cycle", ""),
                "module": i.get("module", ""),
                "parent": i.get("parent", ""),
                "created_at": i.get("created_at", ""),
                "updated_at": i.get("updated_at", ""),
                "created_by": i.get("created_by", ""),
                "updated_by": i.get("updated_by", ""),
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="issue", identifier=f"{project_id}/{issue_id}") from exc
        raise McpError(f"Plane API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def create_issue(
    project_id: str,
    name: str,
    description_html: str = "",
    state: str | None = None,
    priority: str | None = None,
    cycle_id: str | None = None,
    module_id: str | None = None,
    assignees: list[str] | None = None,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Crea un issue en un proyecto. Requiere PLANE_ALLOW_WRITE=true."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece PLANE_ALLOW_WRITE=true para habilitar.")
    try:
        with _client() as client:
            payload: dict[str, Any] = {"name": name, "description_html": description_html}
            if state:
                payload["state"] = state
            if priority:
                payload["priority"] = priority
            if cycle_id:
                payload["cycle"] = cycle_id
            if module_id:
                payload["module"] = module_id
            if assignees:
                payload["assignees"] = assignees
            if labels:
                payload["labels"] = labels
            resp = client.post(
                f"/workspaces/{_workspace()}/projects/{project_id}/issues",
                json=payload,
            )
            resp.raise_for_status()
            i = resp.json()
            return {
                "id": i.get("id"),
                "name": i.get("name", ""),
                "sequence_id": i.get("sequence_id"),
                "state": i.get("state", ""),
                "url": f"{settings.api_url.rsplit('/api/v1', 1)[0]}/{_workspace()}/projects/{project_id}/issues/{i.get('id')}",
            }
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Plane API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def update_issue(
    project_id: str,
    issue_id: str,
    state: str | None = None,
    priority: str | None = None,
    assignees: list[str] | None = None,
    labels: list[str] | None = None,
    cycle_id: str | None = None,
    module_id: str | None = None,
) -> dict[str, Any]:
    """Actualiza un issue. Requiere PLANE_ALLOW_WRITE=true."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece PLANE_ALLOW_WRITE=true para habilitar.")
    try:
        with _client() as client:
            payload: dict[str, Any] = {}
            if state is not None:
                payload["state"] = state
            if priority is not None:
                payload["priority"] = priority
            if assignees is not None:
                payload["assignees"] = assignees
            if labels is not None:
                payload["labels"] = labels
            if cycle_id is not None:
                payload["cycle"] = cycle_id
            if module_id is not None:
                payload["module"] = module_id
            if not payload:
                raise McpError("No se proporcionaron campos para actualizar.")
            resp = client.patch(
                f"/workspaces/{_workspace()}/projects/{project_id}/issues/{issue_id}",
                json=payload,
            )
            resp.raise_for_status()
            i = resp.json()
            return {
                "id": i.get("id"),
                "name": i.get("name", ""),
                "state": i.get("state", ""),
                "priority": i.get("priority", ""),
                "updated_at": i.get("updated_at", ""),
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="issue", identifier=f"{project_id}/{issue_id}") from exc
        raise McpError(f"Plane API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


# ---------------------------------------------------------------------------
# States (workflow)
# ---------------------------------------------------------------------------


def list_states(project_id: str) -> list[dict[str, Any]]:
    """Lista los estados (workflow) de un proyecto."""
    try:
        with _client() as client:
            resp = client.get(f"/workspaces/{_workspace()}/projects/{project_id}/states")
            resp.raise_for_status()
            data = resp.json()
            states = data if isinstance(data, list) else data.get("results", [])
            return [
                {
                    "id": s.get("id"),
                    "name": s.get("name", ""),
                    "color": s.get("color", ""),
                    "group": s.get("group", ""),
                    "default": s.get("default", False),
                    "sequence": s.get("sequence"),
                }
                for s in states
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="project", identifier=project_id) from exc
        raise McpError(f"Plane API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------


def list_labels(project_id: str) -> list[dict[str, Any]]:
    """Lista las labels de un proyecto."""
    try:
        with _client() as client:
            resp = client.get(f"/workspaces/{_workspace()}/projects/{project_id}/labels")
            resp.raise_for_status()
            data = resp.json()
            labels = data if isinstance(data, list) else data.get("results", [])
            return [
                {
                    "id": l.get("id"),
                    "name": l.get("name", ""),
                    "color": l.get("color", ""),
                    "parent": l.get("parent", ""),
                    "sequence": l.get("sequence"),
                }
                for l in labels
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="project", identifier=project_id) from exc
        raise McpError(f"Plane API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc
