# =============================================================================
# mcp-calendar — Multi-stage Dockerfile (non-root, production-ready)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder — instala dependencias con uv
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Instalar uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

# Copiar archivos de dependencias primero (mejor caché de capas)
COPY pyproject.toml ./
# Copiar el paquete shared desde el workspace
COPY ../shared /workspace/shared

# Crear directorio src vacío para que hatchling no falle
RUN mkdir -p src/mcp_calendar

# Instalar dependencias en el entorno del sistema (sin virtualenv para prod)
RUN uv pip install --system --no-cache \
    mcp[cli]>=1.9 \
    holidays>=0.52 \
    python-dateutil>=2.9 \
    pytz>=2024.1 \
    tzdata>=2024.1 \
    httpx>=0.27 \
    pydantic>=2.7 \
    pydantic-settings>=2.3 \
    structlog>=24.1 \
    rich>=13.7

# Instalar mcp-shared desde fuente local
RUN uv pip install --system --no-cache /workspace/shared

# ---------------------------------------------------------------------------
# Stage 2: runtime — imagen final mínima y non-root
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Metadatos OCI
LABEL org.opencontainers.image.title="mcp-calendar" \
      org.opencontainers.image.description="MCP server for business days and currency exchange rates" \
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
COPY --chown=mcpuser:mcpgroup src/ ./src/

# Variables de entorno de producción por defecto
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_SERVER_NAME=mcp-calendar

# Cambiar al usuario no-root
USER mcpuser

# El servidor MCP se comunica vía stdio (no expone puerto HTTP por defecto)
ENTRYPOINT ["python", "-m", "mcp_calendar.server"]
