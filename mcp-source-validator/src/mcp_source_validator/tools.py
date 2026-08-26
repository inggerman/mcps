"""Herramientas de validación de fuentes para mcp-source-validator.

Valida URLs y contenido web contra una whitelist de dominios confiables,
verifica SSL, frescura del contenido, y metadatos.
"""

from __future__ import annotations

import ssl
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from mcp_source_validator.config import settings
from mcp_source_validator.whitelist import TRUSTED_DOMAINS, get_trust_score


def validate_url(url: str) -> dict[str, Any]:
    """Valida una URL: esquema, dominio, trust score, SSL, accesibilidad.

    Args:
        url: URL a validar.

    Returns:
        Dict con: url, valid, trust_score, domain, ssl_valid, accessible,
        status_code, content_type, last_modified, fresh, issues[].
    """
    issues: list[str] = []
    parsed = urlparse(url)

    # Scheme check
    if parsed.scheme not in ("http", "https"):
        issues.append(f"Invalid scheme: {parsed.scheme}. Only http/https allowed.")
        return {"url": url, "valid": False, "issues": issues}

    domain = parsed.hostname or ""
    if not domain:
        issues.append("No hostname in URL")
        return {"url": url, "valid": False, "issues": issues}

    # Trust score
    score = get_trust_score(url)
    if score < settings.min_trust_score:
        issues.append(f"Low trust score: {score:.2f} (threshold: {settings.min_trust_score})")

    # SSL check
    ssl_valid = True
    if parsed.scheme == "https" and settings.check_ssl:
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(
                __import__("socket").create_connection((domain, 443), timeout=5),
                server_hostname=domain,
            ) as s:
                s.getpeercert()
        except Exception:
            ssl_valid = False
            issues.append("SSL certificate invalid or missing")

    # Accessibility check
    accessible = False
    status_code = None
    content_type = None
    last_modified = None
    fresh = True

    try:
        with httpx.Client(timeout=settings.default_timeout, verify=settings.check_ssl) as client:
            resp = client.head(url, follow_redirects=True)
            status_code = resp.status_code
            accessible = 200 <= status_code < 400
            content_type = resp.headers.get("content-type", "")
            last_modified = resp.headers.get("last-modified")

            if not accessible:
                issues.append(f"HTTP {status_code}: not accessible")

            if last_modified and settings.check_content_freshness:
                try:
                    lm_date = datetime.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z")
                    lm_date = lm_date.replace(tzinfo=timezone.utc)
                    days_old = (datetime.now(timezone.utc) - lm_date).days
                    if days_old > settings.freshness_days:
                        fresh = False
                        issues.append(f"Content is {days_old} days old (stale)")
                except (ValueError, TypeError):
                    pass

    except httpx.TimeoutException:
        issues.append("Request timed out")
    except httpx.RequestError as exc:
        issues.append(f"Network error: {exc}")

    valid = len(issues) == 0 and accessible and score >= settings.min_trust_score

    return {
        "url": url,
        "valid": valid,
        "trust_score": score,
        "domain": domain,
        "ssl_valid": ssl_valid,
        "accessible": accessible,
        "status_code": status_code,
        "content_type": content_type,
        "last_modified": last_modified,
        "fresh": fresh,
        "issues": issues,
    }


def validate_content(url: str, content: str = "") -> dict[str, Any]:
    """Valida el contenido de una URL: trust score + contenido HTML.

    Args:
        url: URL del contenido.
        content: Contenido HTML a validar (si está vacío, se descarga).

    Returns:
        Dict con: url, valid, trust_score, has_author, has_date,
        word_count, title, issues[].
    """
    issues: list[str] = []
    score = get_trust_score(url)

    if score < settings.min_trust_score:
        issues.append(f"Low trust score: {score:.2f}")

    if not content:
        try:
            with httpx.Client(timeout=settings.default_timeout) as client:
                resp = client.get(url, follow_redirects=True)
                content = resp.text
        except Exception as exc:
            return {
                "url": url,
                "valid": False,
                "trust_score": score,
                "issues": [f"Failed to fetch: {exc}"],
            }

    soup = BeautifulSoup(content, "html.parser")

    # Extract metadata
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    author_tag = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", attrs={"property": "article:author"})
    has_author = author_tag is not None
    if not has_author:
        issues.append("No author metadata found")

    date_tag = soup.find("meta", attrs={"name": "date"}) or soup.find("meta", attrs={"property": "article:published_time"})
    has_date = date_tag is not None
    if not has_date:
        issues.append("No publication date found")

    # Remove scripts/styles for word count
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    word_count = len(text.split())

    if word_count < 100:
        issues.append(f"Very low word count: {word_count} (possible thin content)")

    # Check for AI-generated spam indicators
    ai_indicators = ["as an ai", "i cannot", "as a language model"]
    text_lower = text.lower()
    ai_hits = [ind for ind in ai_indicators if ind in text_lower]
    if ai_hits:
        issues.append(f"AI-generated content indicators: {ai_hits}")

    valid = score >= settings.min_trust_score and has_author and word_count >= 100 and not ai_hits

    return {
        "url": url,
        "valid": valid,
        "trust_score": score,
        "title": title,
        "has_author": has_author,
        "has_date": has_date,
        "word_count": word_count,
        "issues": issues,
    }


def get_trust_score_for_url(url: str) -> dict[str, Any]:
    """Retorna el trust score de una URL."""
    score = get_trust_score(url)
    return {
        "url": url,
        "trust_score": score,
        "is_trusted": score >= settings.min_trust_score,
        "domain": urlparse(url).hostname or "",
    }


def list_whitelist_domains() -> dict[str, Any]:
    """Lista todos los dominios en la whitelist."""
    return {
        "domains": TRUSTED_DOMAINS,
        "total": len(TRUSTED_DOMAINS),
        "min_trust_score": settings.min_trust_score,
    }
