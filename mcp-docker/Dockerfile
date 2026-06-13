# =============================================================================
# mcp-docker — Multi-stage Dockerfile (non-root, production-ready)
# Nota: para acceder al daemon Docker local se debe montar el socket:
#   docker run -v /var/run/docker.sock:/var/run/docker.sock mcp-docker
# =============================================================================

FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

COPY mcp-docker/pyproject.toml ./
COPY shared /workspace/shared

RUN mkdir -p src/mcp_docker

RUN uv pip install --system --no-cache \
    "fastmcp>=2.3" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "rich>=13.7" \
    "docker>=7.0" && \
    uv pip install --system --no-cache /workspace/shared

# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL org.opencontainers.image.title="mcp-docker" \
      org.opencontainers.image.description="MCP server for Docker management: containers, images, networks, volumes" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

RUN groupadd --gid 1001 mcpgroup && \
    useradd --uid 1001 --gid mcpgroup --shell /bin/bash --create-home mcpuser && \
    groupadd --gid 999 docker 2>/dev/null || true && \
    usermod -aG docker mcpuser 2>/dev/null || true

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

COPY --chown=mcpuser:mcpgroup mcp-docker/src/ ./src/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_SERVER_NAME=mcp-docker \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8007

USER mcpuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python -c "import mcp_docker; print('ok')" || exit 1

CMD ["python", "-m", "mcp_docker.server"]
