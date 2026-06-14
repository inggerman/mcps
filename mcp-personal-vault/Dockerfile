FROM python:3.12-slim AS builder
WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY shared /workspace/shared
COPY mcp-personal-vault/pyproject.toml ./
COPY mcp-personal-vault/src ./src
RUN uv pip install --system --no-cache /workspace/shared .

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY mcp-personal-vault/src ./src
RUN useradd --system --uid 1001 --create-home mcpuser \
    && mkdir -p /vault \
    && chown -R mcpuser:mcpuser /app /vault
USER mcpuser
ENV PYTHONPATH=/app/src \
    PERSONAL_VAULT_DATABASE_PATH=/vault/personal.db \
    PERSONAL_VAULT_KEY_FILE=/vault/vault.key \
    PERSONAL_VAULT_ALLOW_WRITE=false \
    PERSONAL_VAULT_ALLOW_HIGHLY_SENSITIVE=false \
    MCP_PORT=8035
CMD ["python", "-m", "mcp_personal_vault.server"]
