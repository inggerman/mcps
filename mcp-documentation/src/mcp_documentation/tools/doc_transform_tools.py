"""Doc Transform Tools — 7 herramientas para transformación de formatos."""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Any

import yaml
import xmltodict
from mistune import create_markdown
from mistune.renderers.html import HTMLRenderer

from mcp_documentation.config import settings
from mcp_documentation.tools.doc_read_tools import _resolve_path, _ensure_allowed, _read_file_text, _parse_frontmatter


def markdown_to_html(path_or_text: str, is_path: bool = True) -> str:
    """Convierte Markdown a HTML completo con CSS."""
    if is_path:
        resolved = _resolve_path(path_or_text)
        raw = _read_file_text(resolved)
        _, body = _parse_frontmatter(raw)
        title = body.split("\n")[0].replace("# ", "").strip() if body.startswith("#") else "Documento"
    else:
        _, body = _parse_frontmatter(path_or_text)
        title = "Documento"

    md_renderer = create_markdown(
        renderer=HTMLRenderer(escape=False),
        plugins=["strikethrough", "table", "url"],
    )
    html_body: str = md_renderer(body)

    return textwrap.dedent(f"""\
        <!DOCTYPE html>
        <html lang="es">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{title}</title>
          <style>
            body {{ font-family: system-ui, sans-serif; max-width: 860px; margin: 2rem auto; line-height: 1.7; }}
            pre {{ background: #f4f4f4; padding: 1rem; border-radius: 6px; overflow-x: auto; }}
            code {{ background: #f4f4f4; padding: .1em .3em; border-radius: 3px; }}
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


def html_to_markdown(html_text: str) -> str:
    """Convierte HTML a Markdown limpio."""
    text = html_text

    # Headers
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<h4[^>]*>(.*?)</h4>", r"#### \1\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<h5[^>]*>(.*?)</h5>", r"##### \1\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<h6[^>]*>(.*?)</h6>", r"###### \1\n", text, flags=re.IGNORECASE | re.DOTALL)

    # Bold and italic
    text = re.sub(r"<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<(?:em|i)[^>]*>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.IGNORECASE | re.DOTALL)

    # Links
    text = re.sub(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.IGNORECASE | re.DOTALL)

    # Images
    text = re.sub(r'<img[^>]+src="([^"]*)"[^>]+alt="([^"]*)"[^>]*/?\s*>', r'![\2](\1)', text, flags=re.IGNORECASE)
    text = re.sub(r'<img[^>]+src="([^"]*)"[^>]*/?\s*>', r'![](\1)', text, flags=re.IGNORECASE)

    # Code blocks
    text = re.sub(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", r"```\n\1\n```\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL)

    # Lists
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"</?[ou]l[^>]*>", "", text, flags=re.IGNORECASE)

    # Blockquotes
    text = re.sub(r"<blockquote[^>]*>(.*?)</blockquote>", lambda m: "> " + m.group(1).strip().replace("\n", "\n> ") + "\n", text, flags=re.IGNORECASE | re.DOTALL)

    # Paragraphs and line breaks
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)

    # Clean up extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def markdown_to_plain_text(path_or_text: str, is_path: bool = True) -> str:
    """Extrae texto plano sin markup."""
    if is_path:
        resolved = _resolve_path(path_or_text)
        raw = _read_file_text(resolved)
        _, body = _parse_frontmatter(raw)
    else:
        _, body = _parse_frontmatter(path_or_text)

    text = body
    text = re.sub(r"```[^\n]*\n([\s\S]*?)```", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
    text = re.sub(r"~~([^~]+)~~", r"\1", text)
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def yaml_to_json(path_or_text: str, is_path: bool = True) -> str:
    """Convierte YAML a JSON."""
    if is_path:
        resolved = _resolve_path(path_or_text)
        raw = _read_file_text(resolved)
    else:
        raw = path_or_text

    data = yaml.safe_load(raw)
    return json.dumps(data, ensure_ascii=False, indent=2)


def json_to_yaml(path_or_text: str, is_path: bool = True) -> str:
    """Convierte JSON a YAML."""
    if is_path:
        resolved = _resolve_path(path_or_text)
        raw = _read_file_text(resolved)
    else:
        raw = path_or_text

    data = json.loads(raw)
    return yaml.dump(data, ensure_ascii=False, default_flow_style=False, sort_keys=False)


def xml_to_yaml(path_or_text: str, is_path: bool = True) -> str:
    """Convierte XML a YAML."""
    if is_path:
        resolved = _resolve_path(path_or_text)
        raw = _read_file_text(resolved)
    else:
        raw = path_or_text

    data = xmltodict.parse(raw)
    return yaml.dump(data, ensure_ascii=False, default_flow_style=False, sort_keys=False)


def merge_documents(files: list[str], separator: str = "\n\n---\n\n") -> str:
    """Combina múltiples archivos en uno solo."""
    parts: list[str] = []
    for f in files:
        resolved = _resolve_path(f)
        content = _read_file_text(resolved)
        parts.append(content)
    return separator.join(parts)
