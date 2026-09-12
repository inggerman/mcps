FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY shared /workspace/shared
COPY mcp-browser/pyproject.toml ./
COPY mcp-browser/src ./src
RUN useradd --system --uid 1001 --no-create-home mcpuser && mkdir -p /data/browser /home/mcpuser/.cache \
    && chown -R mcpuser:mcpuser /app /data/browser /home/mcpuser
ENV PLAYWRIGHT_BROWSERS_PATH=/home/mcpuser/.cache/ms-playwright
RUN uv pip install --system --no-cache --no-sources /workspace/shared . \
    && su mcpuser -s /bin/bash -c "playwright install --with-deps chromium" \
    && chown -R mcpuser:mcpuser /home/mcpuser
USER mcpuser
ENV PYTHONPATH=/app/src BROWSER_HEADLESS=true BROWSER_OUTPUT_DIR=/data/browser MCP_PORT=8000 PLAYWRIGHT_BROWSERS_PATH=/home/mcpuser/.cache/ms-playwright
CMD ["python", "-m", "mcp_browser.server"]
