# =============================================================================
# mcp-gob-mexico — Dockerfile multi-stage, non-root, production-ready
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder — instala dependencias con uv
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Instalar uv usando la imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar archivos de definición del proyecto
COPY mcp-gob-mexico/pyproject.toml ./

# Copiar el codigo fuente (necesario para instalacion editable con hatchling)
COPY mcp-gob-mexico/src/ ./src/
COPY shared /workspace/shared

# Instalar todas las dependencias del proyecto al directorio de sistema
RUN uv pip install --system --no-cache /workspace/shared && \
    uv pip install --system --no-cache \
    "fastmcp>=2.3" \
    "httpx>=0.27" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "rich>=13.7"

# ---------------------------------------------------------------------------
# Stage 2: Runtime — imagen minima de produccion
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL maintainer="MCP Framework Team" \
      version="1.0.0" \
      description="MCP server for Mexican government APIs (INEGI, Banxico, SAT, etc.)"

WORKDIR /app

# Copiar librerias Python instaladas desde el builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar el codigo fuente del servidor
COPY mcp-gob-mexico/src/ ./src/

# Crear usuario no-root para mayor seguridad en produccion
RUN useradd --system --uid 1001 --shell /bin/false --no-create-home mcpuser \
    && chown -R mcpuser:mcpuser /app

# Cambiar al usuario no-root
USER mcpuser

# Variables de entorno por defecto (sobreescribibles via docker-compose o --env)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_TRANSPORT=streamable-http \
    MCP_PORT=8035 \
    GOB_MX_HTTP_TIMEOUT=30 \
    GOB_MX_MAX_RETRIES=3 \
    GOB_MX_CACHE_TTL=300

# Health check: verifica que el servidor HTTP responde en el puerto configurado
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8035/health', timeout=5)" || exit 1

# Punto de entrada: ejecutar el servidor MCP
CMD ["python", "-m", "mcp_gob_mexico.server"]
