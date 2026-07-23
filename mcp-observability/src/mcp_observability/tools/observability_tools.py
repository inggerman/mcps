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


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def prometheus_range_query(
    base_url: str | None,
    query: str,
    start: float,
    end: float,
    step: str,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Ejecuta una query de rango en Prometheus."""
    if not query.strip():
        raise ValidationError(field="query", message="PromQL no puede estar vacio.")
    response = httpx.get(
        f"{_validate_base_url(base_url, 'prometheus_url')}/api/v1/query_range",
        params={"query": query, "start": start, "end": end, "step": step},
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def list_prometheus_targets(
    base_url: str | None,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Lista los targets de Prometheus."""
    response = httpx.get(
        f"{_validate_base_url(base_url, 'prometheus_url')}/api/v1/targets",
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def list_prometheus_alerts(
    base_url: str | None,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Lista las alertas activas en Prometheus."""
    response = httpx.get(
        f"{_validate_base_url(base_url, 'prometheus_url')}/api/v1/alerts",
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def list_prometheus_rules(
    base_url: str | None,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Lista las reglas de alerta en Prometheus."""
    response = httpx.get(
        f"{_validate_base_url(base_url, 'prometheus_url')}/api/v1/rules",
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def get_prometheus_series(
    base_url: str | None,
    match: str,
    start: float,
    end: float,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Obtiene series de Prometheus por label matcher."""
    response = httpx.get(
        f"{_validate_base_url(base_url, 'prometheus_url')}/api/v1/series",
        params={"match[]": match, "start": start, "end": end},
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def loki_labels(
    base_url: str | None,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Lista las labels disponibles en Loki."""
    response = httpx.get(
        f"{_validate_base_url(base_url, 'loki_url')}/loki/api/v1/labels",
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def loki_label_values(
    base_url: str | None,
    label: str,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Lista los valores de una label en Loki."""
    if not label.strip():
        raise ValidationError(field="label", message="Label no puede estar vacio.")
    response = httpx.get(
        f"{_validate_base_url(base_url, 'loki_url')}/loki/api/v1/label/{label}/values",
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def check_multiple_endpoints(
    urls: list[str],
    timeout_seconds: float,
) -> list[dict[str, Any]]:
    """Verifica multiples endpoints de salud."""
    results: list[dict[str, Any]] = []
    for url in urls:
        try:
            results.append(check_endpoint(url, timeout_seconds))
        except Exception as exc:
            results.append({"url": url, "healthy": False, "error": str(exc)[:100]})
    return results


def get_prometheus_metadata(
    base_url: str | None,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Obtiene metadata de Prometheus."""
    response = httpx.get(
        f"{_validate_base_url(base_url, 'prometheus_url')}/api/v1/metadata",
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def prometheus_status(
    base_url: str | None,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Obtiene el estado de configuracion de Prometheus."""
    response = httpx.get(
        f"{_validate_base_url(base_url, 'prometheus_url')}/api/v1/status/config",
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()


def loki_status(
    base_url: str | None,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Obtiene el estado de Loki."""
    response = httpx.get(
        f"{_validate_base_url(base_url, 'loki_url')}/ready",
        headers=_headers(token),
        timeout=timeout_seconds,
    )
    return {
        "url": base_url,
        "status_code": response.status_code,
        "ready": response.status_code == 200,
        "body": response.text[:500],
    }


def generate_slo_report(
    base_url: str | None,
    slo_query: str,
    error_query: str,
    timeout_seconds: float,
    token: str | None = None,
) -> dict[str, Any]:
    """Genera un reporte SLO basico desde Prometheus."""
    total = query_prometheus(base_url, slo_query, timeout_seconds, token)
    errors = query_prometheus(base_url, error_query, timeout_seconds, token)

    total_val = 0.0
    error_val = 0.0

    try:
        result = total.get("data", {}).get("result", [])
        if result:
            total_val = float(result[0].get("value", [0, "0"])[1])
    except (KeyError, IndexError, ValueError):
        pass

    try:
        result = errors.get("data", {}).get("result", [])
        if result:
            error_val = float(result[0].get("value", [0, "0"])[1])
    except (KeyError, IndexError, ValueError):
        pass

    success_rate = (total_val - error_val) / total_val * 100 if total_val > 0 else 0.0

    return {
        "total_requests": total_val,
        "total_errors": error_val,
        "success_rate_percent": round(success_rate, 4),
        "error_rate_percent": round(100 - success_rate, 4),
        "slo_target": 99.9,
        "slo_met": success_rate >= 99.9,
    }
