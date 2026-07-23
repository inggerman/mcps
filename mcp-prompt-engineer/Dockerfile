FROM python:3.11-slim AS builder
WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY shared /workspace/shared
COPY mcp-prompt-engineer/pyproject.toml ./
COPY mcp-prompt-engineer/src ./src
RUN uv pip install --system --no-cache --no-sources /workspace/shared .

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY mcp-prompt-engineer/src ./src
RUN groupadd --gid 1001 mcp && \
    useradd --uid 1001 --gid mcp --shell /bin/bash --create-home mcp && \
    chown -R mcp:mcp /app
USER mcp
ENV PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8000
ENTRYPOINT ["python", "-m", "mcp_prompt_engineer.server"]
