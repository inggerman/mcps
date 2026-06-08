# =============================================================================
# mcp-prompt-engineer — Multi-stage Dockerfile (non-root)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder — installs dependencies with uv
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install uv
RUN pip install --no-cache-dir uv

# Copy workspace root pyproject.toml and shared package first (for caching)
COPY ../pyproject.toml /workspace/pyproject.toml
COPY ../shared /workspace/shared

# Copy this server's source
COPY . /workspace/mcp-prompt-engineer

WORKDIR /workspace

# Install all dependencies into the system Python (no venv needed in Docker)
RUN uv pip install --system --no-cache \
    "mcp[cli]>=1.9" \
    "tiktoken>=0.7" \
    "langdetect>=1.0.9" \
    "jinja2>=3.1" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "rich>=13.7"

# Install mcp-shared in editable mode
RUN uv pip install --system --no-cache /workspace/shared

# Install this package
RUN uv pip install --system --no-cache /workspace/mcp-prompt-engineer

# ---------------------------------------------------------------------------
# Stage 2: runtime — minimal image with non-root user
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

LABEL maintainer="mcp-framework" \
      version="1.0.0" \
      description="MCP Prompt Engineer — analyzes and improves LLM prompts"

# Create a non-root user
RUN groupadd --gid 1001 mcp && \
    useradd --uid 1001 --gid mcp --shell /bin/bash --create-home mcp

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory owned by the non-root user
WORKDIR /app
RUN chown mcp:mcp /app

USER mcp

# Environment defaults
ENV LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check: import the package
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import mcp_prompt_engineer; print('ok')"

# MCP servers communicate over stdio by default
ENTRYPOINT ["python", "-m", "mcp_prompt_engineer.server"]
