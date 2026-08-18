"""Tools de Redis: info, list keys, get/set, TTL, type, delete (write-gated)."""

from __future__ import annotations

from typing import Any

import redis

from mcp_redis.config import settings
from mcp_shared.errors import McpError, NotFoundError


def _client() -> redis.Redis:
    return redis.Redis(
        host=settings.host,
        port=settings.port,
        password=settings.password or None,
        db=settings.db,
        decode_responses=True,
        socket_timeout=10,
    )


def redis_info() -> dict[str, Any]:
    """Obtiene información del servidor Redis."""
    try:
        client = _client()
        info = client.info()
        return {
            "redis_version": info.get("redis_version", ""),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", ""),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            "db_size": client.dbsize(),
        }
    except redis.RedisError as exc:
        raise McpError(f"Redis error: {exc}") from exc


def list_keys(pattern: str = "*", limit: int = 100) -> list[str]:
    """Lista las claves que coinciden con un patrón."""
    try:
        client = _client()
        keys = list(client.scan_iter(match=pattern, count=limit))
        return keys[:limit]
    except redis.RedisError as exc:
        raise McpError(f"Redis error: {exc}") from exc


def get_key(key: str) -> dict[str, Any]:
    """Obtiene el valor de una clave."""
    try:
        client = _client()
        key_type = client.type(key)
        if key_type == "none":
            raise NotFoundError(resource="key", identifier=key) from None
        if key_type == "string":
            value = client.get(key)
        elif key_type == "list":
            value = client.lrange(key, 0, -1)
        elif key_type == "hash":
            value = client.hgetall(key)
        elif key_type == "set":
            value = list(client.smembers(key))
        elif key_type == "zset":
            value = client.zrange(key, 0, -1, withscores=True)
        else:
            value = None
        return {"key": key, "type": key_type, "value": value}
    except redis.RedisError as exc:
        raise McpError(f"Redis error: {exc}") from exc


def set_key(key: str, value: str, ttl: int | None = None) -> dict[str, Any]:
    """Establece el valor de una clave string."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece REDIS_ALLOW_WRITE=true para habilitar.")
    try:
        client = _client()
        client.set(key, value, ex=ttl)
        return {"key": key, "value": value, "ttl": ttl, "status": "set"}
    except redis.RedisError as exc:
        raise McpError(f"Redis error: {exc}") from exc


def get_ttl(key: str) -> dict[str, Any]:
    """Obtiene el TTL de una clave en segundos."""
    try:
        client = _client()
        ttl = client.ttl(key)
        return {"key": key, "ttl_seconds": ttl}
    except redis.RedisError as exc:
        raise McpError(f"Redis error: {exc}") from exc


def get_key_type(key: str) -> dict[str, Any]:
    """Obtiene el tipo de una clave."""
    try:
        client = _client()
        key_type = client.type(key)
        return {"key": key, "type": key_type}
    except redis.RedisError as exc:
        raise McpError(f"Redis error: {exc}") from exc


def delete_key(key: str) -> dict[str, Any]:
    """Elimina una clave."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece REDIS_ALLOW_WRITE=true para habilitar.")
    try:
        client = _client()
        deleted = client.delete(key)
        return {"key": key, "deleted": deleted}
    except redis.RedisError as exc:
        raise McpError(f"Redis error: {exc}") from exc
