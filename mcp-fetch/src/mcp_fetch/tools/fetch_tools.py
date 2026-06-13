"""Herramientas HTTP para mcp-fetch.

Soporta GET, POST, extracción de texto limpio desde HTML y parsing de JSON.
Todas las operaciones son síncronas (httpx sync client).
"""

from __future__ import annotations

import ipaddress
import json
import socket
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from mcp_shared.errors import (
    ApiError,
    NetworkError,
    NetworkTimeoutError,
    ParseError,
    ValidationError,
)

from mcp_fetch.config import settings

_TRUNCATION_NOTE = "[contenido truncado a {limit} bytes]"
_HTML_TYPES = ("text/html", "application/xhtml+xml")
_JSON_TYPES = ("application/json", "application/ld+json")

# ---------------------------------------------------------------------------
# fetch_url
# ---------------------------------------------------------------------------


def fetch_url(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    """Realiza un GET HTTP y devuelve el contenido crudo + metadatos.

    Args:
        url: URL a consultar (debe incluir esquema http:// o https://).
        headers: Headers HTTP adicionales (dict string→string).
        timeout: Timeout en segundos. Si None usa el default configurado.
        max_bytes: Límite de bytes a leer. Si None usa el default configurado.

    Returns:
        Dict con:
        - ``url`` (str): URL final (tras redirecciones).
        - ``status_code`` (int): Código HTTP de respuesta.
        - ``content_type`` (str): Content-Type de la respuesta.
        - ``content`` (str): Cuerpo de la respuesta (texto).
        - ``truncated`` (bool): True si el contenido fue truncado.
        - ``headers`` (dict): Headers de respuesta relevantes.
        - ``elapsed_ms`` (float): Tiempo de respuesta en ms.

    Raises:
        ValidationError: Si la URL no tiene esquema válido.
        ApiError: Si hay error de red o HTTP 4xx/5xx.
    """
    _validate_url(url)
    resolved_timeout = timeout or settings.default_timeout
    resolved_max = max_bytes or settings.max_content_length

    try:
        with httpx.Client(
            follow_redirects=settings.follow_redirects,
            verify=settings.verify_ssl,
            timeout=resolved_timeout,
            headers={"User-Agent": settings.user_agent},
        ) as client:
            response = client.get(url, headers=headers or {})

    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(url=url, timeout_seconds=resolved_timeout) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=url, reason=str(exc)) from exc

    _validate_url(str(response.url))
    return _build_response(response, resolved_max)


# ---------------------------------------------------------------------------
# fetch_post
# ---------------------------------------------------------------------------


def fetch_post(
    url: str,
    json_body: dict[str, Any] | None = None,
    form_data: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    """Realiza un POST HTTP con cuerpo JSON o form-data.

    Args:
        url: URL destino.
        json_body: Cuerpo a enviar como ``application/json``.
        form_data: Cuerpo a enviar como ``application/x-www-form-urlencoded``.
        headers: Headers HTTP adicionales.
        timeout: Timeout en segundos.
        max_bytes: Límite de bytes a leer.

    Returns:
        Mismo formato que ``fetch_url``.

    Raises:
        ValidationError: Si se pasan ``json_body`` y ``form_data`` simultáneamente,
            o si la URL no tiene esquema válido.
        ApiError: Si hay error de red o HTTP 4xx/5xx.
    """
    _validate_url(url)
    if json_body is not None and form_data is not None:
        raise ValidationError(
            field="body",
            message="Proporciona json_body O form_data, no ambos simultáneamente.",
        )
    resolved_timeout = timeout or settings.default_timeout
    resolved_max = max_bytes or settings.max_content_length

    try:
        with httpx.Client(
            follow_redirects=settings.follow_redirects,
            verify=settings.verify_ssl,
            timeout=resolved_timeout,
            headers={"User-Agent": settings.user_agent},
        ) as client:
            if json_body is not None:
                response = client.post(url, json=json_body, headers=headers or {})
            elif form_data is not None:
                response = client.post(url, data=form_data, headers=headers or {})
            else:
                response = client.post(url, headers=headers or {})

    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(url=url, timeout_seconds=resolved_timeout) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=url, reason=str(exc)) from exc

    _validate_url(str(response.url))
    return _build_response(response, resolved_max)


# ---------------------------------------------------------------------------
# extract_text
# ---------------------------------------------------------------------------


def extract_text(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    include_links: bool = False,
    include_title: bool = True,
) -> dict[str, Any]:
    """Descarga una página HTML y extrae el texto limpio (sin tags).

    Ideal para leer documentación, artículos y páginas web desde el agente.

    Args:
        url: URL de la página HTML.
        headers: Headers HTTP adicionales.
        timeout: Timeout en segundos.
        include_links: Si True, incluye una lista de los links encontrados.
        include_title: Si True, incluye el ``<title>`` de la página.

    Returns:
        Dict con:
        - ``url`` (str): URL final.
        - ``title`` (str | None): Título de la página (si ``include_title=True``).
        - ``text`` (str): Texto limpio extraído.
        - ``word_count`` (int): Número de palabras aproximado.
        - ``links`` (list[dict] | None): Links encontrados (si ``include_links=True``).
        - ``status_code`` (int): Código HTTP.

    Raises:
        ValidationError: Si la URL no tiene esquema válido.
        ApiError: Si hay error de red o la respuesta no es HTML.
    """
    raw = fetch_url(url=url, headers=headers, timeout=timeout)

    content_type = raw["content_type"].lower()
    if not any(ct in content_type for ct in _HTML_TYPES):
        raise ApiError(
            url=url,
            status_code=raw["status_code"],
            response_body=(
                f"La URL no devolvió HTML (Content-Type: {raw['content_type']}). "
                "Usa fetch_url para contenido no-HTML."
            ),
        )

    soup = BeautifulSoup(raw["content"], "html.parser")

    title_text: str | None = None
    if include_title:
        title_tag = soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else None

    for tag in soup(["script", "style", "noscript", "head", "nav", "footer", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(lines)

    result: dict[str, Any] = {
        "url": raw["url"],
        "text": clean_text,
        "word_count": len(clean_text.split()),
        "status_code": raw["status_code"],
        "title": title_text,
        "links": None,
    }

    if include_links:
        links = []
        for a_tag in soup.find_all("a", href=True):
            href = str(a_tag["href"])
            if href.startswith(("http://", "https://")):
                links.append({"href": href, "text": a_tag.get_text(strip=True)[:100]})
        result["links"] = links[:50]

    return result


# ---------------------------------------------------------------------------
# fetch_json
# ---------------------------------------------------------------------------


def fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    jq_path: str | None = None,
) -> dict[str, Any]:
    """Descarga una URL y parsea la respuesta como JSON.

    Opcionalmente navega el JSON resultante con un path simple tipo ``"data.items[0].name"``.

    Args:
        url: URL que devuelve JSON.
        headers: Headers HTTP adicionales.
        timeout: Timeout en segundos.
        jq_path: Path de navegación simple con notación punto+índice,
            ej: ``"results[0].address.city"``. Si None devuelve el JSON completo.

    Returns:
        Dict con:
        - ``url`` (str): URL final.
        - ``data`` (Any): JSON parseado (o el sub-valor si se usó ``jq_path``).
        - ``status_code`` (int): Código HTTP.
        - ``path_used`` (str | None): Path que se aplicó.

    Raises:
        ValidationError: Si la URL no tiene esquema válido o el path es inválido.
        ApiError: Si la respuesta no es JSON o hay error de red.
        ParseError: Si el cuerpo no es JSON válido.
    """
    raw = fetch_url(url=url, headers=headers, timeout=timeout)

    try:
        data: Any = json.loads(raw["content"])
    except json.JSONDecodeError as exc:
        raise ParseError(
            source=url,
            reason=(
                f"Respuesta no es JSON válido. "
                f"Content-Type: {raw['content_type']}. "
                f"Inicio: {raw['content'][:200]!r}"
            ),
        ) from exc

    if jq_path:
        data = _navigate_path(data, jq_path, url)

    return {
        "url": raw["url"],
        "data": data,
        "status_code": raw["status_code"],
        "path_used": jq_path,
    }


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError(
            field="url",
            message=f"La URL debe comenzar con http:// o https://. Recibido: {url!r}",
        )
    if parsed.username or parsed.password:
        raise ValidationError(
            field="url",
            message="No se permiten credenciales embebidas en la URL.",
        )
    if settings.allow_private_networks:
        return

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                parsed.hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        }
    except socket.gaierror as exc:
        raise ValidationError(
            field="url",
            message=f"No se pudo resolver el host {parsed.hostname!r}.",
        ) from exc

    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise ValidationError(
                field="url",
                message=f"El destino {parsed.hostname!r} resuelve a una red no pública.",
            )


def _build_response(response: httpx.Response, max_bytes: int) -> dict[str, Any]:
    content_type = response.headers.get("content-type", "application/octet-stream")
    raw_bytes = response.content
    truncated = len(raw_bytes) > max_bytes

    if truncated:
        raw_bytes = raw_bytes[:max_bytes]

    try:
        text = raw_bytes.decode("utf-8", errors="replace")
    except Exception:
        text = raw_bytes.decode("latin-1", errors="replace")

    if truncated:
        text += f"\n\n{_TRUNCATION_NOTE.format(limit=max_bytes)}"

    elapsed = response.elapsed.total_seconds() * 1000 if response.elapsed else 0.0

    relevant_headers = {
        k: v
        for k, v in response.headers.items()
        if k.lower()
        in (
            "content-type",
            "content-length",
            "last-modified",
            "cache-control",
            "server",
            "x-powered-by",
        )
    }

    return {
        "url": str(response.url),
        "status_code": response.status_code,
        "content_type": content_type,
        "content": text,
        "truncated": truncated,
        "headers": relevant_headers,
        "elapsed_ms": round(elapsed, 2),
    }


def _navigate_path(data: Any, path: str, url: str) -> Any:
    """Navega un objeto JSON usando notación punto+índice: ``"a.b[0].c"``."""
    import re

    parts = re.split(r"\.|(?=\[)", path)
    current = data

    for part in parts:
        if not part:
            continue
        if part.startswith("["):
            try:
                idx = int(part[1:-1])
                current = current[idx]
            except (IndexError, TypeError, ValueError) as exc:
                raise ValidationError(
                    field="jq_path",
                    message=f"Índice {part} inválido o fuera de rango en path '{path}' para {url}.",
                ) from exc
        else:
            if not isinstance(current, dict):
                raise ValidationError(
                    field="jq_path",
                    message=f"No se puede acceder a '{part}' en un {type(current).__name__} (path: '{path}').",
                )
            if part not in current:
                raise ValidationError(
                    field="jq_path",
                    message=f"Clave '{part}' no encontrada en el objeto JSON (path: '{path}').",
                )
            current = current[part]

    return current
