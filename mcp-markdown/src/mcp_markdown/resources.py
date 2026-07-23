"""Resources de solo lectura para mcp-markdown.

Expone metadatos, guias y consejos sobre procesamiento de Markdown
como URIs accesibles para el modelo a traves de `@mcp.resource`.
"""

from __future__ import annotations

import json

from mcp_markdown.config import settings


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


def markdown_configuration() -> str:
    """Configuracion actual del servidor markdown."""
    return json.dumps(
        {
            "server_name": settings.server_name,
            "server_version": settings.server_version,
            "max_file_size_mb": settings.max_file_size_mb,
            "allowed_extensions": settings.allowed_extensions,
            "default_max_toc_depth": settings.default_max_toc_depth,
            "validate_external_links": settings.validate_external_links,
        },
        indent=2,
        ensure_ascii=False,
    )


def markdown_syntax_guide() -> str:
    """Guia de sintaxis Markdown."""
    return (
        "# Sintaxis Markdown\n\n"
        "- **Encabezados**: `# H1`, `## H2`, ... `###### H6`\n"
        "- **Negrita**: `**texto**`\n"
        "- **Cursiva**: `*texto*`\n"
        "- **Tachado**: `~~texto~~`\n"
        "- **Codigo inline**: `` `codigo` ``\n"
        "- **Bloque de codigo**: ``` ```lang ... ``` ```\n"
        "- **Enlaces**: `[texto](url)`\n"
        "- **Imagenes**: `![alt](url)`\n"
        "- **Listas**: `- item` o `1. item`\n"
        "- **Tablas**: `| col1 | col2 |`\n"
        "- **Blockquotes**: `> cita`\n"
        "- **Regla horizontal**: `---`\n"
        "- **Task lists**: `- [ ] todo` / `- [x] hecho`"
    )


def frontmatter_guide() -> str:
    """Guia de frontmatter YAML."""
    return (
        "# Frontmatter YAML\n\n"
        "Bloque de metadatos al inicio del archivo:\n"
        "```\n"
        "---\n"
        "title: Mi Documento\n"
        "date: 2025-01-15\n"
        "tags: [python, markdown]\n"
        "author: Juan Perez\n"
        "draft: false\n"
        "---\n"
        "```\n"
        "Usa get_frontmatter(path) para extraerlo.\n"
        "Usa read_markdown(path) para obtenerlo junto al contenido."
    )


def markdown_extensions() -> str:
    """Extensiones de archivo soportadas."""
    return json.dumps(
        {
            "extensions": settings.allowed_extensions,
            "description": "Extensiones reconocidas como archivos Markdown",
        },
        indent=2,
        ensure_ascii=False,
    )


def markdown_best_practices() -> str:
    """Mejores practicas para Markdown."""
    return (
        "# Mejores practicas Markdown\n\n"
        "- Usa un solo H1 por documento.\n"
        "- Manten una jerarquia de encabezados logica (no saltes niveles).\n"
        "- Usa frontmatter con title, date y tags.\n"
        "- Limita lineas a 80-120 caracteres cuando sea posible.\n"
        "- Usa bloques de codigo con lenguaje declarado.\n"
        "- Enlaces descriptivos: evita 'click aqui'.\n"
        "- Usa tablas solo para datos tabulares, no para layout.\n"
        "- Usa format_markdown() para normalizar el formato."
    )


def markdown_validation_tips() -> str:
    """Consejos de validacion de Markdown."""
    return (
        "# Validacion de Markdown\n\n"
        "- validate_markdown() detecta:\n"
        "  - H1 faltante o multiple\n"
        "  - Encabezados duplicados\n"
        "  - Enlaces locales rotos\n"
        "  - Ausencia de titulo\n"
        "- Retorna valid=True solo si no hay warnings.\n"
        "- Usa search_in_markdown() para buscar texto dentro del documento."
    )


def markdown_conversion_tips() -> str:
    """Consejos de conversion de Markdown."""
    return (
        "# Conversion de Markdown\n\n"
        "- markdown_to_html(): convierte a HTML5 con estilos embebidos.\n"
        "- markdown_to_plain_text(): elimina todo el markup.\n"
        "- format_markdown(): normaliza el formato con mdformat.\n"
        "- Ambas funciones aceptan ruta de archivo o texto directo.\n"
        "- Usa is_path=False para pasar texto directo."
    )


def common_markdown_workflows() -> str:
    """Flujos de trabajo comunes con Markdown."""
    return (
        "# Flujos comunes\n\n"
        "- **Leer**: read_markdown('docs/guide.md')\n"
        "- **Headings**: extract_headings('docs/guide.md')\n"
        "- **Links**: extract_links('docs/guide.md')\n"
        "- **Codigo**: extract_code_blocks('docs/guide.md')\n"
        "- **TOC**: get_toc('docs/guide.md', max_depth=3)\n"
        "- **Frontmatter**: get_frontmatter('docs/guide.md')\n"
        "- **HTML**: markdown_to_html('docs/guide.md')\n"
        "- **Texto plano**: markdown_to_plain_text('docs/guide.md')\n"
        "- **Validar**: validate_markdown('docs/guide.md')\n"
        "- **Buscar**: search_in_markdown('docs/guide.md', 'instalacion')\n"
        "- **Formatear**: format_markdown('docs/guide.md')\n"
        "- **Listar**: list_markdown_files('docs/', recursive=True)"
    )


def markdown_error_codes() -> str:
    """Codigos de error comunes del servidor markdown."""
    return json.dumps(
        {
            "errors": [
                {"code": "FILE_NOT_FOUND", "description": "Archivo no encontrado"},
                {"code": "INVALID_EXTENSION", "description": "Extension no reconocida como Markdown"},
                {"code": "FILE_TOO_LARGE", "description": "Archivo excede el tamano maximo"},
                {"code": "PERMISSION_DENIED", "description": "Sin permisos de lectura o ruta fuera del directorio permitido"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def markdown_table_syntax() -> str:
    """Sintaxis de tablas en Markdown."""
    return (
        "# Tablas Markdown\n\n"
        "```\n"
        "| Col1 | Col2 | Col3 |\n"
        "|------|------|------|\n"
        "| a    | b    | c    |\n"
        "| d    | e    | f    |\n"
        "```\n"
        "Alineacion:\n"
        "- `:---` izquierda\n"
        "- `:---:` centrado\n"
        "- `---:` derecha"
    )


def markdown_code_syntax() -> str:
    """Sintaxis de bloques de codigo en Markdown."""
    return (
        "# Bloques de codigo\n\n"
        "Bloque cercado (fenced):\n"
        "```python\n"
        "def hello():\n"
        "    print('Hello')\n"
        "```\n"
        "Codigo inline: `` `codigo` ``\n"
        "Lenguajes comunes: python, javascript, bash, json, yaml, sql, html, css."
    )


def markdown_link_syntax() -> str:
    """Sintaxis de enlaces en Markdown."""
    return (
        "# Enlaces en Markdown\n\n"
        "- Inline: `[texto](https://example.com)`\n"
        "- Con titulo: `[texto](https://example.com \"Titulo\")`\n"
        "- Referencia: `[texto][ref]` + `[ref]: https://example.com`\n"
        "- Auto-link: `<https://example.com>`\n"
        "- Interno: `[seccion](#anchor)`\n"
        "- Imagen: `![alt](imagen.png)`\n"
        "- Usa extract_links() para listar todos los enlaces."
    )


def markdown_toc_guide() -> str:
    """Guia de tabla de contenidos."""
    return (
        "# Tabla de contenidos\n\n"
        "- get_toc() genera un TOC automatico desde los encabezados.\n"
        "- max_depth controla la profundidad (1-6).\n"
        "- Los anchors se generan con slugify (minusculas, guiones).\n"
        "- El TOC usa listas anidadas con indentacion.\n"
        "- Por defecto usa default_max_toc_depth de la configuracion."
    )


def example_read_markdown() -> str:
    """Ejemplo de lectura de Markdown."""
    return (
        "# Ejemplo: read_markdown\n\n"
        "```\n"
        "read_markdown('docs/guide.md')\n"
        "```\n"
        "Retorna: content, frontmatter, title, word_count, headings, links, code_blocks, images"
    )


def example_validate_markdown() -> str:
    """Ejemplo de validacion de Markdown."""
    return (
        "# Ejemplo: validate_markdown\n\n"
        "```\n"
        "validate_markdown('docs/guide.md')\n"
        "```\n"
        "Retorna: valid (bool), warnings (list), broken_links (list), duplicate_headings (list)"
    )
