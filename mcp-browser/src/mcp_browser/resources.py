"""Resources de solo lectura para mcp-browser.

Expone metadatos, guias y consejos sobre automatizacion web con Playwright
como URIs accesibles para el modelo a traves de `@mcp.resource`.
"""

from __future__ import annotations

import json

from mcp_browser.config import settings


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


def supported_selectors() -> str:
    """Selectores CSS soportados para extraccion."""
    return (
        "# Selectores CSS soportados\n\n"
        "- `body` — Todo el cuerpo de la pagina.\n"
        "- `#id` — Elemento por ID.\n"
        "- `.class` — Elementos por clase.\n"
        "- `div.content` — Div con clase content.\n"
        "- `article` — Etiqueta article.\n"
        "- `main` — Contenido principal.\n"
        "- `table` — Tablas.\n"
        "- `nav` — Navegacion.\n"
        "- Combinaciones: `div.main > p`, `ul li:first-child`\n"
        "- Atributos: `[data-testid='value']`, `input[type='text']`"
    )


def playwright_tips() -> str:
    """Consejos de uso de Playwright."""
    return (
        "# Consejos Playwright\n\n"
        "- Playwright usa Chromium por defecto (headless=true).\n"
        "- BROWSER_HEADLESS=false para modo visible (debug).\n"
        "- BROWSER_TIMEOUT_MS controla el timeout (default 30s).\n"
        "- wait_until='domcontentloaded' para extraccion rapida.\n"
        "- wait_until='networkidle' para capturas completas.\n"
        "- full_page=true captura toda la pagina (no solo viewport)."
    )


def web_scraping_best_practices() -> str:
    """Mejores practicas de web scraping."""
    return (
        "# Web scraping responsable\n\n"
        "- Respeta robots.txt y terminos de servicio.\n"
        "- Usa delays entre peticiones para no saturar el servidor.\n"
        "- Identificate con un User-Agent apropiado.\n"
        "- Cachea resultados cuando sea posible.\n"
        "- Extrae solo lo necesario, no toda la pagina.\n"
        "- Maneja errores y timeouts gracefulmente."
    )


def browser_security_guide() -> str:
    """Guia de seguridad del navegador."""
    return (
        "# Seguridad del navegador\n\n"
        "- BROWSER_ALLOWED_HOSTS controla que sitios se pueden visitar.\n"
        "- Si la lista esta vacia, se permiten todos los hosts.\n"
        "- Solo se permiten esquemas http:// y https://.\n"
        "- No se permiten credenciales embebidas en URLs.\n"
        "- El navegador corre en modo headless por defecto.\n"
        "- Las capturas se guardan en BROWSER_OUTPUT_DIR."
    )


def css_selector_cheatsheet() -> str:
    """Cheatsheet de selectores CSS."""
    return json.dumps(
        {
            "selectors": [
                {"selector": "*", "description": "Todos los elementos"},
                {"selector": "element", "description": "Por etiqueta"},
                {"selector": "#id", "description": "Por ID"},
                {"selector": ".class", "description": "Por clase"},
                {"selector": "A > B", "description": "Hijo directo"},
                {"selector": "A B", "description": "Descendiente"},
                {"selector": "A + B", "description": "Hermano adyacente"},
                {"selector": "A ~ B", "description": "Hermanos generales"},
                {"selector": "[attr]", "description": "Con atributo"},
                {"selector": "[attr='val']", "description": "Atributo con valor"},
                {"selector": ":first-child", "description": "Primer hijo"},
                {"selector": ":last-child", "description": "Ultimo hijo"},
                {"selector": ":nth-child(n)", "description": "Enesimo hijo"},
                {"selector": ":not(sel)", "description": "Negacion"},
                {"selector": ":text('str')", "description": "Playwright: contiene texto"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def screenshot_tips() -> str:
    """Consejos para capturas de pantalla."""
    return (
        "# Capturas de pantalla\n\n"
        "- browser_screenshot captura la pagina completa por defecto.\n"
        "- full_page=false para capturar solo el viewport visible.\n"
        "- El archivo se guarda como PNG en BROWSER_OUTPUT_DIR.\n"
        "- El nombre debe terminar en .png.\n"
        "- Se sanitiza el nombre para evitar path traversal."
    )


def common_use_cases() -> str:
    """Casos de uso comunes del navegador."""
    return (
        "# Casos de uso comunes\n\n"
        "- **Extraer texto**: `browser_extract(url, selector='body')`\n"
        "- **Extraer tabla**: `browser_extract(url, selector='table')`\n"
        "- **Extraer articulo**: `browser_extract(url, selector='article')`\n"
        "- **Capturar pagina**: `browser_screenshot(url, filename='page.png')`\n"
        "- **Capturar viewport**: `browser_screenshot(url, full_page=False)`\n"
        "- **Obtener titulo**: `browser_extract(url, selector='title')`"
    )


def browser_configuration() -> str:
    """Configuracion actual del navegador."""
    return json.dumps(
        {
            "headless": settings.headless,
            "timeout_ms": settings.timeout_ms,
            "allowed_hosts": settings.allowed_hosts,
            "output_dir": str(settings.output_dir),
        },
        indent=2,
        ensure_ascii=False,
    )


def error_handling_tips() -> str:
    """Consejos de manejo de errores del navegador."""
    return (
        "# Manejo de errores\n\n"
        "- Timeout: La pagina tardo mas de BROWSER_TIMEOUT_MS.\n"
        "- Navigation error: La URL no responde o devuelve error.\n"
        "- Selector not found: El selector CSS no existe en la pagina.\n"
        "- Host not allowed: El host no esta en BROWSER_ALLOWED_HOSTS.\n"
        "- Invalid URL: Esquema no soportado o credenciales embebidas."
    )


def playwright_installation_guide() -> str:
    """Guia de instalacion de Playwright."""
    return (
        "# Instalacion de Playwright\n\n"
        "- `pip install playwright`\n"
        "- `playwright install chromium` (descarga el browser)\n"
        "- En Docker: `RUN playwright install chromium --with-deps`\n"
        "- Requiere dependencias del sistema en Linux.\n"
        "- El MCP ya incluye Playwright en sus dependencias."
    )


def page_interaction_patterns() -> str:
    """Patrones de interaccion con paginas."""
    return (
        "# Patrones de interaccion\n\n"
        "- **Navegar**: `page.goto(url, wait_until='domcontentloaded')`\n"
        "- **Esperar selector**: `page.wait_for_selector(selector)`\n"
        "- **Click**: `page.click(selector)`\n"
        "- **Escribir**: `page.fill(selector, value)`\n"
        "- **Extraer texto**: `page.locator(selector).inner_text()`\n"
        "- **Extraer HTML**: `page.locator(selector).inner_html()`\n"
        "- **Capturar**: `page.screenshot(path=file, full_page=True)`"
    )


def url_validation_rules() -> str:
    """Reglas de validacion de URLs del navegador."""
    return (
        "# Validacion de URLs\n\n"
        "- Solo esquemas http:// y https://.\n"
        "- No se permiten credenciales embebidas (user:pass@host).\n"
        "- Si BROWSER_ALLOWED_HOSTS no esta vacio, el host debe estar en la lista.\n"
        "- Si la lista esta vacia, se permiten todos los hosts publicos."
    )


def example_extract_page() -> str:
    """Ejemplo de extraccion de pagina."""
    return (
        "# Ejemplo: browser_extract\n\n"
        "```\n"
        "browser_extract(\n"
        "    url='https://example.com',\n"
        "    selector='article.main-content'\n"
        ")\n"
        "```\n"
        "Retorna: url, title, text, html"
    )


def example_screenshot() -> str:
    """Ejemplo de captura de pantalla."""
    return (
        "# Ejemplo: browser_screenshot\n\n"
        "```\n"
        "browser_screenshot(\n"
        "    url='https://example.com',\n"
        "    filename='homepage.png',\n"
        "    full_page=True\n"
        ")\n"
        "```\n"
        "Retorna: url, path"
    )
