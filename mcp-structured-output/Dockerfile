# =============================================================================
# mcp-structured-output — Multi-stage Dockerfile (non-root, production-ready)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder — instala dependencias con uv
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

# Copiar archivos de dependencias primero (mejor caché de capas)
COPY mcp-structured-output/pyproject.toml ./
# Copiar el paquete shared desde el workspace
COPY shared /workspace/shared

# Crear directorio src vacío para que hatchling no falle
RUN mkdir -p src/mcp_structured_output

# Instalar dependencias en el entorno del sistema (sin virtualenv para prod)
RUN uv pip install --system --no-cache \
    "fastmcp>=2.3" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "rich>=13.7" \
    "boto3>=1.34" \
    "openai>=1.30" \
    "jsonschema>=4.22"

# Instalar mcp-shared desde fuente local
RUN uv pip install --system --no-cache /workspace/shared

# ---------------------------------------------------------------------------
# Stage 2: runtime — imagen final mínima y non-root
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Metadatos OCI
LABEL org.opencontainers.image.title="mcp-structured-output" \
      org.opencontainers.image.description="MCP server for structured JSON output across LLM providers" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.licenses="MIT"

# Crear usuario no-root
RUN groupadd --gid 1001 mcpgroup && \
    useradd --uid 1001 --gid mcpgroup --shell /bin/bash --create-home mcpuser

# Copiar paquetes Python instalados desde builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# Copiar el código fuente del servidor
COPY --chown=mcpuser:mcpgroup mcp-structured-output/src/ ./src/

# Variables de entorno de producción por defecto
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_SERVER_NAME=mcp-structured-output \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8005 \
    MCP_SO_AWS_REGION=us-east-1

# Cambiar al usuario no-root
USER mcpuser

# Healthcheck: verifica que el módulo es importable
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python -c "import mcp_structured_output; print('ok')" || exit 1

# CMD permite sobreescribir el comando en docker-compose
CMD ["python", "-m", "mcp_structured_output.server"]
