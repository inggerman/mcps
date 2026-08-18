"""Tools de RabbitMQ: overview, queues, exchanges, messages (publish gated)."""

from __future__ import annotations

from typing import Any

import httpx

from mcp_rabbitmq.config import settings
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


def get_overview() -> dict[str, Any]:
    """Obtiene el overview del cluster RabbitMQ."""
    try:
        with _client() as client:
            resp = client.get("/overview")
            resp.raise_for_status()
            data = resp.json()
            return {
                "rabbitmq_version": data.get("rabbitmq_version", ""),
                "cluster_name": data.get("cluster_name", ""),
                "erlang_version": data.get("erlang_version", ""),
                "management_version": data.get("management_version", ""),
                "object_totals": data.get("object_totals", {}),
                "queue_totals": data.get("queue_totals", {}),
                "message_stats": data.get("message_stats", {}),
                "listeners": [l.get("protocol", "") for l in data.get("listeners", [])],
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ApiAuthenticationError(url=str(exc.request.url)) from exc
        raise McpError(f"RabbitMQ API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def list_queues(vhost: str = "/") -> list[dict[str, Any]]:
    """Lista las colas de un vhost."""
    try:
        with _client() as client:
            resp = client.get("/queues", params={"vhost": vhost} if vhost != "/" else {})
            resp.raise_for_status()
            return [
                {
                    "name": q.get("name", ""),
                    "vhost": q.get("vhost", ""),
                    "durable": q.get("durable", False),
                    "messages": q.get("messages", 0),
                    "messages_ready": q.get("messages_ready", 0),
                    "messages_unacknowledged": q.get("messages_unacknowledged", 0),
                    "consumers": q.get("consumers", 0),
                    "state": q.get("state", ""),
                    "policy": q.get("policy"),
                }
                for q in resp.json()
            ]
    except httpx.HTTPStatusError as exc:
        raise McpError(f"RabbitMQ API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def get_queue_details(queue_name: str, vhost: str = "/") -> dict[str, Any]:
    """Obtiene los detalles de una cola específica."""
    try:
        with _client() as client:
            vhost_encoded = vhost.replace("/", "%2F") if vhost == "/" else vhost
            resp = client.get(f"/queues/{vhost_encoded}/{queue_name}")
            resp.raise_for_status()
            q = resp.json()
            return {
                "name": q.get("name", ""),
                "vhost": q.get("vhost", ""),
                "durable": q.get("durable", False),
                "auto_delete": q.get("auto_delete", False),
                "messages": q.get("messages", 0),
                "messages_ready": q.get("messages_ready", 0),
                "messages_unacknowledged": q.get("messages_unacknowledged", 0),
                "consumers": q.get("consumers", 0),
                "state": q.get("state", ""),
                "arguments": q.get("arguments", {}),
                "message_stats": q.get("message_stats", {}),
            }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise NotFoundError(resource="queue", identifier=queue_name) from exc
        raise McpError(f"RabbitMQ API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def list_exchanges(vhost: str = "/") -> list[dict[str, Any]]:
    """Lista los exchanges de un vhost."""
    try:
        with _client() as client:
            resp = client.get("/exchanges", params={"vhost": vhost} if vhost != "/" else {})
            resp.raise_for_status()
            return [
                {
                    "name": e.get("name", ""),
                    "type": e.get("type", ""),
                    "vhost": e.get("vhost", ""),
                    "durable": e.get("durable", False),
                    "internal": e.get("internal", False),
                    "auto_delete": e.get("auto_delete", False),
                }
                for e in resp.json()
            ]
    except httpx.HTTPStatusError as exc:
        raise McpError(f"RabbitMQ API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc


def publish_message(
    exchange: str,
    routing_key: str,
    payload: str,
    vhost: str = "/",
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Publica un mensaje en un exchange."""
    if not settings.allow_publish:
        raise McpError("Publicación no permitida. Establece RABBITMQ_ALLOW_PUBLISH=true para habilitar.")
    try:
        with _client() as client:
            vhost_encoded = vhost.replace("/", "%2F") if vhost == "/" else vhost
            body: dict[str, Any] = {
                "routing_key": routing_key,
                "payload": payload,
                "payload_encoding": "string",
            }
            if properties:
                body["properties"] = properties
            resp = client.post(f"/exchanges/{vhost_encoded}/{exchange}/publish", json=body)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as exc:
        raise McpError(f"RabbitMQ API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise McpError(f"Error de red: {exc}") from exc
