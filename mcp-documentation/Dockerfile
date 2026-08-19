FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

COPY mcp-documentation/pyproject.toml ./
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
    "rich>=13.7" \
    "pyyaml>=6.0" \
    "xmltodict>=0.13" \
    "pypdf>=4.0" \
    "python-docx>=1.1" && \
    uv pip install --system --no-cache /workspace/shared

FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="mcp-documentation" \
      org.opencontainers.image.description="MCP server for documentation management" \
      org.opencontainers.image.version="1.0.0"

RUN groupadd --gid 1001 mcpgroup && \
    useradd --uid 1001 --gid mcpgroup --shell /bin/bash --create-home mcpuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app
COPY --chown=mcpuser:mcpgroup mcp-documentation/src/ ./src/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_SERVER_NAME=mcp-documentation \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8055 \
    DOC_ROOT_PATH=/data/mcp-doc

USER mcpuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import mcp_documentation; print('ok')" || exit 1

CMD ["python", "-m", "mcp_documentation.server"]
