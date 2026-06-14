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
