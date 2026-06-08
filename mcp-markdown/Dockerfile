# =============================================================================
# mcp-markdown — Multi-stage Dockerfile (production-grade, non-root)
# =============================================================================
# Stage 1: builder  — instala dependencias con uv en un entorno aislado
# Stage 2: runtime  — imagen mínima sin herramientas de compilación
# =============================================================================

# ---- Stage 1: builder -------------------------------------------------------
FROM python:3.11-slim AS builder

# Instalar uv (gestor de paquetes rápido)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Variables de entorno para uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar solo los archivos de dependencias primero (cache layer)
COPY pyproject.toml ./

# Copiar el paquete compartido (workspace)
COPY ../shared ./shared

# Instalar dependencias sin el propio paquete (para cache eficiente)
RUN uv sync --no-install-project --no-dev

# Copiar el código fuente
COPY src/ ./src/

# Instalar el paquete completo
RUN uv sync --no-dev


# ---- Stage 2: runtime -------------------------------------------------------
FROM python:3.11-slim AS runtime

# Metadatos OCI
LABEL org.opencontainers.image.title="mcp-markdown" \
      org.opencontainers.image.description="MCP server for reading and processing Markdown files" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.source="https://github.com/example/mcp-framework"

# Variables de entorno de producción
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    MCP_MARKDOWN_LOG_FORMAT=json \
    MCP_MARKDOWN_LOG_LEVEL=INFO

# Crear usuario no-root para seguridad
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copiar el entorno virtual y el código desde el builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/src /app/src

# Crear directorio de datos con permisos correctos
RUN mkdir -p /data && chown appuser:appgroup /data

# Cambiar al usuario no-root
USER appuser

# Healthcheck: verificar que el módulo es importable
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import mcp_markdown; print('ok')" || exit 1

# Ejecutar el servidor MCP via stdio (protocolo MCP estándar)
CMD ["python", "-m", "mcp_markdown.server"]
