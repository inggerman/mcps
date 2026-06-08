# mcp-markdown

> MCP server for reading, analyzing, transforming, and validating Markdown files.

Part of the **MCP Framework** — a collection of specialized MCP servers sharing a common
workspace, tooling, and conventions.

---

## Features

| Tool | Description |
|------|-------------|
| `read_markdown` | Full analysis: frontmatter, title, word count, headings, links, code blocks, images |
| `extract_headings` | List of H1–H6 headings with level, text, and HTML anchor |
| `extract_links` | All links (internal, external, images) with metadata |
| `extract_code_blocks` | Fenced code blocks with language and content |
| `get_toc` | Generate a Markdown table of contents with anchor links |
| `markdown_to_html` | Convert to full HTML5 document with embedded styles |
| `markdown_to_plain_text` | Strip all Markdown markup → clean plain text |
| `validate_markdown` | Detect missing H1, duplicate headings, broken local links |
| `search_in_markdown` | Full-text search with line number and heading context |
| `format_markdown` | Normalize formatting with [mdformat](https://mdformat.readthedocs.io/) |
| `get_frontmatter` | Extract only the YAML frontmatter metadata |
| `list_markdown_files` | Inventory of Markdown files in a directory |

---

## Installation

This server is part of the `mcps` uv workspace. From the workspace root:

```bash
uv sync --all-packages
```

### Standalone install

```bash
cd mcp-markdown
uv sync
```

---

## Usage

### Running locally (stdio — for Claude Desktop)

```bash
uv run python -m mcp_markdown.server
```

Or via the workspace Makefile:

```bash
make dev-mcp-markdown
```

### MCP Inspector

```bash
make inspect SERVER=mcp-markdown
```

---

## Configuration

Environment variables (prefix `MCP_MARKDOWN_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_MARKDOWN_LOG_LEVEL` | `INFO` | `DEBUG \| INFO \| WARNING \| ERROR` |
| `MCP_MARKDOWN_LOG_FORMAT` | `json` | `json` (prod) \| `console` (dev) |
| `MCP_MARKDOWN_MAX_FILE_SIZE_MB` | `10.0` | Max file size in MB |
| `MCP_MARKDOWN_DEFAULT_MAX_TOC_DEPTH` | `3` | Default ToC depth (1–6) |
| `MCP_MARKDOWN_VALIDATE_EXTERNAL_LINKS` | `false` | Validate external URLs (requires network) |

For Claude Desktop, set in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-markdown": {
      "command": "uv",
      "args": [
        "--directory", "C:/Users/germa/Documents/IA/mcps/mcp-markdown",
        "run", "python", "-m", "mcp_markdown.server"
      ],
      "env": {
        "MCP_MARKDOWN_LOG_LEVEL": "INFO",
        "MCP_MARKDOWN_LOG_FORMAT": "console"
      }
    }
  }
}
```

---

## Tool Examples

### `read_markdown`

```json
{
  "tool": "read_markdown",
  "arguments": { "path": "/docs/README.md" }
}
```

Response:
```json
{
  "content": "---\ntitle: My Doc\n---\n# My Doc\n\nHello world.",
  "frontmatter": { "title": "My Doc" },
  "title": "My Doc",
  "word_count": 2,
  "headings": [{ "level": 1, "text": "My Doc", "anchor": "my-doc" }],
  "links": [],
  "code_blocks": [],
  "images": []
}
```

---

### `extract_headings`

```json
{
  "tool": "extract_headings",
  "arguments": { "path": "/docs/guide.md" }
}
```

Response:
```json
[
  { "level": 1, "text": "Getting Started", "anchor": "getting-started" },
  { "level": 2, "text": "Installation", "anchor": "installation" },
  { "level": 2, "text": "Configuration", "anchor": "configuration" }
]
```

---

### `get_toc`

```json
{
  "tool": "get_toc",
  "arguments": { "path": "/docs/guide.md", "max_depth": 2 }
}
```

Response:
```markdown
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Configuration](#configuration)
```

---

### `validate_markdown`

```json
{
  "tool": "validate_markdown",
  "arguments": { "path": "/docs/guide.md" }
}
```

Response:
```json
{
  "valid": false,
  "warnings": ["Enlace local roto: 'setup.md'"],
  "broken_links": [{ "text": "Setup", "url": "setup.md", "resolved_path": "/docs/setup.md" }],
  "duplicate_headings": []
}
```

---

### `search_in_markdown`

```json
{
  "tool": "search_in_markdown",
  "arguments": { "path": "/docs/guide.md", "query": "installation", "case_sensitive": false }
}
```

Response:
```json
[
  {
    "line_number": 12,
    "context": "## Installation",
    "heading_context": null
  },
  {
    "line_number": 14,
    "context": "Run the installation script:",
    "heading_context": "Installation"
  }
]
```

---

### `markdown_to_html` (direct text)

```json
{
  "tool": "markdown_to_html",
  "arguments": {
    "path_or_text": "# Hello\n\nThis is **bold**.",
    "is_path": false
  }
}
```

---

### `list_markdown_files`

```json
{
  "tool": "list_markdown_files",
  "arguments": { "directory": "/docs", "recursive": true }
}
```

Response:
```json
[
  {
    "path": "/docs/index.md",
    "relative_path": "index.md",
    "title": "Home",
    "word_count": 120,
    "size_bytes": 4096,
    "frontmatter": { "title": "Home", "date": "2024-01-01" }
  }
]
```

---

## Docker

Build and run with Docker Compose (from the workspace root):

```bash
docker compose build mcp-markdown
docker compose up mcp-markdown
```

---

## Testing

```bash
# From the workspace root
make test-mcp-markdown

# Or directly
cd mcp-markdown
uv run pytest -v
uv run pytest --cov=src --cov-report=term-missing
```

---

## Supported Markdown Extensions

`.md` · `.markdown` · `.mdx` · `.mdown` · `.mkd`

---

## Dependencies

| Package | Purpose |
|---------|---------|
| [`mistune`](https://mistune.lepture.com/) ≥ 3.0 | Markdown parser / AST builder |
| [`python-frontmatter`](https://python-frontmatter.readthedocs.io/) ≥ 1.1 | YAML frontmatter extraction |
| [`mdformat`](https://mdformat.readthedocs.io/) ≥ 0.7 | Markdown formatter / normalizer |
| [`mcp[cli]`](https://github.com/modelcontextprotocol/python-sdk) ≥ 1.9 | MCP server framework (FastMCP) |
| [`pydantic-settings`](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) ≥ 2.3 | Configuration from env vars |
| [`structlog`](https://www.structlog.org/) ≥ 24.1 | Structured logging |

---

## Architecture

```
mcp-markdown/
├── pyproject.toml              # Project metadata & dependencies
├── Dockerfile                  # Multi-stage, non-root, production build
├── src/
│   └── mcp_markdown/
│       ├── __init__.py
│       ├── config.py           # pydantic-settings configuration
│       ├── server.py           # FastMCP server with all tool registrations
│       └── tools/
│           ├── __init__.py
│           └── markdown_tools.py   # All 12 tool implementations
└── tests/
    ├── conftest.py             # Shared fixtures (temp Markdown files)
    ├── test_config.py          # Settings tests
    ├── test_server.py          # Server registration tests
    └── test_markdown_tools.py  # Full tool test suite
```
