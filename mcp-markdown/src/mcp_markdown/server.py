"""
Servidor FastMCP para el procesamiento de archivos Markdown.

Registra todas las herramientas del módulo markdown_tools y configura
el servidor con lifespan, logging estructurado e instrucciones.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp_shared.logging import setup_logging

from mcp_markdown.config import settings
from mcp_markdown.tools.markdown_tools import (
    extract_code_blocks,
    extract_headings,
    extract_links,
    format_markdown,
    get_frontmatter,
    get_toc,
    list_markdown_files,
    markdown_to_html,
    markdown_to_plain_text,
    read_markdown,
    search_in_markdown,
    validate_markdown,
)

# ---------------------------------------------------------------------------
# Logging estructurado
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name=settings.server_name,
)

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Ciclo de vida del servidor: startup y shutdown."""
    log.info(
        "mcp-markdown iniciando",
        version=settings.server_version,
        log_level=settings.log_level,
        max_file_size_mb=settings.max_file_size_mb,
        allowed_extensions=settings.allowed_extensions,
    )
    yield
    log.info("mcp-markdown detenido")


# ---------------------------------------------------------------------------
# Instancia del servidor
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name=settings.server_name,
    instructions=f"""
Servidor MCP especializado en lectura, análisis, transformación y validación
de archivos Markdown (.md, .markdown, .mdx, .mdown, .mkd).

## Capacidades disponibles

### 📖 Lectura y análisis
- **read_markdown**: Lectura completa con frontmatter, headings, links, código e imágenes.
- **get_frontmatter**: Extrae solo los metadatos YAML del frontmatter.
- **extract_headings**: Lista de encabezados (H1-H6) con nivel, texto y anchor.
- **extract_links**: Todos los enlaces con URL, texto, tipo (externo/interno/imagen).
- **extract_code_blocks**: Bloques de código con lenguaje y contenido.

### 🗂 Organización
- **get_toc**: Tabla de contenidos Markdown con enlaces de anclaje.
- **list_markdown_files**: Inventario de archivos Markdown en un directorio.

### 🔄 Transformación
- **markdown_to_html**: Convierte Markdown a HTML5 completo con estilos.
- **markdown_to_plain_text**: Elimina todo el markup y retorna texto limpio.
- **format_markdown**: Normaliza el formato del Markdown con mdformat.

### 🔍 Búsqueda y validación
- **search_in_markdown**: Búsqueda de texto con contexto de línea y encabezado.
- **validate_markdown**: Detecta H1 faltante/duplicado, enlaces rotos y otros problemas.

## Formatos soportados
.md · .markdown · .mdx · .mdown · .mkd

## Límites
- Tamaño máximo de archivo: {settings.max_file_size_mb} MB
""",
    lifespan=_lifespan,
)


# ---------------------------------------------------------------------------
# Registro de tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="read_markdown",
    description=(
        "Lee y analiza un archivo Markdown de forma completa. "
        "Retorna el contenido crudo, frontmatter YAML, título (primer H1), "
        "recuento de palabras, headings, links, bloques de código e imágenes."
    ),
)
def tool_read_markdown(path: str) -> dict[str, Any]:
    """
    Args:
        path: Ruta absoluta o relativa al archivo Markdown.
    """
    return read_markdown(path)


@mcp.tool(
    name="extract_headings",
    description=(
        "Extrae todos los encabezados (H1-H6) de un archivo Markdown. "
        "Cada encabezado incluye su nivel (1-6), texto y anchor HTML."
    ),
)
def tool_extract_headings(path: str) -> list[dict[str, Any]]:
    """
    Args:
        path: Ruta absoluta o relativa al archivo Markdown.
    """
    return extract_headings(path)


@mcp.tool(
    name="extract_links",
    description=(
        "Extrae todos los enlaces de un archivo Markdown, incluyendo imágenes. "
        "Cada enlace indica texto, URL, si es externo y si es imagen."
    ),
)
def tool_extract_links(path: str) -> list[dict[str, Any]]:
    """
    Args:
        path: Ruta absoluta o relativa al archivo Markdown.
    """
    return extract_links(path)


@mcp.tool(
    name="extract_code_blocks",
    description=(
        "Extrae todos los bloques de código (fenced code blocks) de un archivo Markdown. "
        "Incluye el lenguaje declarado, el contenido y la línea de inicio."
    ),
)
def tool_extract_code_blocks(path: str) -> list[dict[str, Any]]:
    """
    Args:
        path: Ruta absoluta o relativa al archivo Markdown.
    """
    return extract_code_blocks(path)


@mcp.tool(
    name="get_toc",
    description=(
        "Genera una tabla de contenidos Markdown para el archivo, "
        "con enlaces de anclaje a cada encabezado. "
        "Se puede limitar la profundidad (1-6)."
    ),
)
def tool_get_toc(path: str, max_depth: int = 3) -> str:
    """
    Args:
        path: Ruta absoluta o relativa al archivo Markdown.
        max_depth: Profundidad máxima de encabezados a incluir (1-6). Por defecto 3.
    """
    return get_toc(path, max_depth=max_depth)


@mcp.tool(
    name="markdown_to_html",
    description=(
        "Convierte un archivo Markdown (o texto Markdown directo) a HTML5 completo "
        "con estilos básicos embebidos. Soporta tablas, strikethrough y autolinks."
    ),
)
def tool_markdown_to_html(path_or_text: str, is_path: bool = True) -> str:
    """
    Args:
        path_or_text: Ruta al archivo Markdown, o texto Markdown directo.
        is_path: True (por defecto) para tratar como ruta; False para texto directo.
    """
    return markdown_to_html(path_or_text, is_path=is_path)


@mcp.tool(
    name="markdown_to_plain_text",
    description=(
        "Convierte Markdown a texto plano eliminando todo el markup "
        "(encabezados, énfasis, links, bloques de código, tablas, etc.)."
    ),
)
def tool_markdown_to_plain_text(path_or_text: str, is_path: bool = True) -> str:
    """
    Args:
        path_or_text: Ruta al archivo Markdown, o texto Markdown directo.
        is_path: True (por defecto) para tratar como ruta; False para texto directo.
    """
    return markdown_to_plain_text(path_or_text, is_path=is_path)


@mcp.tool(
    name="validate_markdown",
    description=(
        "Valida un archivo Markdown y reporta problemas: "
        "H1 faltante o múltiple, encabezados duplicados, enlaces locales rotos, "
        "y ausencia de título. Retorna valid=True solo si no hay warnings."
    ),
)
def tool_validate_markdown(path: str) -> dict[str, Any]:
    """
    Args:
        path: Ruta absoluta o relativa al archivo Markdown.
    """
    return validate_markdown(path)


@mcp.tool(
    name="search_in_markdown",
    description=(
        "Busca un texto en un archivo Markdown línea por línea. "
        "Retorna cada coincidencia con número de línea, contexto completo "
        "y el encabezado bajo el cual aparece."
    ),
)
def tool_search_in_markdown(
    path: str,
    query: str,
    case_sensitive: bool = False,
) -> list[dict[str, Any]]:
    """
    Args:
        path: Ruta absoluta o relativa al archivo Markdown.
        query: Texto o frase a buscar.
        case_sensitive: Si True, distingue mayúsculas/minúsculas. Por defecto False.
    """
    return search_in_markdown(path, query, case_sensitive=case_sensitive)


@mcp.tool(
    name="format_markdown",
    description=(
        "Formatea y normaliza un archivo Markdown (o texto directo) usando mdformat. "
        "Estandariza encabezados, listas, espaciado y bloques de código."
    ),
)
def tool_format_markdown(path_or_text: str, is_path: bool = True) -> str:
    """
    Args:
        path_or_text: Ruta al archivo Markdown, o texto Markdown directo.
        is_path: True (por defecto) para tratar como ruta; False para texto directo.
    """
    return format_markdown(path_or_text, is_path=is_path)


@mcp.tool(
    name="get_frontmatter",
    description=(
        "Extrae solo el frontmatter YAML de un archivo Markdown. "
        "Retorna un dict vacío si el archivo no tiene frontmatter."
    ),
)
def tool_get_frontmatter(path: str) -> dict[str, Any]:
    """
    Args:
        path: Ruta absoluta o relativa al archivo Markdown.
    """
    return get_frontmatter(path)


@mcp.tool(
    name="list_markdown_files",
    description=(
        "Lista todos los archivos Markdown en un directorio. "
        "Para cada archivo retorna la ruta, título, recuento de palabras, "
        "tamaño y frontmatter. Soporta búsqueda recursiva."
    ),
)
def tool_list_markdown_files(
    directory: str,
    recursive: bool = True,
) -> list[dict[str, Any]]:
    """
    Args:
        directory: Ruta al directorio a explorar.
        recursive: Si True (por defecto), busca en subdirectorios.
    """
    return list_markdown_files(directory, recursive=recursive)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Punto de entrada principal del servidor."""
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
