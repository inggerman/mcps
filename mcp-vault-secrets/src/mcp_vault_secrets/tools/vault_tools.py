"""Tools de Vault: status, mounts, list/read secrets KV-v2 with allowlist."""

from __future__ import annotations

from typing import Any

import httpx

from mcp_vault_secrets.config import settings
from mcp_shared.errors import ApiAuthenticationError, McpError, NotFoundError, ValidationError


def _client() -> httpx.Client:
    headers = {"Content-Type": "application/json"}
    if settings.token:
        headers["X-Vault-Token"] = settings.token
    return httpx.Client(
        base_url=settings.api_url,
        headers=headers,
        timeout=settings.default_timeout,
        verify=False,
    )


def _check_path_allowed(path: str) -> None:
    if not settings.allowed_path_list:
        return
    for prefix in settings.allowed_path_list:
        if path.startswith(prefix):
            return
    raise ValidationError(field="path", message=f"Path '{path}' no está en la allowlist.", value=path)


def vault_status() -> dict[str, Any]:
    """Obtiene el estado del seal de Vault."""
    try:
        with _client() as client:
            resp = client.get("/v1/sys/seal-status")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Vault API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def list_mounts() -> dict[str, Any]:
    """Lista los secret mounts de Vault."""
    try:
        with _client() as client:
            resp = client.get("/v1/sys/mounts")
            resp.raise_for_status()
            data = resp.json()
            return {k: {"type": v.get("type", ""), "version": v.get("options", {}).get("version", "")} for k, v in data.items()}
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"Vault API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def list_secrets(path: str) -> list[str]:
    """Lista las claves en un path de Vault KV-v2."""
    _check_path_allowed(path)
    try:
        with _client() as client:
            resp = client.list(f"/v1/{path}/metadata")
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            return resp.json().get("data", {}).get("keys", [])
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Vault API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def read_secret(path: str, version: int | None = None) -> dict[str, Any]:
    """Lee un secreto de Vault KV-v2."""
    _check_path_allowed(path)
    try:
        with _client() as client:
            params: dict[str, Any] = {}
            if version is not None:
                params["version"] = version
            resp = client.get(f"/v1/{path}/data", params=params)
            if resp.status_code == 404:
                raise NotFoundError(resource="secret", identifier=path) from None
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return {
                "path": path,
                "data": data.get("data", {}),
                "metadata": data.get("metadata", {}),
                "version": version,
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"Vault API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_secret_metadata(path: str) -> dict[str, Any]:
    """Obtiene los metadatos de un secreto KV-v2 (versiones, timestamps)."""
    _check_path_allowed(path)
    try:
        with _client() as client:
            resp = client.get(f"/v1/{path}/metadata")
            if resp.status_code == 404:
                raise NotFoundError(resource="secret metadata", identifier=path) from None
            resp.raise_for_status()
            return resp.json().get("data", {})
    except httpx.HTTPStatusError as exc:
        raise McpError(f"Vault API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc
