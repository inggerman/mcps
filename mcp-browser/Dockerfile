FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY shared /workspace/shared
COPY mcp-browser/pyproject.toml ./
COPY mcp-browser/src ./src
RUN uv pip install --system --no-cache --no-sources /workspace/shared . \
    && playwright install --with-deps chromium
RUN useradd --system --uid 1001 --no-create-home mcpuser && mkdir -p /data/browser \
    && cp -r /root/.cache/ms-playwright /home/mcpuser/.cache/ms-playwright 2>/dev/null || true \
    && mkdir -p /home/mcpuser/.cache && cp -r /root/.cache/ms-playwright /home/mcpuser/.cache/ 2>/dev/null || true \
    && chown -R mcpuser:mcpuser /app /data/browser /home/mcpuser
ENV PLAYWRIGHT_BROWSERS_PATH=/home/mcpuser/.cache/ms-playwright
USER mcpuser
ENV PYTHONPATH=/app/src BROWSER_HEADLESS=true BROWSER_OUTPUT_DIR=/data/browser MCP_PORT=8000
CMD ["python", "-m", "mcp_browser.server"]
