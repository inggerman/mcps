"""Tools de Harbor: projects, repos, tags, scan reports, image existence, delete tags."""

from __future__ import annotations

from typing import Any

import httpx

from mcp_harbor.config import settings
from mcp_shared.errors import ApiAuthenticationError, McpError, NotFoundError


def _client() -> httpx.Client:
    auth = None
    if settings.username and settings.password:
        auth = (settings.username, settings.password)
    return httpx.Client(
        base_url=settings.api_url,
        auth=auth,
        timeout=settings.default_timeout,
        verify=False,
    )


def list_projects() -> list[dict[str, Any]]:
    """Lista todos los proyectos de Harbor."""
    try:
        with _client() as client:
            resp = client.get("/projects")
            resp.raise_for_status()
            return [
                {
                    "project_id": p.get("project_id"),
                    "name": p.get("name", ""),
                    "repo_count": p.get("repo_count", 0),
                    "metadata": p.get("metadata", {}),
                }
                for p in resp.json()
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"Harbor API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def list_repositories(project_name: str) -> list[dict[str, Any]]:
    """Lista los repositorios de un proyecto de Harbor."""
    try:
        with _client() as client:
            resp = client.get(f"/projects/{project_name}/repositories")
            resp.raise_for_status()
            return [
                {
                    "id": r.get("id"),
                    "name": r.get("name", ""),
                    "project_id": r.get("project_id"),
                    "artifact_count": r.get("artifact_count", 0),
                    "pull_count": r.get("pull_count", 0),
                }
                for r in resp.json()
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="project", identifier=project_name) from exc
        raise McpError(f"Harbor API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def list_tags(project_name: str, repo_name: str) -> list[dict[str, Any]]:
    """Lista los tags/artifacts de un repositorio en Harbor."""
    try:
        with _client() as client:
            resp = client.get(f"/projects/{project_name}/repositories/{repo_name}/artifacts")
            resp.raise_for_status()
            artifacts = resp.json()
            result: list[dict[str, Any]] = []
            for a in artifacts:
                tags = a.get("tags", [])
                for tag in tags:
                    result.append({
                        "digest": a.get("digest", ""),
                        "tag": tag.get("name", ""),
                        "size": a.get("size", 0),
                        "push_time": a.get("push_time", ""),
                        "pull_time": a.get("pull_time", ""),
                        "scan_status": a.get("scan_overview", {}).get("scan_status", ""),
                    })
            return result
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="repository", identifier=f"{project_name}/{repo_name}") from exc
        raise McpError(f"Harbor API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_scan_report(project_name: str, repo_name: str, tag: str) -> dict[str, Any]:
    """Obtiene el reporte de scan de vulnerabilidades de un artifact."""
    try:
        with _client() as client:
            resp = client.get(
                f"/projects/{project_name}/repositories/{repo_name}/artifacts/{tag}/additions/vulnerabilities"
            )
            resp.raise_for_status()
            data = resp.json()
            summary = data.get("summary", {})
            return {
                "tag": tag,
                "repository": f"{project_name}/{repo_name}",
                "scan_status": summary.get("scan_status", ""),
                "severity": summary.get("severity", ""),
                "vulnerabilities": {
                    "critical": summary.get("summary", {}).get("Critical", 0),
                    "high": summary.get("summary", {}).get("High", 0),
                    "medium": summary.get("summary", {}).get("Medium", 0),
                    "low": summary.get("summary", {}).get("Low", 0),
                    "none": summary.get("summary", {}).get("None", 0),
                },
                "details": data.get("details", [])[:20],
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="artifact", identifier=f"{project_name}/{repo_name}:{tag}") from exc
        raise McpError(f"Harbor API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def image_exists(project_name: str, repo_name: str, tag: str = "latest") -> bool:
    """Verifica si una imagen existe en Harbor."""
    try:
        with _client() as client:
            resp = client.get(
                f"/projects/{project_name}/repositories/{repo_name}/artifacts/{tag}"
            )
            return resp.status_code == 200
    except httpx.RequestError:
        return False


def delete_tag(project_name: str, repo_name: str, tag: str) -> dict[str, Any]:
    """Elimina un tag de un repositorio en Harbor."""
    if not settings.allow_delete:
        raise McpError("Borrado no permitido. Establece HARBOR_ALLOW_DELETE=true para habilitar.")
    try:
        with _client() as client:
            resp = client.delete(
                f"/projects/{project_name}/repositories/{repo_name}/artifacts/{tag}"
            )
            resp.raise_for_status()
            return {"status": "deleted", "project": project_name, "repo": repo_name, "tag": tag}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="artifact", identifier=f"{project_name}/{repo_name}:{tag}") from exc
        raise McpError(f"Harbor API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc
