FROM python:3.12-slim AS builder
WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY shared /workspace/shared
COPY mcp-documents/pyproject.toml ./
COPY mcp-documents/src ./src
RUN uv pip install --system --no-cache --no-sources /workspace/shared .

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY mcp-documents/src ./src
RUN useradd --system --uid 1001 --no-create-home mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser
ENV PYTHONPATH=/app/src DOCUMENTS_ROOT=/data MCP_PORT=8000
CMD ["python", "-m", "mcp_documents.server"]
