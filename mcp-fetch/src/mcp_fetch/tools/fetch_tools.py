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


# ---------------------------------------------------------------------------
# fetch_head
# ---------------------------------------------------------------------------


def fetch_head(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Realiza un HEAD HTTP y devuelve solo metadatos (sin cuerpo)."""
    _validate_url(url)
    resolved_timeout = timeout or settings.default_timeout
    try:
        with httpx.Client(
            follow_redirects=settings.follow_redirects,
            verify=settings.verify_ssl,
            timeout=resolved_timeout,
            headers={"User-Agent": settings.user_agent},
        ) as client:
            response = client.head(url, headers=headers or {})
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(url=url, timeout_seconds=resolved_timeout) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=url, reason=str(exc)) from exc
    _validate_url(str(response.url))
    return {
        "url": str(response.url),
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "content_length": response.headers.get("content-length", ""),
        "headers": dict(response.headers),
        "elapsed_ms": round(response.elapsed.total_seconds() * 1000, 2) if response.elapsed else 0.0,
    }


# ---------------------------------------------------------------------------
# check_url
# ---------------------------------------------------------------------------


def check_url(
    url: str,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Verifica si una URL es accesible (HEAD) y retorna status + metadatos."""
    try:
        return fetch_head(url, timeout=timeout)
    except Exception as exc:
        return {
            "url": url,
            "status_code": None,
            "accessible": False,
            "error": str(exc),
        }
    result = fetch_head(url, timeout=timeout)
    result["accessible"] = 200 <= result["status_code"] < 400
    return result


# ---------------------------------------------------------------------------
# fetch_with_auth
# ---------------------------------------------------------------------------


def fetch_with_auth(
    url: str,
    auth_type: str = "bearer",
    token: str = "",
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Realiza un GET HTTP con autenticación (bearer, basic, apikey)."""
    _validate_url(url)
    resolved_timeout = timeout or settings.default_timeout
    merged_headers = headers or {}
    if auth_type == "bearer":
        merged_headers["Authorization"] = f"Bearer {token}"
    elif auth_type == "basic":
        import base64
        cred = base64.b64encode(token.encode()).decode()
        merged_headers["Authorization"] = f"Basic {cred}"
    elif auth_type == "apikey":
        merged_headers["X-API-Key"] = token
    else:
        raise ValidationError(
            field="auth_type",
            message=f"Tipo de auth no soportado: {auth_type}. Usa bearer, basic o apikey.",
        )
    return fetch_url(url=url, headers=merged_headers, timeout=timeout)


# ---------------------------------------------------------------------------
# extract_links
# ---------------------------------------------------------------------------


def extract_links(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    filter_pattern: str | None = None,
) -> dict[str, Any]:
    """Extrae todos los links de una página HTML."""
    import fnmatch
    raw = fetch_url(url=url, headers=headers, timeout=timeout)
    content_type = raw["content_type"].lower()
    if not any(ct in content_type for ct in _HTML_TYPES):
        raise ApiError(
            url=url,
            status_code=raw["status_code"],
            response_body=f"La URL no devolvió HTML (Content-Type: {raw['content_type']}).",
        )
    soup = BeautifulSoup(raw["content"], "html.parser")
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = str(a_tag["href"])
        if href.startswith(("http://", "https://")):
            if filter_pattern is None or fnmatch.fnmatch(href, filter_pattern):
                links.append({"href": href, "text": a_tag.get_text(strip=True)[:100]})
    return {
        "url": raw["url"],
        "status_code": raw["status_code"],
        "links": links[:200],
        "link_count": len(links),
    }


# ---------------------------------------------------------------------------
# extract_metadata
# ---------------------------------------------------------------------------


def extract_metadata(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Extrae metadatos SEO/OpenGraph de una página HTML."""
    raw = fetch_url(url=url, headers=headers, timeout=timeout)
    content_type = raw["content_type"].lower()
    if not any(ct in content_type for ct in _HTML_TYPES):
        raise ApiError(
            url=url,
            status_code=raw["status_code"],
            response_body=f"La URL no devolvió HTML (Content-Type: {raw['content_type']}).",
        )
    soup = BeautifulSoup(raw["content"], "html.parser")
    metadata: dict[str, Any] = {
        "url": raw["url"],
        "status_code": raw["status_code"],
        "title": None,
        "description": None,
        "og_tags": {},
    }
    title_tag = soup.find("title")
    if title_tag:
        metadata["title"] = title_tag.get_text(strip=True)
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag:
        metadata["description"] = desc_tag.get("content", "")
    for og_tag in soup.find_all("meta", attrs={"property": lambda p: p and p.startswith("og:")}):
        prop = og_tag.get("property", "")
        content = og_tag.get("content", "")
        if prop and content:
            metadata["og_tags"][prop] = content
    return metadata


# ---------------------------------------------------------------------------
# extract_tables
# ---------------------------------------------------------------------------


def extract_tables(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Extrae todas las tablas HTML de una página y las convierte a listas de dicts."""
    raw = fetch_url(url=url, headers=headers, timeout=timeout)
    content_type = raw["content_type"].lower()
    if not any(ct in content_type for ct in _HTML_TYPES):
        raise ApiError(
            url=url,
            status_code=raw["status_code"],
            response_body=f"La URL no devolvió HTML (Content-Type: {raw['content_type']}).",
        )
    soup = BeautifulSoup(raw["content"], "html.parser")
    tables = []
    for table in soup.find_all("table"):
        headers_row = []
        thead = table.find("thead")
        if thead:
            ths = thead.find_all("th")
            headers_row = [th.get_text(strip=True) for th in ths]
        rows = []
        tbody = table.find("tbody") or table
        for tr in tbody.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            row_values = [cell.get_text(strip=True) for cell in cells]
            if not headers_row and row_values:
                headers_row = row_values
                continue
            if headers_row and row_values:
                row_dict = dict(zip(headers_row, row_values))
                rows.append(row_dict)
        if rows:
            tables.append({"headers": headers_row, "rows": rows, "row_count": len(rows)})
    return {
        "url": raw["url"],
        "status_code": raw["status_code"],
        "tables": tables,
        "table_count": len(tables),
    }


# ---------------------------------------------------------------------------
# fetch_with_retry
# ---------------------------------------------------------------------------


def fetch_with_retry(
    url: str,
    max_retries: int = 3,
    delay_seconds: float = 1.0,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Realiza un GET HTTP con reintentos automáticos."""
    import time
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            result = fetch_url(url=url, headers=headers, timeout=timeout)
            result["attempts"] = attempt
            return result
        except (NetworkError, NetworkTimeoutError) as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(delay_seconds * attempt)
    raise NetworkError(url=url, reason=f"Falló tras {max_retries} intentos. Último error: {last_error}")


# ---------------------------------------------------------------------------
# batch_fetch_json
# ---------------------------------------------------------------------------


def batch_fetch_json(
    urls: list[str],
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> list[dict[str, Any]]:
    """Descarga múltiples URLs y las parsea como JSON en lote."""
    results = []
    for u in urls:
        try:
            data = fetch_json(url=u, headers=headers, timeout=timeout)
            results.append({"url": u, "success": True, "data": data})
        except Exception as exc:
            results.append({"url": u, "success": False, "error": str(exc)})
    return results


# ---------------------------------------------------------------------------
# convert_html_to_markdown
# ---------------------------------------------------------------------------


def convert_html_to_markdown(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Descarga una página HTML y la convierte a Markdown simplificado."""
    raw = fetch_url(url=url, headers=headers, timeout=timeout)
    content_type = raw["content_type"].lower()
    if not any(ct in content_type for ct in _HTML_TYPES):
        raise ApiError(
            url=url,
            status_code=raw["status_code"],
            response_body=f"La URL no devolvió HTML (Content-Type: {raw['content_type']}).",
        )
    soup = BeautifulSoup(raw["content"], "html.parser")
    for tag in soup(["script", "style", "noscript", "head", "nav", "footer", "aside"]):
        tag.decompose()
    lines: list[str] = []
    for element in soup.body or soup:
        if element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(element.name[1])
            lines.append(f"{'#' * level} {element.get_text(strip=True)}")
        elif element.name == "p":
            text = element.get_text(strip=True)
            if text:
                lines.append(text)
        elif element.name == "li":
            lines.append(f"- {element.get_text(strip=True)}")
        elif element.name == "pre":
            code = element.get_text()
            lines.append(f"```\n{code}\n```")
        elif element.name == "code":
            lines.append(f"`{element.get_text(strip=True)}`")
        elif element.name == "a" and element.get("href"):
            href = element["href"]
            text = element.get_text(strip=True)
            lines.append(f"[{text}]({href})")
        elif element.name == "blockquote":
            text = element.get_text(strip=True)
            lines.append(f"> {text}")
        elif element.name in ("ul", "ol"):
            for li in element.find_all("li", recursive=False):
                lines.append(f"- {li.get_text(strip=True)}")
    markdown = "\n\n".join(lines)
    return {
        "url": raw["url"],
        "status_code": raw["status_code"],
        "markdown": markdown,
        "char_count": len(markdown),
    }


# ---------------------------------------------------------------------------
# download_file
# ---------------------------------------------------------------------------


def download_file(
    url: str,
    output_path: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    """Descarga un archivo desde una URL y lo guarda en output_path."""
    import os
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
            with client.stream("GET", url, headers=headers or {}) as response:
                _validate_url(str(response.url))
                total = 0
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        total += len(chunk)
                        if total > resolved_max:
                            f.write(chunk[: resolved_max - (total - len(chunk))])
                            break
                        f.write(chunk)
                truncated = total > resolved_max
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(url=url, timeout_seconds=resolved_timeout) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=url, reason=str(exc)) from exc
    return {
        "url": url,
        "output_path": output_path,
        "bytes_downloaded": min(total, resolved_max),
        "status_code": response.status_code,
        "truncated": truncated,
    }
