"""Tools de image builder: list repos, tags, inspect, scan, vulnerabilities via Harbor API."""

from __future__ import annotations

from typing import Any

import httpx

from mcp_image_builder.config import settings
from mcp_shared.errors import ApiAuthenticationError, McpError, NotFoundError


def _client() -> httpx.Client:
    auth = None
    if settings.harbor_username and settings.harbor_password:
        auth = (settings.harbor_username, settings.harbor_password)
    return httpx.Client(
        base_url=settings.harbor_url,
        auth=auth,
        timeout=settings.default_timeout,
        verify=False,
    )


def list_repositories(project: str | None = None) -> list[dict[str, Any]]:
    """Lista los repositorios en un proyecto de Harbor."""
    proj = project or settings.harbor_project
    try:
        with _client() as client:
            resp = client.get(f"/api/v2.0/projects/{proj}/repositories")
            resp.raise_for_status()
            return [
                {
                    "name": r.get("name", ""),
                    "artifact_count": r.get("artifact_count", 0),
                    "pull_count": r.get("pull_count", 0),
                    "tags_count": r.get("tags_count", 0),
                }
                for r in resp.json()
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"Harbor API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def list_tags(repo_name: str, project: str | None = None) -> list[dict[str, Any]]:
    """Lista los tags/artifacts de un repositorio."""
    proj = project or settings.harbor_project
    try:
        with _client() as client:
            resp = client.get(f"/api/v2.0/projects/{proj}/repositories/{repo_name}/artifacts")
            resp.raise_for_status()
            result: list[dict[str, Any]] = []
            for artifact in resp.json():
                tags = [t.get("name", "") for t in artifact.get("tags", [])]
                result.append({
                    "digest": artifact.get("digest", ""),
                    "type": artifact.get("type", ""),
                    "size": artifact.get("size", 0),
                    "tags": tags,
                    "push_time": artifact.get("push_time", ""),
                    "pull_time": artifact.get("pull_time", ""),
                })
            return result
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="repository", identifier=repo_name) from exc
        raise McpError(f"Harbor API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def inspect_image(repo_name: str, tag_or_digest: str, project: str | None = None) -> dict[str, Any]:
    """Inspecciona un artifact específico por tag o digest."""
    proj = project or settings.harbor_project
    try:
        with _client() as client:
            resp = client.get(
                f"/api/v2.0/projects/{proj}/repositories/{repo_name}/artifacts/{tag_or_digest}"
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "digest": data.get("digest", ""),
                "type": data.get("type", ""),
                "size": data.get("size", 0),
                "tags": [t.get("name", "") for t in data.get("tags", [])],
                "labels": data.get("labels", []),
                "push_time": data.get("push_time", ""),
                "pull_time": data.get("pull_time", ""),
                "extra_attrs": data.get("extra_attrs", {}),
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="image", identifier=f"{repo_name}:{tag_or_digest}") from exc
        raise McpError(f"Harbor API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_image_scan(repo_name: str, tag_or_digest: str, project: str | None = None) -> dict[str, Any]:
    """Obtiene el reporte de scan de un artifact."""
    proj = project or settings.harbor_project
    try:
        with _client() as client:
            resp = client.get(
                f"/api/v2.0/projects/{proj}/repositories/{repo_name}/artifacts/{tag_or_digest}/scan"
            )
            if resp.status_code == 404:
                return {"status": "not_scanned", "repo": repo_name, "reference": tag_or_digest}
            resp.raise_for_status()
            data = resp.json()
            return {
                "status": data.get("status", ""),
                "scan_time": data.get("scan_time", ""),
                "duration": data.get("duration", 0),
                "scanner": data.get("scanner", ""),
            }
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Harbor API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_image_vulnerabilities(repo_name: str, tag_or_digest: str, project: str | None = None) -> dict[str, Any]:
    """Obtiene las vulnerabilidades de un artifact escaneado."""
    proj = project or settings.harbor_project
    try:
        with _client() as client:
            resp = client.get(
                f"/api/v2.0/projects/{proj}/repositories/{repo_name}/artifacts/{tag_or_digest}/scan/vulnerabilities/report"
            )
            if resp.status_code == 404:
                return {"status": "no_report", "vulnerabilities": []}
            resp.raise_for_status()
            data = resp.json()
            summary = data.get("summary", {})
            vulnerabilities = data.get("vulnerabilities", [])
            return {
                "summary": {
                    "critical": summary.get("Critical", 0),
                    "high": summary.get("High", 0),
                    "medium": summary.get("Medium", 0),
                    "low": summary.get("Low", 0),
                    "total": summary.get("Total", 0),
                },
                "vulnerabilities": [
                    {
                        "id": v.get("id", ""),
                        "package": v.get("package", ""),
                        "version": v.get("version", ""),
                        "severity": v.get("severity", ""),
                        "description": v.get("description", "")[:200],
                        "fixed_version": v.get("fixed_version", ""),
                    }
                    for v in vulnerabilities[:50]
                ],
            }
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Harbor API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc
