FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY shared /workspace/shared
COPY mcp-browser/pyproject.toml ./
COPY mcp-browser/src ./src
RUN uv pip install --system --no-cache /workspace/shared . && playwright install --with-deps chromium
RUN useradd --system --uid 1001 --no-create-home mcpuser && mkdir -p /data/browser \
    && chown -R mcpuser:mcpuser /app /data/browser
USER mcpuser
ENV PYTHONPATH=/app/src BROWSER_HEADLESS=true BROWSER_OUTPUT_DIR=/data/browser MCP_PORT=8000
CMD ["python", "-m", "mcp_browser.server"]
