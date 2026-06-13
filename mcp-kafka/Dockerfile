# =============================================================================
# mcp-kafka — Multi-stage Dockerfile (non-root, production-ready)
# Nota: confluent-kafka requiere librdkafka. Usa python:3.12-slim que incluye
# gcc para compilar extensiones C si es necesario.
# =============================================================================

FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

COPY mcp-kafka/pyproject.toml ./
COPY shared /workspace/shared

RUN mkdir -p src/mcp_kafka

RUN uv pip install --system --no-cache \
    "fastmcp>=2.3" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "rich>=13.7" \
    "confluent-kafka>=2.5" && \
    uv pip install --system --no-cache /workspace/shared

# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    librdkafka1 \
    && rm -rf /var/lib/apt/lists/*

LABEL org.opencontainers.image.title="mcp-kafka" \
      org.opencontainers.image.description="MCP server for Apache Kafka: topics, consumer groups, produce and consume" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

RUN groupadd --gid 1001 mcpgroup && \
    useradd --uid 1001 --gid mcpgroup --shell /bin/bash --create-home mcpuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

COPY --chown=mcpuser:mcpgroup mcp-kafka/src/ ./src/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_SERVER_NAME=mcp-kafka \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8008 \
    MCP_KAFKA_BOOTSTRAP_SERVERS=localhost:9092

USER mcpuser

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python -c "import mcp_kafka; print('ok')" || exit 1

CMD ["python", "-m", "mcp_kafka.server"]
