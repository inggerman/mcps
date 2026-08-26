"""Herramientas de búsqueda web para mcp-web-search.

Soporta DuckDuckGo (gratis, sin API key) y Brave Search (con API key).
Filtra resultados por whitelist de dominios confiables.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from mcp_web_search.config import settings
from mcp_web_search.whitelist import get_trust_score, is_trusted


class RateLimiter:
    """Rate limiter simple por minuto."""

    def __init__(self, max_per_minute: int) -> None:
        self.max = max_per_minute
        self._timestamps: list[float] = []

    def check(self) -> bool:
        now = time.monotonic()
        self._timestamps = [t for t in self._timestamps if now - t < 60]
        if len(self._timestamps) >= self.max:
            return False
        self._timestamps.append(now)
        return True


_rate_limiter = RateLimiter(settings.rate_limit_per_minute)


def _filter_results(results: list[dict[str, Any]], threshold: float) -> list[dict[str, Any]]:
    """Filtra resultados por trust score y agrega metadata."""
    filtered = []
    for r in results:
        url = r.get("url", "") or r.get("href", "") or r.get("link", "")
        if not url:
            continue
        score = get_trust_score(url)
        if score < threshold:
            continue
        r["trust_score"] = score
        r["domain"] = _extract_domain(url)
        # Truncate snippet
        snippet = r.get("snippet", "") or r.get("description", "") or r.get("body", "")
        if len(snippet) > settings.snippet_max_length:
            snippet = snippet[: settings.snippet_max_length] + "..."
        r["snippet"] = snippet
        filtered.append(r)
    return filtered


def _extract_domain(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).hostname or ""


def search_duckduckgo(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Busca con DuckDuckGo Search API (gratis, sin API key)."""
    from duckduckgo_search import DDGS

    raw_results: list[dict[str, Any]] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results * 3):
            raw_results.append({
                "url": r.get("href", ""),
                "title": r.get("title", ""),
                "snippet": r.get("body", ""),
            })
    return raw_results


def search_brave(query: str, max_results: int = 10, api_key: str = "") -> list[dict[str, Any]]:
    """Busca con Brave Search API (requiere API key)."""
    if not api_key:
        raise ValueError("Brave API key not configured")

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": query,
        "count": max_results * 3,
    }

    with httpx.Client(timeout=30) as client:
        resp = client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

    raw_results: list[dict[str, Any]] = []
    for r in data.get("web", {}).get("results", []):
        raw_results.append({
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "snippet": r.get("description", ""),
        })
    return raw_results


def search_web(
    query: str,
    max_results: int | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """Busca en la web y filtra resultados por whitelist de fuentes confiables.

    Args:
        query: Consulta de búsqueda.
        max_results: Máximo número de resultados (default: settings.max_results).
        provider: Provider de búsqueda (default: settings.provider).

    Returns:
        Dict con query, results (filtrados), total_raw, total_filtered, provider.
    """
    if not _rate_limiter.check():
        return {
            "query": query,
            "results": [],
            "error": "Rate limit exceeded. Max searches per minute reached.",
            "total_raw": 0,
            "total_filtered": 0,
            "provider": provider or settings.provider,
        }

    resolved_max = max_results or settings.max_results
    resolved_provider = provider or settings.provider

    if resolved_provider == "brave":
        raw = search_brave(query, resolved_max, settings.brave_api_key)
    else:
        raw = search_duckduckgo(query, resolved_max)

    filtered = _filter_results(raw, settings.trust_threshold)

    return {
        "query": query,
        "results": filtered[:resolved_max],
        "total_raw": len(raw),
        "total_filtered": len(filtered),
        "provider": resolved_provider,
    }


def search_docs(query: str, technology: str = "", max_results: int | None = None) -> dict[str, Any]:
    """Busca específicamente en documentación oficial.

    Args:
        query: Consulta de búsqueda.
        technology: Tecnología específica (ej: 'fastapi', 'kubernetes', 'python').
        max_results: Máximo número de resultados.

    Returns:
        Dict con resultados filtrados a solo trust_score >= 0.9.
    """
    enhanced_query = f"{query} {technology} documentation site:*.org OR site:*.dev OR site:*.io" if technology else f"{query} documentation"
    result = search_web(enhanced_query, max_results or settings.max_results)

    # For docs, use higher threshold
    result["results"] = [
        r for r in result["results"] if r.get("trust_score", 0) >= 0.9
    ]
    result["search_type"] = "docs"
    result["technology"] = technology
    return result


def search_github(query: str, max_results: int | None = None) -> dict[str, Any]:
    """Busca en GitHub específicamente.

    Args:
        query: Consulta de búsqueda.
        max_results: Máximo número de resultados.

    Returns:
        Dict con resultados de GitHub.
    """
    enhanced_query = f"{query} site:github.com"
    result = search_web(enhanced_query, max_results or settings.max_results)
    result["search_type"] = "github"
    return result


def search_stackoverflow(query: str, max_results: int | None = None) -> dict[str, Any]:
    """Busca en Stack Overflow específicamente.

    Args:
        query: Consulta de búsqueda.
        max_results: Máximo número de resultados.

    Returns:
        Dict con resultados de Stack Overflow.
    """
    enhanced_query = f"{query} site:stackoverflow.com"
    result = search_web(enhanced_query, max_results or settings.max_results)
    result["search_type"] = "stackoverflow"
    return result
