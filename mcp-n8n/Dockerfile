# =============================================================================
# mcp-n8n — Multi-stage Dockerfile (non-root, production-ready)
# =============================================================================

FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

COPY mcp-n8n/pyproject.toml ./
COPY shared /workspace/shared

RUN mkdir -p src/mcp_n8n

RUN uv pip install --system --no-cache \
    "fastmcp>=2.3" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "rich>=13.7" \
    "httpx>=0.27"

RUN uv pip install --system --no-cache /workspace/shared

# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="mcp-n8n" \
      org.opencontainers.image.description="MCP server for n8n: workflows, webhooks, executions" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

RUN groupadd --gid 1001 mcpgroup && \
    useradd --uid 1001 --gid mcpgroup --shell /bin/bash --create-home mcpuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

COPY --chown=mcpuser:mcpgroup mcp-n8n/src/ ./src/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_SERVER_NAME=mcp-n8n \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8039

USER mcpuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python -c "import mcp_n8n; print('ok')" || exit 1

CMD ["python", "-m", "mcp_n8n.server"]
