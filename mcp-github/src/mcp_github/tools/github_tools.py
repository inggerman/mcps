"""
Lógica de negocio de mcp-github.

Interacciones con la API REST de GitHub usando httpx.
Maneja issues, pull requests y comentarios.
"""

from __future__ import annotations

from typing import Any

import httpx
from mcp_shared.errors import (
    ApiAuthenticationError,
    ApiError,
    NetworkError,
    ValidationError,
)


def _get_client(token: str, api_url: str, timeout: int) -> httpx.Client:
    """Configura y retorna un cliente HTTPX autenticado."""
    if not token:
        raise ValidationError(
            field="token",
            message="No hay token de GitHub configurado. Configura GITHUB_TOKEN en el .env.",
        )

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return httpx.Client(base_url=api_url, headers=headers, timeout=timeout)


def _handle_response(resp: httpx.Response) -> Any:
    """Maneja errores HTTP y devuelve el JSON."""
    if resp.status_code == 401:
        raise ApiAuthenticationError(url=str(resp.url))
    if resp.status_code >= 400:
        raise ApiError(
            url=str(resp.url),
            status_code=resp.status_code,
            response_body=resp.text,
        )
    return resp.json() if resp.text else {}


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------


def create_issue(
    token: str,
    api_url: str,
    timeout: int,
    owner: str,
    repo: str,
    title: str,
    body: str,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Crea un issue en GitHub."""
    if not owner or not repo:
        raise ValidationError(field="owner/repo", message="Se requiere owner y repo.")
    if not title:
        raise ValidationError(field="title", message="El título no puede estar vacío.")

    payload: dict[str, Any] = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.post(f"/repos/{owner}/{repo}/issues", json=payload)
            data = _handle_response(resp)
            return {
                "number": data.get("number"),
                "url": data.get("html_url"),
                "title": data.get("title"),
            }
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def get_issue(
    token: str, api_url: str, timeout: int, owner: str, repo: str, issue_number: int
) -> dict[str, Any]:
    """Obtiene detalles de un issue."""
    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.get(f"/repos/{owner}/{repo}/issues/{issue_number}")
            data = _handle_response(resp)
            return {
                "number": data.get("number"),
                "state": data.get("state"),
                "title": data.get("title"),
                "body": data.get("body"),
                "html_url": data.get("html_url"),
            }
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Pull Requests
# ---------------------------------------------------------------------------


def create_pull_request(
    token: str,
    api_url: str,
    timeout: int,
    owner: str,
    repo: str,
    title: str,
    head: str,
    base: str,
    body: str = "",
) -> dict[str, Any]:
    """Crea un Pull Request."""
    if not head or not base:
        raise ValidationError(field="head/base", message="Se requiere rama base y rama head.")

    payload = {
        "title": title,
        "head": head,
        "base": base,
        "body": body,
    }

    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.post(f"/repos/{owner}/{repo}/pulls", json=payload)
            data = _handle_response(resp)
            return {
                "number": data.get("number"),
                "url": data.get("html_url"),
                "title": data.get("title"),
                "state": data.get("state"),
            }
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def get_pull_request_diff(
    token: str, api_url: str, timeout: int, owner: str, repo: str, pull_number: int
) -> str:
    """Retorna el diff de un PR."""
    try:
        with _get_client(token, api_url, timeout) as client:
            headers = client.headers.copy()
            headers["Accept"] = "application/vnd.github.v3.diff"
            resp = client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}", headers=headers)
            if resp.status_code == 401:
                raise ApiAuthenticationError(url=str(resp.url))
            if resp.status_code >= 400:
                raise ApiError(
                    url=str(resp.url), status_code=resp.status_code, response_body=resp.text
                )
            return resp.text
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Comentarios
# ---------------------------------------------------------------------------


def add_issue_comment(
    token: str, api_url: str, timeout: int, owner: str, repo: str, issue_number: int, body: str
) -> dict[str, Any]:
    """Agrega un comentario a un issue o PR."""
    payload = {"body": body}
    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.post(
                f"/repos/{owner}/{repo}/issues/{issue_number}/comments", json=payload
            )
            data = _handle_response(resp)
            return {
                "id": data.get("id"),
                "url": data.get("html_url"),
            }
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def list_issues(
    token: str, api_url: str, timeout: int, owner: str, repo: str,
    state: str = "open", per_page: int = 30,
) -> list[dict[str, Any]]:
    """Lista issues de un repositorio."""
    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.get(
                f"/repos/{owner}/{repo}/issues",
                params={"state": state, "per_page": min(per_page, 100)},
            )
            data = _handle_response(resp)
            return [
                {
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "url": item.get("html_url"),
                    "labels": [l["name"] for l in item.get("labels", [])],
                }
                for item in data
            ]
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def list_branches(
    token: str, api_url: str, timeout: int, owner: str, repo: str,
    per_page: int = 30,
) -> list[dict[str, Any]]:
    """Lista branches de un repositorio."""
    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.get(
                f"/repos/{owner}/{repo}/branches",
                params={"per_page": min(per_page, 100)},
            )
            data = _handle_response(resp)
            return [
                {
                    "name": item.get("name"),
                    "protected": item.get("protected", False),
                    "commit_sha": item.get("commit", {}).get("sha"),
                }
                for item in data
            ]
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def list_commits(
    token: str, api_url: str, timeout: int, owner: str, repo: str,
    sha: str | None = None, per_page: int = 30,
) -> list[dict[str, Any]]:
    """Lista commits de un repositorio."""
    try:
        with _get_client(token, api_url, timeout) as client:
            params: dict[str, Any] = {"per_page": min(per_page, 100)}
            if sha:
                params["sha"] = sha
            resp = client.get(f"/repos/{owner}/{repo}/commits", params=params)
            data = _handle_response(resp)
            return [
                {
                    "sha": item.get("sha"),
                    "message": item.get("commit", {}).get("message", ""),
                    "author": item.get("commit", {}).get("author", {}).get("name"),
                    "date": item.get("commit", {}).get("author", {}).get("date"),
                    "url": item.get("html_url"),
                }
                for item in data
            ]
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def get_file_content(
    token: str, api_url: str, timeout: int, owner: str, repo: str, path: str,
    ref: str | None = None,
) -> dict[str, Any]:
    """Obtiene el contenido de un archivo del repositorio."""
    try:
        with _get_client(token, api_url, timeout) as client:
            params: dict[str, Any] = {}
            if ref:
                params["ref"] = ref
            resp = client.get(f"/repos/{owner}/{repo}/contents/{path}", params=params)
            data = _handle_response(resp)
            import base64
            content = ""
            if data.get("encoding") == "base64":
                content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
            return {
                "path": data.get("path"),
                "type": data.get("type"),
                "size": data.get("size"),
                "content": content,
                "encoding": data.get("encoding"),
                "url": data.get("html_url"),
            }
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def get_repo_info(
    token: str, api_url: str, timeout: int, owner: str, repo: str,
) -> dict[str, Any]:
    """Obtiene informacion del repositorio."""
    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.get(f"/repos/{owner}/{repo}")
            data = _handle_response(resp)
            return {
                "name": data.get("name"),
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "private": data.get("private"),
                "default_branch": data.get("default_branch"),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "open_issues": data.get("open_issues_count"),
                "language": data.get("language"),
                "url": data.get("html_url"),
                "clone_url": data.get("clone_url"),
            }
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def get_user_info(
    token: str, api_url: str, timeout: int, username: str,
) -> dict[str, Any]:
    """Obtiene informacion de un usuario de GitHub."""
    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.get(f"/users/{username}")
            data = _handle_response(resp)
            return {
                "login": data.get("login"),
                "name": data.get("name"),
                "company": data.get("company"),
                "blog": data.get("blog"),
                "location": data.get("location"),
                "public_repos": data.get("public_repos"),
                "followers": data.get("followers"),
                "following": data.get("following"),
                "url": data.get("html_url"),
            }
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def list_pull_requests(
    token: str, api_url: str, timeout: int, owner: str, repo: str,
    state: str = "open", per_page: int = 30,
) -> list[dict[str, Any]]:
    """Lista pull requests de un repositorio."""
    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.get(
                f"/repos/{owner}/{repo}/pulls",
                params={"state": state, "per_page": min(per_page, 100)},
            )
            data = _handle_response(resp)
            return [
                {
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "head": item.get("head", {}).get("ref"),
                    "base": item.get("base", {}).get("ref"),
                    "url": item.get("html_url"),
                    "draft": item.get("draft", False),
                }
                for item in data
            ]
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def get_pull_request_files(
    token: str, api_url: str, timeout: int, owner: str, repo: str, pull_number: int,
) -> list[dict[str, Any]]:
    """Obtiene los archivos modificados en un pull request."""
    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}/files")
            data = _handle_response(resp)
            return [
                {
                    "filename": item.get("filename"),
                    "status": item.get("status"),
                    "additions": item.get("additions"),
                    "deletions": item.get("deletions"),
                    "changes": item.get("changes"),
                    "patch": item.get("patch", ""),
                }
                for item in data
            ]
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def create_branch(
    token: str, api_url: str, timeout: int, owner: str, repo: str,
    branch_name: str, from_branch: str = "main",
) -> dict[str, Any]:
    """Crea una nueva branch desde una branch existente."""
    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.get(f"/repos/{owner}/{repo}/git/refs/heads/{from_branch}")
            sha = _handle_response(resp)["object"]["sha"]
            resp = client.post(
                f"/repos/{owner}/{repo}/git/refs",
                json={"ref": f"refs/heads/{branch_name}", "sha": sha},
            )
            data = _handle_response(resp)
            return {
                "ref": data.get("ref"),
                "sha": data.get("object", {}).get("sha"),
                "created": True,
            }
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc


def get_issue_comments(
    token: str, api_url: str, timeout: int, owner: str, repo: str, issue_number: int,
    per_page: int = 30,
) -> list[dict[str, Any]]:
    """Obtiene los comentarios de un issue."""
    try:
        with _get_client(token, api_url, timeout) as client:
            resp = client.get(
                f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
                params={"per_page": min(per_page, 100)},
            )
            data = _handle_response(resp)
            return [
                {
                    "id": item.get("id"),
                    "author": item.get("user", {}).get("login"),
                    "body": item.get("body"),
                    "created_at": item.get("created_at"),
                    "url": item.get("html_url"),
                }
                for item in data
            ]
    except httpx.RequestError as exc:
        raise NetworkError(url=str(exc.request.url), detail=str(exc)) from exc
