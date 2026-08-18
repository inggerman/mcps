"""Tools de Gitea: repos, PRs, issues, workflow runs, logs."""

from __future__ import annotations

from typing import Any

import httpx

from mcp_gitea.config import settings
from mcp_shared.errors import ApiAuthenticationError, McpError, NotFoundError


def _client() -> httpx.Client:
    headers = {"Content-Type": "application/json"}
    if settings.api_token:
        headers["Authorization"] = f"token {settings.api_token}"
    return httpx.Client(
        base_url=settings.api_url,
        headers=headers,
        timeout=settings.default_timeout,
        verify=False,
    )


def list_repos(limit: int = 50) -> list[dict[str, Any]]:
    """Lista los repositorios accesibles en Gitea."""
    try:
        with _client() as client:
            resp = client.get("/repos", params={"limit": limit})
            resp.raise_for_status()
            return [
                {
                    "id": r.get("id"),
                    "name": r.get("name", ""),
                    "full_name": r.get("full_name", ""),
                    "owner": r.get("owner", {}).get("login", ""),
                    "private": r.get("private", False),
                    "stars": r.get("stars_count", 0),
                    "forks": r.get("forks_count", 0),
                    "default_branch": r.get("default_branch", ""),
                    "updated_at": r.get("updated_at", ""),
                }
                for r in resp.json()
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"Gitea API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def list_prs(owner: str, repo: str, state: str = "open") -> list[dict[str, Any]]:
    """Lista los pull requests de un repositorio."""
    try:
        with _client() as client:
            resp = client.get(f"/repos/{owner}/{repo}/pulls", params={"state": state})
            resp.raise_for_status()
            return [
                {
                    "number": p.get("number"),
                    "title": p.get("title", ""),
                    "state": p.get("state", ""),
                    "user": p.get("user", {}).get("login", ""),
                    "merged": p.get("merged", False),
                    "mergeable": p.get("mergeable"),
                    "created_at": p.get("created_at", ""),
                    "updated_at": p.get("updated_at", ""),
                    "head": p.get("head", {}).get("ref", ""),
                    "base": p.get("base", {}).get("ref", ""),
                }
                for p in resp.json()
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="repo", identifier=f"{owner}/{repo}") from exc
        raise McpError(f"Gitea API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def create_pr(owner: str, repo: str, title: str, head: str, base: str, body: str = "") -> dict[str, Any]:
    """Crea un pull request en un repositorio."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece GITEA_ALLOW_WRITE=true para habilitar.")
    try:
        with _client() as client:
            payload = {"title": title, "head": head, "base": base, "body": body}
            resp = client.post(f"/repos/{owner}/{repo}/pulls", json=payload)
            resp.raise_for_status()
            p = resp.json()
            return {
                "number": p.get("number"),
                "title": p.get("title", ""),
                "state": p.get("state", ""),
                "url": p.get("html_url", ""),
            }
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Gitea API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def list_issues(owner: str, repo: str, state: str = "open") -> list[dict[str, Any]]:
    """Lista los issues de un repositorio."""
    try:
        with _client() as client:
            resp = client.get(f"/repos/{owner}/{repo}/issues", params={"state": state})
            resp.raise_for_status()
            return [
                {
                    "number": i.get("number"),
                    "title": i.get("title", ""),
                    "state": i.get("state", ""),
                    "user": i.get("user", {}).get("login", ""),
                    "labels": [l.get("name", "") for l in i.get("labels", [])],
                    "created_at": i.get("created_at", ""),
                    "updated_at": i.get("updated_at", ""),
                    "assignee": i.get("assignee", {}).get("login", "") if i.get("assignee") else "",
                }
                for i in resp.json()
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="repo", identifier=f"{owner}/{repo}") from exc
        raise McpError(f"Gitea API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def create_issue(owner: str, repo: str, title: str, body: str = "") -> dict[str, Any]:
    """Crea un issue en un repositorio."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece GITEA_ALLOW_WRITE=true para habilitar.")
    try:
        with _client() as client:
            payload = {"title": title, "body": body}
            resp = client.post(f"/repos/{owner}/{repo}/issues", json=payload)
            resp.raise_for_status()
            i = resp.json()
            return {
                "number": i.get("number"),
                "title": i.get("title", ""),
                "state": i.get("state", ""),
                "url": i.get("html_url", ""),
            }
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Gitea API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_workflow_runs(owner: str, repo: str, limit: int = 20) -> list[dict[str, Any]]:
    """Lista las ejecuciones de Gitea Actions de un repositorio."""
    try:
        with _client() as client:
            resp = client.get(f"/repos/{owner}/{repo}/actions/runs", params={"limit": limit})
            resp.raise_for_status()
            data = resp.json()
            runs = data.get("workflow_runs", data) if isinstance(data, dict) else data
            return [
                {
                    "id": r.get("id"),
                    "name": r.get("name", ""),
                    "status": r.get("status", ""),
                    "conclusion": r.get("conclusion", ""),
                    "event": r.get("event", ""),
                    "head_branch": r.get("head_branch", ""),
                    "created_at": r.get("created_at", ""),
                    "html_url": r.get("html_url", ""),
                }
                for r in runs
            ]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="repo", identifier=f"{owner}/{repo}") from exc
        raise McpError(f"Gitea API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_run_logs(owner: str, repo: str, run_id: int) -> dict[str, Any]:
    """Obtiene los logs de una ejecución de Gitea Actions."""
    try:
        with _client() as client:
            resp = client.get(f"/repos/{owner}/{repo}/actions/runs/{run_id}/logs")
            if resp.status_code == 200 and "text" in resp.headers.get("content-type", ""):
                return {"run_id": run_id, "logs": resp.text[:5000]}
            resp.raise_for_status()
            return {"run_id": run_id, "data": resp.json()}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="workflow run", identifier=str(run_id)) from exc
        raise McpError(f"Gitea API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc
