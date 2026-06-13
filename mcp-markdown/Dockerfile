FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

COPY mcp-markdown/pyproject.toml ./
COPY shared /workspace/shared

RUN uv pip install --system --no-cache \
    "fastmcp>=2.3" \
    "mistune>=3.0" \
    "python-frontmatter>=1.1" \
    "mdformat>=0.7" \
    "markdown>=3.6" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "rich>=13.7" && \
    uv pip install --system --no-cache /workspace/shared

FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="mcp-markdown" \
      org.opencontainers.image.description="MCP server for Markdown files" \
      org.opencontainers.image.version="1.0.0"

RUN groupadd --gid 1001 mcpgroup && \
    useradd --uid 1001 --gid mcpgroup --shell /bin/bash --create-home mcpuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app
COPY --chown=mcpuser:mcpgroup mcp-markdown/src/ ./src/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_SERVER_NAME=mcp-markdown \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8003

USER mcpuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import mcp_markdown; print('ok')" || exit 1

CMD ["python", "-m", "mcp_markdown.server"]
