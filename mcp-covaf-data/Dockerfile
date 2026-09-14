# =============================================================================
# mcp-covaf-data — Dockerfile
# =============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY mcp-covaf-data/pyproject.toml ./mcp-covaf-data/
COPY mcp-covaf-data/src/ ./mcp-covaf-data/src/
COPY shared /workspace/shared

RUN uv pip install --system --no-cache /workspace/shared && \
    uv pip install --system --no-cache \
    "fastmcp>=2.3" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "httpx>=0.27" \
    "rich>=13.7" \
    "defusedxml>=0.7"

FROM python:3.12-slim AS runtime

LABEL maintainer="COVAF Agent Team" \
      version="1.0.0" \
      description="MCP server for COVAF data formats (PDF, Excel, Word, XML, JSON, JSON-PDF, JSON-Word, XML-Short)"

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY mcp-covaf-data/src/ ./src/

RUN useradd --system --uid 1001 --shell /bin/false --no-create-home mcpuser \
    && chown -R mcpuser:mcpuser /app

USER mcpuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_TRANSPORT=streamable-http \
    MCP_PORT=8000 \
    COVAF_WORKSPACE_PATH=/workspace

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python -c "import mcp_covaf_data; print('ok')" || exit 1

CMD ["python", "-m", "mcp_covaf_data.server"]
