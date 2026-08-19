"""Fixtures compartidas para los tests de mcp-documentation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

SAMPLE_MD = """\
---
title: Test Document
type: feature
project: test-project
tags: [python, mcp, documentation]
timestamp: 2026-08-15T12:00:00-06:00
status: draft
author: tester
---

# Test Document

This is a **simple** test document with _italic_ text.

## Section One

Some content here with a [link to Python](https://python.org).

### Subsection

More content about the feature implementation.

## Section Two

A code example:

```python
def hello(name: str) -> str:
    return f"Hello, {name}!"
```
"""

SAMPLE_YAML = """\
name: test-config
version: 1.0.0
database:
  host: localhost
  port: 5432
"""

SAMPLE_JSON = """\
{"name": "test", "version": "1.0.0", "items": ["a", "b", "c"]}
"""

SAMPLE_XML = """\
<root>
  <name>test</name>
  <items>
    <item>a</item>
    <item>b</item>
  </items>
</root>
"""

SAMPLE_FIX_MD = """\
---
title: Bug Fix Report
type: fix
project: test-project
tags: [bug, fix]
timestamp: 2026-08-15T13:00:00-06:00
status: active
author: tester
---

# Fix: Critical Bug

## Problema

Se encontró un bug en el módulo de autenticación.

## Solución

Se aplicó un parche para corregir el error.
"""


@pytest.fixture
def tmp_root(tmp_path: Path) -> Path:
    """Directorio raíz temporal para tests de documentación."""
    return tmp_path


@pytest.fixture
def mock_settings(tmp_root: Path):
    """Mock settings con root_path temporal."""
    from mcp_documentation.config import DocumentationSettings

    settings = DocumentationSettings(
        root_path=tmp_root,
        index_path=tmp_root / ".index",
        max_file_size_mb=20,
        auto_classify=True,
    )
    with patch("mcp_documentation.config.settings", settings):
        with patch("mcp_documentation.tools.doc_read_tools.settings", settings):
            with patch("mcp_documentation.tools.doc_write_tools.settings", settings):
                with patch("mcp_documentation.tools.doc_transform_tools.settings", settings):
                    with patch("mcp_documentation.tools.doc_classify_tools.settings", settings):
                        with patch("mcp_documentation.tools.doc_index_tools.settings", settings):
                            with patch("mcp_documentation.tools.session_tools.settings", settings):
                                with patch("mcp_documentation.tools.diagram_tools.settings", settings):
                                    with patch("mcp_documentation.tools.investigation_tools.settings", settings):
                                        with patch("mcp_documentation.tools.versioning_tools.settings", settings):
                                            with patch("mcp_documentation.tools.health_tools.settings", settings):
                                                with patch("mcp_documentation.tools.backup_tools.settings", settings):
                                                    yield settings


@pytest.fixture
def sample_md_file(tmp_root: Path) -> str:
    """Archivo Markdown de muestra con frontmatter."""
    p = tmp_root / "feature" / "test-doc.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(SAMPLE_MD, encoding="utf-8")
    return str(p)


@pytest.fixture
def sample_fix_md_file(tmp_root: Path) -> str:
    """Archivo Markdown de fix."""
    p = tmp_root / "fix" / "bug-fix.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(SAMPLE_FIX_MD, encoding="utf-8")
    return str(p)


@pytest.fixture
def sample_yaml_file(tmp_root: Path) -> str:
    """Archivo YAML de muestra."""
    p = tmp_root / "config.yaml"
    p.write_text(SAMPLE_YAML, encoding="utf-8")
    return str(p)


@pytest.fixture
def sample_json_file(tmp_root: Path) -> str:
    """Archivo JSON de muestra."""
    p = tmp_root / "data.json"
    p.write_text(SAMPLE_JSON, encoding="utf-8")
    return str(p)


@pytest.fixture
def sample_xml_file(tmp_root: Path) -> str:
    """Archivo XML de muestra."""
    p = tmp_root / "data.xml"
    p.write_text(SAMPLE_XML, encoding="utf-8")
    return str(p)


@pytest.fixture
def doc_directory(tmp_root: Path) -> str:
    """Directorio con varios documentos."""
    (tmp_root / "feature").mkdir(exist_ok=True)
    (tmp_root / "fix").mkdir(exist_ok=True)
    (tmp_root / "bitacoras").mkdir(exist_ok=True)

    (tmp_root / "feature" / "doc1.md").write_text(
        '---\ntitle: Feature One\ntype: feature\ntags: [api]\ntimestamp: 2026-08-15T10:00:00-06:00\n---\n# Feature One\n\nContent.',
        encoding="utf-8",
    )
    (tmp_root / "fix" / "doc2.md").write_text(
        '---\ntitle: Fix One\ntype: fix\ntags: [bug]\ntimestamp: 2026-08-15T11:00:00-06:00\n---\n# Fix One\n\nBug fix content.',
        encoding="utf-8",
    )
    (tmp_root / "bitacoras" / "doc3.md").write_text(
        '---\ntitle: Bitacora One\ntype: bitacora\ntags: [session]\ntimestamp: 2026-08-15T12:00:00-06:00\n---\n# Bitacora\n\nSession log.',
        encoding="utf-8",
    )
    return str(tmp_root)
