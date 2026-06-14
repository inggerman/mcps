# =============================================================================
# mcp-llm-router — Dockerfile multi-stage, non-root, production-ready
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY mcp-llm-router/pyproject.toml ./
COPY mcp-llm-router/src/ ./src/
COPY shared /workspace/shared

RUN uv pip install --system --no-cache /workspace/shared && \
    uv pip install --system --no-cache \
    "fastmcp>=2.3" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "rich>=13.7" \
    "httpx>=0.27"

# ---------------------------------------------------------------------------
# Stage 2: Runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL maintainer="MCP Framework Team" \
      version="1.0.0" \
      description="MCP server for intelligent routing between local (LM Studio) and cloud AI models"

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY mcp-llm-router/src/ ./src/

RUN useradd --system --uid 1001 --shell /bin/false --no-create-home mcpuser \
    && mkdir -p /app/.ai-memory \
    && chown -R mcpuser:mcpuser /app

USER mcpuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8000 \
    ROUTER_LMSTUDIO_BASE_URL=http://host.docker.internal:1234/v1 \
    ROUTER_COMPLEXITY_THRESHOLD=6 \
    ROUTER_MODEL_FAST=qwen3-8b \
    ROUTER_MODEL_CODE=devstral-small-2507 \
    ROUTER_MODEL_REASON=deepseek-r1-0528-qwen3-8b \
    ROUTER_MODEL_LARGE=qwen2.5-14b-instruct-1m

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python -c "import mcp_llm_router; print('ok')" || exit 1

CMD ["python", "-m", "mcp_llm_router.server"]
