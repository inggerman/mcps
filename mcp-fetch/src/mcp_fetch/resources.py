"""Resources de solo lectura para mcp-fetch.

Expone metadatos, guías y consejos sobre HTTP, APIs y extracción de contenido
como URIs accesibles para el modelo a través de `@mcp.resource`.
"""

from __future__ import annotations

import json

from mcp_fetch.config import settings


# ---------------------------------------------------------------------------
# Resources estáticos
# ---------------------------------------------------------------------------


def http_status_codes() -> str:
    """Códigos de estado HTTP comunes."""
    return json.dumps(
        {
            "codes": [
                {"code": "200", "name": "OK", "description": "Respuesta exitosa"},
                {"code": "201", "name": "Created", "description": "Recurso creado"},
                {"code": "204", "name": "No Content", "description": "Sin contenido"},
                {"code": "301", "name": "Moved Permanently", "description": "Redirección permanente"},
                {"code": "302", "name": "Found", "description": "Redirección temporal"},
                {"code": "304", "name": "Not Modified", "description": "Caché válido"},
                {"code": "400", "name": "Bad Request", "description": "Solicitud malformada"},
                {"code": "401", "name": "Unauthorized", "description": "Autenticación requerida"},
                {"code": "403", "name": "Forbidden", "description": "Acceso denegado"},
                {"code": "404", "name": "Not Found", "description": "Recurso no encontrado"},
                {"code": "405", "name": "Method Not Allowed", "description": "Método no permitido"},
                {"code": "409", "name": "Conflict", "description": "Conflicto de estado"},
                {"code": "429", "name": "Too Many Requests", "description": "Rate limit"},
                {"code": "500", "name": "Internal Server Error", "description": "Error del servidor"},
                {"code": "502", "name": "Bad Gateway", "description": "Gateway inválido"},
                {"code": "503", "name": "Service Unavailable", "description": "Servicio no disponible"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def http_methods_guide() -> str:
    """Guía de métodos HTTP."""
    return (
        "# Métodos HTTP\n\n"
        "- **GET**: Recuperar datos (idempotente, seguro).\n"
        "- **POST**: Crear un recurso o enviar datos.\n"
        "- **PUT**: Reemplazar un recurso completo (idempotente).\n"
        "- **PATCH**: Modificar parcialmente un recurso.\n"
        "- **DELETE**: Eliminar un recurso (idempotente).\n"
        "- **HEAD**: Como GET pero sin cuerpo (solo headers).\n"
        "- **OPTIONS**: Describir opciones de comunicación.\n"
        "\n"
        "El MCP mcp-fetch soporta GET (fetch_url, extract_text, fetch_json) "
        "y POST (fetch_post)."
    )


def content_types_guide() -> str:
    """Guía de Content-Types comunes."""
    return (
        "# Content-Types comunes\n\n"
        "- `text/html` — Páginas web (usa extract_text).\n"
        "- `application/json` — APIs REST (usa fetch_json).\n"
        "- `application/xml` — XML (usa fetch_url).\n"
        "- `text/plain` — Texto plano (usa fetch_url).\n"
        "- `text/csv` — CSV (usa fetch_url).\n"
        "- `application/octet-stream` — Binario genérico.\n"
        "- `application/pdf` — PDF.\n"
        "- `text/markdown` — Markdown.\n"
        "- `application/x-www-form-urlencoded` — Form data.\n"
        "- `multipart/form-data` — Upload de archivos."
    )


def security_best_practices() -> str:
    """Mejores prácticas de seguridad HTTP."""
    return (
        "# Seguridad HTTP\n\n"
        "- MCP_FETCH_ALLOW_PRIVATE_NETWORKS=false por defecto (bloquea SSRF).\n"
        "- MCP_FETCH_FOLLOW_REDIRECTS=false por defecto.\n"
        "- MCP_FETCH_VERIFY_SSL=true por defecto.\n"
        "- No se permiten credenciales embebidas en URLs.\n"
        "- Solo esquemas http:// y https:// son válidos.\n"
        "- Se valida que el host resuelva a IP públicas.\n"
        "- MCP_FETCH_MAX_CONTENT_LENGTH limita el tamaño (default 5 MB).\n"
        "- MCP_FETCH_DEFAULT_TIMEOUT limita el tiempo (default 30s)."
    )


def api_authentication_guide() -> str:
    """Guía de autenticación para APIs."""
    return (
        "# Autenticación de APIs\n\n"
        "- **Bearer Token**: `Authorization: Bearer <token>`\n"
        "- **API Key (header)**: `X-API-Key: <key>`\n"
        "- **Basic Auth**: `Authorization: Basic <base64>`\n"
        "- **OAuth2**: Obtener token primero, luego usar como Bearer.\n"
        "- Pasa los headers como dict en el parámetro `headers`.\n"
        "- Ejemplo: `headers={'Authorization': 'Bearer ghp_xxx'}`"
    )


def rest_api_conventions() -> str:
    """Convenciones REST API."""
    return (
        "# Convenciones REST\n\n"
        "- GET /resource — Listar recursos.\n"
        "- GET /resource/{id} — Obtener un recurso.\n"
        "- POST /resource — Crear recurso.\n"
        "- PUT /resource/{id} — Actualizar completo.\n"
        "- PATCH /resource/{id} — Actualizar parcial.\n"
        "- DELETE /resource/{id} — Eliminar.\n"
        "- GET /resource?param=value — Filtrar/paginar.\n"
        "- Status 200 para éxito, 201 para creación, 4xx/5xx para errores."
    )


def json_path_guide() -> str:
    """Guía de navegación JSON con jq_path."""
    return (
        "# Navegación JSON (jq_path)\n\n"
        "El parámetro `jq_path` de fetch_json permite navegar el JSON:\n"
        "- `data` — Acceder a la clave 'data'.\n"
        "- `data.items` — Acceder a data.items.\n"
        "- `data.items[0]` — Primer elemento del array.\n"
        "- `data.items[0].name` — Nombre del primer item.\n"
        "- `results[2].address.city` — Path anidado con índice.\n"
        "\n"
        "Notación: punto para claves, [n] para índices de array."
    )


def html_extraction_tips() -> str:
    """Consejos para extracción de texto HTML."""
    return (
        "# Extracción de texto HTML\n\n"
        "- `extract_text` elimina scripts, estilos, nav, footer y aside.\n"
        "- Usa `include_links=true` para obtener enlaces de la página.\n"
        "- Usa `include_title=true` (default) para obtener el <title>.\n"
        "- El texto se limpia de tags y se preservan los saltos de línea.\n"
        "- Para contenido no-HTML, usa `fetch_url` en su lugar."
    )


def common_api_examples() -> str:
    """Ejemplos de APIs comunes."""
    return json.dumps(
        {
            "examples": [
                {"name": "GitHub API", "url": "https://api.github.com/repos/python/cpython", "tool": "fetch_json"},
                {"name": "Docker Hub", "url": "https://hub.docker.com/v2/repositories/library/python", "tool": "fetch_json"},
                {"name": "Kubernetes docs", "url": "https://kubernetes.io/docs/home/", "tool": "extract_text"},
                {"name": "Spring Boot actuator", "url": "http://localhost:8080/actuator/health", "tool": "fetch_json"},
                {"name": "NPM registry", "url": "https://registry.npmjs.org/express", "tool": "fetch_json"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def fetch_configuration() -> str:
    """Configuración actual del servidor fetch."""
    return json.dumps(
        {
            "default_timeout_seconds": settings.default_timeout,
            "max_content_length_bytes": settings.max_content_length,
            "user_agent": settings.user_agent,
            "follow_redirects": settings.follow_redirects,
            "allow_private_networks": settings.allow_private_networks,
            "verify_ssl": settings.verify_ssl,
        },
        indent=2,
        ensure_ascii=False,
    )


def rate_limiting_tips() -> str:
    """Consejos sobre rate limiting."""
    return (
        "# Rate limiting\n\n"
        "- Muchas APIs limitan el número de peticiones por minuto.\n"
        "- HTTP 429 indica que se excedió el rate limit.\n"
        "- Revisa el header `Retry-After` para saber cuándo reintentar.\n"
        "- Considera cachear respuestas cuando sea posible.\n"
        "- Usa timeouts razonables para no saturar el servidor."
    )


def error_handling_guide() -> str:
    """Guía de manejo de errores HTTP."""
    return (
        "# Manejo de errores HTTP\n\n"
        "- 4xx: Error del cliente (URL incorrecta, sin permisos, etc).\n"
        "- 5xx: Error del servidor (problema temporal o bug).\n"
        "- Timeout: El servidor no respondió a tiempo.\n"
        "- Connection error: No se pudo conectar al host.\n"
        "- SSL error: Certificado inválido o expirado.\n"
        "- El MCP devuelve errores estructurados con código y mensaje."
    )


def url_validation_rules() -> str:
    """Reglas de validación de URLs."""
    return (
        "# Validación de URLs\n\n"
        "- Solo se permiten esquemas http:// y https://.\n"
        "- No se permiten credenciales embebidas (user:pass@host).\n"
        "- Si MCP_FETCH_ALLOW_PRIVATE_NETWORKS=false:\n"
        "  - Se bloquean IPs loopback (127.x, ::1).\n"
        "  - Se bloquean IPs privadas (10.x, 172.16-31.x, 192.168.x).\n"
        "  - Se bloquean IPs link-local (169.254.x).\n"
        "  - Se bloquean IPs reservadas.\n"
        "- Se valida la URL final tras redirecciones."
    )


def example_fetch_url() -> str:
    """Ejemplo de uso de fetch_url."""
    return (
        "# Ejemplo: fetch_url\n\n"
        "```\n"
        "fetch_url(\n"
        "    url='https://httpbin.org/get',\n"
        "    headers={'X-Custom': 'value'},\n"
        "    timeout=15\n"
        ")\n"
        "```\n"
        "Retorna: url, status_code, content_type, content, truncated, headers, elapsed_ms"
    )


def example_fetch_json() -> str:
    """Ejemplo de uso de fetch_json."""
    return (
        "# Ejemplo: fetch_json\n\n"
        "```\n"
        "fetch_json(\n"
        "    url='https://api.github.com/repos/python/cpython',\n"
        "    headers={'Authorization': 'Bearer ghp_xxx'},\n"
        "    jq_path='stargazers_count'\n"
        ")\n"
        "```\n"
        "Retorna: url, data, status_code, path_used"
    )
