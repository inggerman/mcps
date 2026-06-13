"""
Fixtures compartidos para los tests de mcp-markdown.

Provee archivos Markdown temporales con distintos contenidos
para probar todas las herramientas del servidor.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Contenidos de muestra
# ---------------------------------------------------------------------------

SIMPLE_MD = """\
---
title: Test Document
author: Test Author
tags: [python, mcp, markdown]
---

# Hello World

This is a **simple** test document with _italic_ text.

## Section One

Some content here with a [link to Python](https://python.org) and
an [internal link](./other.md).

### Subsection

More content.

## Section Two

A code example:

```python
def hello(name: str) -> str:
    return f"Hello, {name}!"
```

And some inline `code`.

![Logo](https://example.com/logo.png "Example Logo")
"""

DUPLICATE_HEADINGS_MD = """\
# Title

## Overview

Content here.

## Overview

More content.

# Title
"""

BROKEN_LINKS_MD = """\
# Document with broken links

See [existing file](README.md) and [missing file](does_not_exist.md).

Also check [another missing](subdir/nope.md).
"""

EMPTY_MD = """\
# Empty Document

No frontmatter here.
"""

CODE_BLOCKS_MD = """\
# Code Examples

```python
x = 1
y = 2
print(x + y)
```

```javascript
const greet = (name) => `Hello, ${name}!`;
```

```
No language declared.
```
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_md_file(tmp_path: pytest.TempPathFactory) -> str:
    """Archivo Markdown simple con frontmatter y múltiples secciones."""
    p = tmp_path / "simple.md"
    p.write_text(SIMPLE_MD, encoding="utf-8")
    return str(p)


@pytest.fixture
def duplicate_headings_file(tmp_path: pytest.TempPathFactory) -> str:
    """Archivo Markdown con encabezados duplicados."""
    p = tmp_path / "duplicates.md"
    p.write_text(DUPLICATE_HEADINGS_MD, encoding="utf-8")
    return str(p)


@pytest.fixture
def broken_links_file(tmp_path: pytest.TempPathFactory) -> str:
    """Archivo Markdown con un enlace local roto."""
    p = tmp_path / "broken.md"
    p.write_text(BROKEN_LINKS_MD, encoding="utf-8")
    return str(p)


@pytest.fixture
def empty_md_file(tmp_path: pytest.TempPathFactory) -> str:
    """Archivo Markdown mínimo sin frontmatter."""
    p = tmp_path / "empty.md"
    p.write_text(EMPTY_MD, encoding="utf-8")
    return str(p)


@pytest.fixture
def code_blocks_file(tmp_path: pytest.TempPathFactory) -> str:
    """Archivo Markdown con varios bloques de código."""
    p = tmp_path / "code.md"
    p.write_text(CODE_BLOCKS_MD, encoding="utf-8")
    return str(p)


@pytest.fixture
def markdown_directory(tmp_path: pytest.TempPathFactory) -> str:
    """Directorio con varios archivos Markdown para list_markdown_files."""
    (tmp_path / "doc1.md").write_text("# Document One\n\nContent of doc one.", encoding="utf-8")
    (tmp_path / "doc2.md").write_text("# Document Two\n\nContent of doc two.", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.md").write_text("# Nested Document\n\nNested content.", encoding="utf-8")
    (tmp_path / "not_markdown.txt").write_text("Plain text file.", encoding="utf-8")
    return str(tmp_path)
