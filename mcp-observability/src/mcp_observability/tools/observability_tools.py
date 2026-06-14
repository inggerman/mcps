from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlparse

import httpx
from mcp_shared.errors import ValidationError


def _headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _validate_base_url(url: str | None, field: str) -> str:
    if not url:
        raise ValidationError(field=field, message=f"{field} no está configurado.")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError(field=field, message="La URL configurada no es válida.")
    return url.rstrip("/")


def query_prometheus(
    base_url: str | None,
    query: str,
    timeout_seconds: float,
    token: str | None = None,
    timestamp: float | None = None,
) -> dict[str, Any]:
    if not query.strip():
        raise ValidationError(field="query", message="PromQL no puede estar vacío.")
    response = httpx.get(
        f"{_validate_base_url(base_url, 'prometheus_url')}/api/v1/query",
        params={"query": query, "time": timestamp},
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def query_loki(
    base_url: str | None,
    query: str,
    timeout_seconds: float,
    max_entries: int,
    token: str | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
) -> dict[str, Any]:
    if not query.strip():
        raise ValidationError(field="query", message="LogQL no puede estar vacío.")
    now_ns = time.time_ns()
    response = httpx.get(
        f"{_validate_base_url(base_url, 'loki_url')}/loki/api/v1/query_range",
        params={
            "query": query,
            "start": start_ns or now_ns - 3_600_000_000_000,
            "end": end_ns or now_ns,
            "limit": max_entries,
        },
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def check_endpoint(url: str, timeout_seconds: float) -> dict[str, Any]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError(field="url", message="La URL debe ser HTTP(S).")
    started = time.perf_counter()
    response = httpx.get(url, timeout=timeout_seconds, follow_redirects=False)
    return {
        "url": url,
        "status_code": response.status_code,
        "healthy": response.is_success,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }
