"""Tools de OpenProject: work packages, types, statuses, relations, time entries.

API reference: https://www.openproject.org/docs/api/
OpenProject API v3 usa HAL+JSON (Hypermedia). Los IDs son enteros.
Autenticación: Basic auth con `apikey` como username y el API token como password.
"""

from __future__ import annotations

from typing import Any

import httpx

from mcp_openproject.config import settings
from mcp_shared.errors import ApiAuthenticationError, McpError, NotFoundError


def _client() -> httpx.Client:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if settings.api_token:
        # OpenProject usa Basic auth con apikey
        import base64
        cred = base64.b64encode(f"apikey:{settings.api_token}".encode()).decode()
        headers["Authorization"] = f"Basic {cred}"
    return httpx.Client(
        base_url=settings.api_url,
        headers=headers,
        timeout=settings.default_timeout,
        verify=False,
    )


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


def list_projects(limit: int = 50) -> list[dict[str, Any]]:
    """Lista los proyectos."""
    try:
        with _client() as client:
            resp = client.get("/projects", params={"pageSize": limit})
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("_embedded", {}).get("elements", [])
            return [
                {
                    "id": p.get("id"),
                    "identifier": p.get("identifier", ""),
                    "name": p.get("name", ""),
                    "description": p.get("description", {}).get("raw", "") if isinstance(p.get("description"), dict) else "",
                    "status": p.get("status", ""),
                    "created_at": p.get("createdAt", ""),
                    "updated_at": p.get("updatedAt", ""),
                }
                for p in elements
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


# ---------------------------------------------------------------------------
# Work Packages
# ---------------------------------------------------------------------------


def list_work_packages(
    project_id: int | None = None,
    type_id: int | None = None,
    status_id: int | None = None,
    assignee_id: int | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Lista work packages con filtros opcionales."""
    try:
        with _client() as client:
            params: dict[str, Any] = {"pageSize": limit}
            filters = []
            if project_id is not None:
                filters.append({"project": {"operator": "=", "values": [str(project_id)]}})
            if type_id is not None:
                filters.append({"type": {"operator": "=", "values": [str(type_id)]}})
            if status_id is not None:
                filters.append({"status": {"operator": "=", "values": [str(status_id)]}})
            if assignee_id is not None:
                filters.append({"assignee": {"operator": "=", "values": [str(assignee_id)]}})
            if filters:
                import json
                params["filters"] = json.dumps(filters)
            resp = client.get("/work_packages", params=params)
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("_embedded", {}).get("elements", [])
            return [
                {
                    "id": wp.get("id"),
                    "subject": wp.get("subject", ""),
                    "type": wp.get("_links", {}).get("type", {}).get("title", ""),
                    "status": wp.get("_links", {}).get("status", {}).get("title", ""),
                    "priority": wp.get("_links", {}).get("priority", {}).get("title", ""),
                    "assignee": wp.get("_links", {}).get("assignee", {}).get("title", ""),
                    "project": wp.get("_links", {}).get("project", {}).get("title", ""),
                    "created_at": wp.get("createdAt", ""),
                    "updated_at": wp.get("updatedAt", ""),
                    "start_date": wp.get("startDate", ""),
                    "due_date": wp.get("dueDate", ""),
                }
                for wp in elements
            ]
    except httpx.HTTPStatusError as exc:
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_work_package(work_package_id: int) -> dict[str, Any]:
    """Obtiene el detalle de un work package."""
    try:
        with _client() as client:
            resp = client.get(f"/work_packages/{work_package_id}")
            resp.raise_for_status()
            wp = resp.json()
            return {
                "id": wp.get("id"),
                "subject": wp.get("subject", ""),
                "description": wp.get("description", {}).get("raw", "") if isinstance(wp.get("description"), dict) else "",
                "description_html": wp.get("description", {}).get("html", "") if isinstance(wp.get("description"), dict) else "",
                "type": wp.get("_links", {}).get("type", {}).get("title", ""),
                "status": wp.get("_links", {}).get("status", {}).get("title", ""),
                "priority": wp.get("_links", {}).get("priority", {}).get("title", ""),
                "assignee": wp.get("_links", {}).get("assignee", {}).get("title", ""),
                "project": wp.get("_links", {}).get("project", {}).get("title", ""),
                "created_at": wp.get("createdAt", ""),
                "updated_at": wp.get("updatedAt", ""),
                "start_date": wp.get("startDate", ""),
                "due_date": wp.get("dueDate", ""),
                "estimated_time": wp.get("estimatedTime", ""),
                "spent_time": wp.get("spentTime", ""),
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="work_package", identifier=str(work_package_id)) from exc
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def create_work_package(
    project_id: int,
    subject: str,
    type_id: int | None = None,
    description: str = "",
    assignee_id: int | None = None,
    status_id: int | None = None,
    priority_id: int | None = None,
    start_date: str | None = None,
    due_date: str | None = None,
) -> dict[str, Any]:
    """Crea un work package. Requiere OPENPROJECT_ALLOW_WRITE=true."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece OPENPROJECT_ALLOW_WRITE=true para habilitar.")
    try:
        with _client() as client:
            payload: dict[str, Any] = {
                "subject": subject,
                "_links": {"project": {"href": f"/api/v3/projects/{project_id}"}},
            }
            if description:
                payload["description"] = {"raw": description, "format": "markdown"}
            if type_id is not None:
                payload["_links"]["type"] = {"href": f"/api/v3/types/{type_id}"}
            if assignee_id is not None:
                payload["_links"]["assignee"] = {"href": f"/api/v3/users/{assignee_id}"}
            if status_id is not None:
                payload["_links"]["status"] = {"href": f"/api/v3/statuses/{status_id}"}
            if priority_id is not None:
                payload["_links"]["priority"] = {"href": f"/api/v3/priorities/{priority_id}"}
            if start_date:
                payload["startDate"] = start_date
            if due_date:
                payload["dueDate"] = due_date
            resp = client.post("/work_packages", json=payload)
            resp.raise_for_status()
            wp = resp.json()
            return {
                "id": wp.get("id"),
                "subject": wp.get("subject", ""),
                "type": wp.get("_links", {}).get("type", {}).get("title", ""),
                "status": wp.get("_links", {}).get("status", {}).get("title", ""),
            }
    except httpx.HTTPStatusError as exc:
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def update_work_package(
    work_package_id: int,
    status_id: int | None = None,
    assignee_id: int | None = None,
    type_id: int | None = None,
    priority_id: int | None = None,
    subject: str | None = None,
    description: str | None = None,
    start_date: str | None = None,
    due_date: str | None = None,
) -> dict[str, Any]:
    """Actualiza un work package. Requiere OPENPROJECT_ALLOW_WRITE=true."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece OPENPROJECT_ALLOW_WRITE=true para habilitar.")
    try:
        with _client() as client:
            payload: dict[str, Any] = {"_links": {}}
            if status_id is not None:
                payload["_links"]["status"] = {"href": f"/api/v3/statuses/{status_id}"}
            if assignee_id is not None:
                payload["_links"]["assignee"] = {"href": f"/api/v3/users/{assignee_id}"}
            if type_id is not None:
                payload["_links"]["type"] = {"href": f"/api/v3/types/{type_id}"}
            if priority_id is not None:
                payload["_links"]["priority"] = {"href": f"/api/v3/priorities/{priority_id}"}
            if subject is not None:
                payload["subject"] = subject
            if description is not None:
                payload["description"] = {"raw": description, "format": "markdown"}
            if start_date is not None:
                payload["startDate"] = start_date
            if due_date is not None:
                payload["dueDate"] = due_date
            if not any(payload.get(k) for k in ["subject", "description", "startDate", "dueDate"]) and not payload["_links"]:
                raise McpError("No se proporcionaron campos para actualizar.")
            resp = client.patch(f"/work_packages/{work_package_id}", json=payload)
            resp.raise_for_status()
            wp = resp.json()
            return {
                "id": wp.get("id"),
                "subject": wp.get("subject", ""),
                "status": wp.get("_links", {}).get("status", {}).get("title", ""),
                "type": wp.get("_links", {}).get("type", {}).get("title", ""),
                "updated_at": wp.get("updatedAt", ""),
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="work_package", identifier=str(work_package_id)) from exc
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


# ---------------------------------------------------------------------------
# Types (Task, Bug, Milestone, etc.)
# ---------------------------------------------------------------------------


def list_types() -> list[dict[str, Any]]:
    """Lista los tipos de work package."""
    try:
        with _client() as client:
            resp = client.get("/types")
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("_embedded", {}).get("elements", [])
            return [
                {
                    "id": t.get("id"),
                    "name": t.get("name", ""),
                    "color": t.get("color", ""),
                    "is_default": t.get("isDefault", False),
                    "is_milestone": t.get("isMilestone", False),
                }
                for t in elements
            ]
    except httpx.HTTPStatusError as exc:
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


# ---------------------------------------------------------------------------
# Statuses
# ---------------------------------------------------------------------------


def list_statuses() -> list[dict[str, Any]]:
    """Lista los estados de work package."""
    try:
        with _client() as client:
            resp = client.get("/statuses")
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("_embedded", {}).get("elements", [])
            return [
                {
                    "id": s.get("id"),
                    "name": s.get("name", ""),
                    "color": s.get("color", ""),
                    "is_default": s.get("isDefault", False),
                    "is_closed": s.get("isClosed", False),
                }
                for s in elements
            ]
    except httpx.HTTPStatusError as exc:
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------


def list_relations(work_package_id: int) -> list[dict[str, Any]]:
    """Lista las relaciones de un work package (blocks, blocked_by, relates)."""
    try:
        with _client() as client:
            resp = client.get(f"/work_packages/{work_package_id}/relations")
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("_embedded", {}).get("elements", [])
            return [
                {
                    "id": r.get("id"),
                    "type": r.get("type", ""),
                    "from_id": r.get("fromId"),
                    "to_id": r.get("toId"),
                    "from": r.get("_links", {}).get("from", {}).get("title", ""),
                    "to": r.get("_links", {}).get("to", {}).get("title", ""),
                }
                for r in elements
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="work_package", identifier=str(work_package_id)) from exc
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def create_relation(from_id: int, to_id: int, relation_type: str = "relates") -> dict[str, Any]:
    """Crea una relación entre work packages. Requiere OPENPROJECT_ALLOW_WRITE=true.

    Tipos: relates, blocks, blocked_by, follows, precedes, duplicates, duplicated_by.
    """
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece OPENPROJECT_ALLOW_WRITE=true para habilitar.")
    try:
        with _client() as client:
            payload = {"fromId": from_id, "toId": to_id, "type": relation_type}
            resp = client.post("/relations", json=payload)
            resp.raise_for_status()
            r = resp.json()
            return {
                "id": r.get("id"),
                "type": r.get("type", ""),
                "from_id": r.get("fromId"),
                "to_id": r.get("toId"),
            }
    except httpx.HTTPStatusError as exc:
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


# ---------------------------------------------------------------------------
# Time entries
# ---------------------------------------------------------------------------


def list_time_entries(work_package_id: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Lista entradas de time-tracking."""
    try:
        with _client() as client:
            params: dict[str, Any] = {"pageSize": limit}
            if work_package_id is not None:
                import json
                params["filters"] = json.dumps([{"work_package": {"operator": "=", "values": [str(work_package_id)]}}])
            resp = client.get("/time_entries", params=params)
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("_embedded", {}).get("elements", [])
            return [
                {
                    "id": te.get("id"),
                    "hours": te.get("hours", ""),
                    "spent_on": te.get("spentOn", ""),
                    "activity": te.get("_links", {}).get("activity", {}).get("title", ""),
                    "work_package": te.get("_links", {}).get("workPackage", {}).get("title", ""),
                    "user": te.get("_links", {}).get("user", {}).get("title", ""),
                    "comment": te.get("comment", {}).get("raw", "") if isinstance(te.get("comment"), dict) else "",
                    "created_at": te.get("createdAt", ""),
                }
                for te in elements
            ]
    except httpx.HTTPStatusError as exc:
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def create_time_entry(
    work_package_id: int,
    hours: float,
    spent_on: str,
    activity_id: int | None = None,
    comment: str = "",
) -> dict[str, Any]:
    """Registra tiempo en un work package. Requiere OPENPROJECT_ALLOW_WRITE=true."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece OPENPROJECT_ALLOW_WRITE=true para habilitar.")
    try:
        with _client() as client:
            payload: dict[str, Any] = {
                "hours": f"{hours}h",
                "spentOn": spent_on,
                "_links": {"workPackage": {"href": f"/api/v3/work_packages/{work_package_id}"}},
            }
            if activity_id is not None:
                payload["_links"]["activity"] = {"href": f"/api/v3/time_entry_activities/{activity_id}"}
            if comment:
                payload["comment"] = {"raw": comment, "format": "markdown"}
            resp = client.post("/time_entries", json=payload)
            resp.raise_for_status()
            te = resp.json()
            return {
                "id": te.get("id"),
                "hours": te.get("hours", ""),
                "spent_on": te.get("spentOn", ""),
            }
    except httpx.HTTPStatusError as exc:
        raise McpError(f"OpenProject API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc
