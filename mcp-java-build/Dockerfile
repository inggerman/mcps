# =============================================================================
# mcp-java-build — Dockerfile
# =============================================================================

FROM python:3.12-slim AS builder

WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY mcp-java-build/pyproject.toml ./
COPY mcp-java-build/src/ ./src/
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
      description="MCP server for Java Build tools"

WORKDIR /app

# Install Java, Maven, Gradle
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-21-jdk-headless maven gradle \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY mcp-java-build/src/ ./src/

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
    JAVA_PROJECT_PATH=/repo

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python -c "import mcp_java_build; print('ok')" || exit 1

CMD ["python", "-m", "mcp_java_build.server"]
