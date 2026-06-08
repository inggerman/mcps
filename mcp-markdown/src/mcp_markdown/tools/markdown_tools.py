"""
Herramientas MCP para leer, analizar, transformar y validar archivos Markdown.

Implementa todas las tools del servidor mcp-markdown usando:
- mistune >= 3.0  para parsing de AST
- python-frontmatter para extracción de metadatos YAML
- mdformat para normalización del formato
- markdown (Python-Markdown) como motor HTML alternativo
"""

from __future__ import annotations

import re
import textwrap
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import frontmatter  # python-frontmatter
import mdformat
import mistune
from mistune import create_markdown
from mistune.renderers.html import HTMLRenderer

from mcp_markdown.config import settings


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------


def _read_file(path: str | Path) -> tuple[str, Path]:
    """
    Lee un archivo Markdown y retorna (contenido, Path resuelto).

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el archivo supera el tamaño máximo o no es Markdown.
        PermissionError: Si no hay permisos de lectura.
    """
    resolved = Path(path).resolve()
    if not resolved.exists():
        msg = f"Archivo no encontrado: {resolved}"
        raise FileNotFoundError(msg)
    if not resolved.is_file():
        msg = f"La ruta no es un archivo: {resolved}"
        raise ValueError(msg)
    if not settings.is_markdown_file(resolved):
        msg = (
            f"Extensión '{resolved.suffix}' no reconocida como Markdown. "
            f"Extensiones permitidas: {settings.allowed_extensions}"
        )
        raise ValueError(msg)
    size = resolved.stat().st_size
    if size > settings.max_file_size_bytes:
        msg = (
            f"Archivo demasiado grande: {size / 1_048_576:.1f} MB "
            f"(máximo: {settings.max_file_size_mb} MB)"
        )
        raise ValueError(msg)
    return resolved.read_text(encoding="utf-8"), resolved


def _slugify(text: str) -> str:
    """Genera un slug/anchor HTML a partir de un texto de encabezado."""
    # Normalizar unicode
    text = unicodedata.normalize("NFKD", text)
    # Convertir a ASCII ignorando caracteres no convertibles
    text = text.encode("ascii", "ignore").decode("ascii")
    # Minúsculas y reemplazar no-alfanuméricos por guión
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Separa y retorna (frontmatter_dict, body_text).

    El body_text es el Markdown sin el bloque YAML inicial.
    """
    post = frontmatter.loads(content)
    return dict(post.metadata), post.content


def _extract_title_from_body(body: str) -> str | None:
    """Extrae el primer H1 del cuerpo Markdown (sin frontmatter)."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


# ---------------------------------------------------------------------------
# AST walker con mistune 3.x
# ---------------------------------------------------------------------------


class _ASTCollector:
    """
    Recorre el AST de mistune 3.x (formato lista de tokens) y recopila
    headings, links e imágenes y bloques de código.
    """

    def __init__(self) -> None:
        self.headings: list[dict[str, Any]] = []
        self.links: list[dict[str, Any]] = []
        self.code_blocks: list[dict[str, Any]] = []
        self.images: list[dict[str, Any]] = []

    def walk(self, tokens: list[dict[str, Any]], line_offset: int = 0) -> None:  # noqa: ANN401
        """Recorre la lista de tokens del AST recursivamente."""
        current_line = line_offset
        for token in tokens:
            token_type = token.get("type", "")

            if token_type == "heading":
                level = token.get("attrs", {}).get("level", 1)
                text = self._extract_text(token.get("children", []))
                self.headings.append(
                    {
                        "level": level,
                        "text": text,
                        "anchor": _slugify(text),
                    }
                )

            elif token_type == "code":
                attrs = token.get("attrs", {})
                info = attrs.get("info", "") or ""
                language = info.split()[0] if info.strip() else None
                code = token.get("raw", "")
                self.code_blocks.append(
                    {
                        "language": language,
                        "code": code,
                        "line_start": current_line + 1,
                    }
                )

            elif token_type == "image":
                attrs = token.get("attrs", {})
                alt = self._extract_text(token.get("children", []))
                self.images.append(
                    {
                        "text": alt,
                        "url": attrs.get("url", ""),
                        "title": attrs.get("title"),
                        "is_image": True,
                    }
                )
                self.links.append(
                    {
                        "text": alt,
                        "url": attrs.get("url", ""),
                        "title": attrs.get("title"),
                        "is_image": True,
                        "is_external": _is_external_url(attrs.get("url", "")),
                    }
                )

            elif token_type == "link":
                attrs = token.get("attrs", {})
                text = self._extract_text(token.get("children", []))
                url = attrs.get("url", "")
                self.links.append(
                    {
                        "text": text,
                        "url": url,
                        "title": attrs.get("title"),
                        "is_image": False,
                        "is_external": _is_external_url(url),
                    }
                )

            # Recurse into children
            children = token.get("children")
            if isinstance(children, list):
                self.walk(children, current_line)

    @staticmethod
    def _extract_text(children: list[dict[str, Any]]) -> str:
        """Extrae texto plano de una lista de tokens hijos."""
        parts: list[str] = []
        for child in children:
            if child.get("type") == "text" or child.get("type") == "raw_text":
                parts.append(child.get("raw", ""))
            elif child.get("type") == "softline":
                parts.append(" ")
            elif "children" in child:
                parts.append(_ASTCollector._extract_text(child["children"]))
            elif "raw" in child:
                parts.append(child["raw"])
        return "".join(parts)


def _is_external_url(url: str) -> bool:
    """Retorna True si la URL es absoluta/externa (http/https/ftp/etc.)."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https", "ftp", "ftps"}
    except Exception:  # noqa: BLE001
        return False


def _build_ast(body: str) -> list[dict[str, Any]]:
    """Construye el AST de mistune 3.x desde el cuerpo Markdown."""
    md = mistune.create_markdown(renderer=None)  # renderer=None → AST
    result = md(body)
    if isinstance(result, list):
        return result
    return []


# ---------------------------------------------------------------------------
# Tools públicas
# ---------------------------------------------------------------------------


def read_markdown(path: str) -> dict[str, Any]:
    """
    Lee y analiza un archivo Markdown completo.

    Returns:
        dict con:
        - content: texto completo (incluyendo frontmatter)
        - frontmatter: dict de metadatos YAML
        - title: primer H1 del cuerpo o None
        - word_count: número de palabras del cuerpo
        - headings: lista de dicts {level, text, anchor}
        - links: lista de dicts {text, url, is_external, is_image, title}
        - code_blocks: lista de dicts {language, code, line_start}
        - images: lista de dicts {text, url, title}
    """
    content, _ = _read_file(path)
    fm_data, body = _parse_frontmatter(content)
    ast = _build_ast(body)
    collector = _ASTCollector()
    collector.walk(ast)

    # Word count: contar palabras en el texto plano del body
    plain = re.sub(r"```[\s\S]*?```", "", body)  # quitar code blocks
    plain = re.sub(r"`[^`]+`", "", plain)  # quitar inline code
    plain = re.sub(r"!\[.*?\]\(.*?\)", "", plain)  # quitar imágenes
    plain = re.sub(r"\[.*?\]\(.*?\)", "", plain)  # quitar links
    plain = re.sub(r"[#*_~`>|]", "", plain)  # quitar markup
    word_count = len(plain.split())

    title = _extract_title_from_body(body)

    return {
        "content": content,
        "frontmatter": fm_data,
        "title": title,
        "word_count": word_count,
        "headings": collector.headings,
        "links": [lnk for lnk in collector.links if not lnk.get("is_image")],
        "code_blocks": collector.code_blocks,
        "images": collector.images,
    }


def extract_headings(path: str) -> list[dict[str, Any]]:
    """
    Extrae todos los encabezados de un archivo Markdown.

    Returns:
        Lista de dicts con:
        - level (int 1-6)
        - text (str)
        - anchor (str)
    """
    content, _ = _read_file(path)
    _, body = _parse_frontmatter(content)
    ast = _build_ast(body)
    collector = _ASTCollector()
    collector.walk(ast)
    return collector.headings


def extract_links(path: str) -> list[dict[str, Any]]:
    """
    Extrae todos los enlaces de un archivo Markdown.

    Returns:
        Lista de dicts con:
        - text (str): texto visible del enlace
        - url (str): URL de destino
        - title (str | None): título opcional
        - is_external (bool): True si la URL es http/https
        - is_image (bool): True si es una imagen embebida
    """
    content, _ = _read_file(path)
    _, body = _parse_frontmatter(content)
    ast = _build_ast(body)
    collector = _ASTCollector()
    collector.walk(ast)
    return collector.links


def extract_code_blocks(path: str) -> list[dict[str, Any]]:
    """
    Extrae todos los bloques de código (cercas triple backtick) de un archivo Markdown.

    Returns:
        Lista de dicts con:
        - language (str | None): lenguaje declarado
        - code (str): contenido del bloque
        - line_start (int | None): línea de inicio en el documento
    """
    content, _ = _read_file(path)
    _, body = _parse_frontmatter(content)
    ast = _build_ast(body)
    collector = _ASTCollector()
    collector.walk(ast)
    return collector.code_blocks


def get_toc(path: str, max_depth: int | None = None) -> str:
    """
    Genera una tabla de contenidos Markdown para el archivo.

    Args:
        path: Ruta al archivo Markdown.
        max_depth: Profundidad máxima de encabezados a incluir (1-6).
                   Por defecto usa settings.default_max_toc_depth.

    Returns:
        Cadena Markdown con la tabla de contenidos formateada con listas anidadas.
    """
    depth = max_depth if max_depth is not None else settings.default_max_toc_depth
    depth = max(1, min(6, depth))

    headings = extract_headings(path)
    if not headings:
        return "_No se encontraron encabezados._"

    lines: list[str] = []
    for h in headings:
        if h["level"] > depth:
            continue
        indent = "  " * (h["level"] - 1)
        anchor = h["anchor"]
        text = h["text"]
        lines.append(f"{indent}- [{text}](#{anchor})")

    return "\n".join(lines) if lines else "_No se encontraron encabezados dentro del nivel indicado._"


def markdown_to_html(path_or_text: str, is_path: bool = True) -> str:
    """
    Convierte Markdown a HTML completo.

    Args:
        path_or_text: Ruta a un archivo Markdown, o texto Markdown directo.
        is_path: Si True (por defecto), trata path_or_text como ruta de archivo.

    Returns:
        Cadena HTML completa con wrapper <html><body>.
    """
    if is_path:
        raw, resolved = _read_file(path_or_text)
        _, body = _parse_frontmatter(raw)
        title_hint = _extract_title_from_body(body) or resolved.stem
    else:
        body = path_or_text
        _, body = _parse_frontmatter(body)
        title_hint = _extract_title_from_body(body) or "Documento"

    md_renderer = create_markdown(
        renderer=HTMLRenderer(escape=False),
        plugins=["strikethrough", "table", "url"],
    )
    html_body: str = md_renderer(body)  # type: ignore[assignment]

    return textwrap.dedent(f"""\
        <!DOCTYPE html>
        <html lang="es">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{title_hint}</title>
          <style>
            body {{ font-family: system-ui, sans-serif; max-width: 860px; margin: 2rem auto; line-height: 1.7; }}
            pre {{ background: #f4f4f4; padding: 1rem; border-radius: 6px; overflow-x: auto; }}
            code {{ background: #f4f4f4; padding: .1em .3em; border-radius: 3px; font-size: .92em; }}
            pre code {{ background: none; padding: 0; }}
            blockquote {{ border-left: 4px solid #ccc; margin-left: 0; padding-left: 1rem; color: #555; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: .5rem 1rem; }}
            th {{ background: #f0f0f0; }}
            img {{ max-width: 100%; height: auto; }}
            a {{ color: #0366d6; }}
          </style>
        </head>
        <body>
        {html_body}
        </body>
        </html>
        """)


def markdown_to_plain_text(path_or_text: str, is_path: bool = True) -> str:
    """
    Convierte Markdown a texto plano limpio (sin markup).

    Args:
        path_or_text: Ruta a un archivo Markdown o texto Markdown directo.
        is_path: Si True, trata path_or_text como ruta de archivo.

    Returns:
        Texto plano sin caracteres de markup Markdown.
    """
    if is_path:
        raw, _ = _read_file(path_or_text)
        _, body = _parse_frontmatter(raw)
    else:
        _, body = _parse_frontmatter(path_or_text)

    text = body

    # Quitar bloques de código fenced (con contenido)
    text = re.sub(r"```[^\n]*\n([\s\S]*?)```", r"\1", text)
    # Quitar código inline
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Quitar imágenes
    text = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", text)
    # Convertir links a solo texto
    text = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", text)
    # Quitar links de referencia
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    # Quitar definiciones de referencia
    text = re.sub(r"^\s{0,3}\[[^\]]+\]:\s+\S+.*$", "", text, flags=re.MULTILINE)
    # Quitar encabezados (mantener texto)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Quitar énfasis negrita/itálica
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
    # Quitar strikethrough
    text = re.sub(r"~~([^~]+)~~", r"\1", text)
    # Quitar reglas horizontales
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Quitar viñetas de listas
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    # Quitar listas numeradas
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Quitar blockquotes
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # Quitar líneas de tabla
    text = re.sub(r"^\|.*\|$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-|: ]+$", "", text, flags=re.MULTILINE)
    # Comprimir múltiples líneas en blanco
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def validate_markdown(path: str) -> dict[str, Any]:
    """
    Valida un archivo Markdown y reporta problemas comunes.

    Returns:
        dict con:
        - valid (bool): True si no hay warnings ni broken_links
        - warnings (list[str]): lista de advertencias
        - broken_links (list[dict]): enlaces locales rotos
        - duplicate_headings (list[str]): textos de headings duplicados
    """
    content, resolved = _read_file(path)
    fm_data, body = _parse_frontmatter(content)
    ast = _build_ast(body)
    collector = _ASTCollector()
    collector.walk(ast)

    warnings: list[str] = []
    broken_links: list[dict[str, Any]] = []
    base_dir = resolved.parent

    # --- Comprobar H1 único ---
    h1_headings = [h for h in collector.headings if h["level"] == 1]
    if not h1_headings:
        warnings.append("El documento no tiene encabezado H1.")
    elif len(h1_headings) > 1:
        warnings.append(f"El documento tiene {len(h1_headings)} encabezados H1 (se recomienda 1).")

    # --- Detectar headings duplicados ---
    seen_texts: dict[str, int] = {}
    duplicate_texts: list[str] = []
    for h in collector.headings:
        t = h["text"]
        seen_texts[t] = seen_texts.get(t, 0) + 1
    for text, count in seen_texts.items():
        if count > 1:
            duplicate_texts.append(text)
            warnings.append(f"Encabezado duplicado ({count} veces): '{text}'")

    # --- Comprobar enlances locales rotos ---
    for link in collector.links:
        url = link.get("url", "")
        if not url or url.startswith("#") or _is_external_url(url):
            continue
        # Quitar fragmentos
        url_path = url.split("#")[0]
        if not url_path:
            continue
        target = (base_dir / url_path).resolve()
        if not target.exists():
            broken_links.append(
                {
                    "text": link.get("text", ""),
                    "url": url,
                    "resolved_path": str(target),
                }
            )
            warnings.append(f"Enlace local roto: '{url}'")

    # --- Comprobar frontmatter recomendado ---
    if not fm_data.get("title") and not h1_headings:
        warnings.append("Sin título: ni frontmatter 'title' ni encabezado H1.")

    return {
        "valid": len(warnings) == 0 and len(broken_links) == 0,
        "warnings": warnings,
        "broken_links": broken_links,
        "duplicate_headings": duplicate_texts,
    }


def search_in_markdown(
    path: str,
    query: str,
    case_sensitive: bool = False,
) -> list[dict[str, Any]]:
    """
    Busca un texto en un archivo Markdown línea por línea.

    Args:
        path: Ruta al archivo Markdown.
        query: Texto a buscar.
        case_sensitive: Si False (por defecto), busca sin distinguir mayúsculas.

    Returns:
        Lista de dicts con:
        - line_number (int): número de línea donde se encontró (1-based)
        - context (str): línea completa
        - heading_context (str | None): encabezado bajo el que aparece la coincidencia
    """
    content, _ = _read_file(path)
    _, body = _parse_frontmatter(content)

    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(query), flags)

    # Construir mapa de línea → heading context
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
    current_heading: str | None = None
    line_to_heading: dict[int, str | None] = {}
    for i, line in enumerate(body.splitlines(), start=1):
        m = heading_pattern.match(line)
        if m:
            current_heading = m.group(2).strip()
        line_to_heading[i] = current_heading

    results: list[dict[str, Any]] = []
    for i, line in enumerate(body.splitlines(), start=1):
        if pattern.search(line):
            results.append(
                {
                    "line_number": i,
                    "context": line,
                    "heading_context": line_to_heading.get(i),
                }
            )

    return results


def format_markdown(path_or_text: str, is_path: bool = True) -> str:
    """
    Formatea Markdown usando mdformat (normaliza espacios, headings, listas, etc.).

    Args:
        path_or_text: Ruta a un archivo Markdown o texto Markdown directo.
        is_path: Si True, trata path_or_text como ruta de archivo.

    Returns:
        Texto Markdown formateado.
    """
    if is_path:
        raw, _ = _read_file(path_or_text)
        text = raw
    else:
        text = path_or_text

    return mdformat.text(text)


def get_frontmatter(path: str) -> dict[str, Any]:
    """
    Extrae solo el frontmatter YAML de un archivo Markdown.

    Returns:
        dict con los metadatos del frontmatter. Vacío si no hay frontmatter.
    """
    content, _ = _read_file(path)
    fm_data, _ = _parse_frontmatter(content)
    return fm_data


def list_markdown_files(directory: str, recursive: bool = True) -> list[dict[str, Any]]:
    """
    Lista todos los archivos Markdown en un directorio.

    Args:
        directory: Ruta al directorio a explorar.
        recursive: Si True (por defecto), busca recursivamente en subdirectorios.

    Returns:
        Lista de dicts con:
        - path (str): ruta absoluta del archivo
        - relative_path (str): ruta relativa al directorio base
        - title (str | None): primer H1 o frontmatter['title']
        - word_count (int): número de palabras
        - size_bytes (int): tamaño del archivo
        - frontmatter (dict): metadatos del frontmatter
    """
    base = Path(directory).resolve()
    if not base.exists():
        msg = f"Directorio no encontrado: {base}"
        raise FileNotFoundError(msg)
    if not base.is_dir():
        msg = f"La ruta no es un directorio: {base}"
        raise ValueError(msg)

    results: list[dict[str, Any]] = []
    pattern = "**/*" if recursive else "*"

    for file_path in sorted(base.glob(pattern)):
        if not file_path.is_file():
            continue
        if not settings.is_markdown_file(file_path):
            continue
        if file_path.stat().st_size > settings.max_file_size_bytes:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            fm_data, body = _parse_frontmatter(content)

            # Título: frontmatter['title'] > primer H1
            title: str | None = fm_data.get("title") or _extract_title_from_body(body)

            # Word count
            plain = re.sub(r"```[\s\S]*?```", "", body)
            plain = re.sub(r"`[^`]+`", "", plain)
            plain = re.sub(r"[#*_~`>|\[\]!]", "", plain)
            word_count = len(plain.split())

            results.append(
                {
                    "path": str(file_path),
                    "relative_path": str(file_path.relative_to(base)),
                    "title": title,
                    "word_count": word_count,
                    "size_bytes": file_path.stat().st_size,
                    "frontmatter": fm_data,
                }
            )
        except Exception:  # noqa: BLE001
            # Ignorar archivos que no se puedan leer
            continue

    return results
