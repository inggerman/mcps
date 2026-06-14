FROM python:3.12-slim AS builder
WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY shared /workspace/shared
COPY mcp-database/pyproject.toml ./
COPY mcp-database/src ./src
RUN uv pip install --system --no-cache /workspace/shared . psycopg[binary] pymysql

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY mcp-database/src ./src
RUN useradd --system --uid 1001 --no-create-home mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser
ENV PYTHONPATH=/app/src MCP_TRANSPORT=stdio MCP_PORT=8000 DATABASE_READ_ONLY=true
CMD ["python", "-m", "mcp_database.server"]
