FROM python:3.12-slim AS builder
WORKDIR /build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY shared /workspace/shared
COPY mcp-terraform/pyproject.toml ./
COPY mcp-terraform/src ./src
RUN uv pip install --system --no-cache /workspace/shared .

FROM hashicorp/terraform:1.11 AS terraform
FROM python:3.12-slim
WORKDIR /app
COPY --from=terraform /bin/terraform /usr/local/bin/terraform
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY mcp-terraform/src ./src
RUN useradd --system --uid 1001 --no-create-home mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser
ENV PYTHONPATH=/app/src TERRAFORM_ROOT=/workspace TERRAFORM_ALLOW_APPLY=false MCP_PORT=8000
CMD ["python", "-m", "mcp_terraform.server"]
