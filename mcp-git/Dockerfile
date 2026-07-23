# =============================================================================
# mcp-git — Dockerfile multi-stage, non-root, production-ready
# =============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY mcp-git/pyproject.toml ./
COPY mcp-git/src/ ./src/
COPY shared /workspace/shared

RUN uv pip install --system --no-cache /workspace/shared && \
    uv pip install --system --no-cache \
    "fastmcp>=2.3" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "rich>=13.7"

FROM python:3.12-slim AS runtime

LABEL maintainer="MCP Framework Team" \
      version="1.0.0" \
      description="MCP server for local Git operations with strict commit confirmations"

WORKDIR /app

# Instalar Git
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY mcp-git/src/ ./src/

RUN useradd --system --uid 1001 --shell /bin/false --no-create-home mcpuser \
    && chown -R mcpuser:mcpuser /app

# Consideración: Para mcp-git, puede que queramos correr como root o usar
# un volumen montado si el repositorio pertenece a otro usuario en host,
# pero git tiene config safe.directory que podemos setear:
RUN git config --global --add safe.directory '*'

USER mcpuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8000 \
    GIT_REPO_PATH=/repo \
    GIT_DEFAULT_BRANCH=main \
    GIT_ALLOW_FORCE_PUSH=false

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python -c "import mcp_git; print('ok')" || exit 1

CMD ["python", "-m", "mcp_git.server"]
