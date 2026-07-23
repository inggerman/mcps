# =============================================================================
# mcp-tabular — Dockerfile multi-stage, non-root, production-ready
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Builder — instala dependencias con uv
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Instalar uv usando la imagen oficial (más rápido y siempre actualizado)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar archivos de definición del proyecto
COPY mcp-tabular/pyproject.toml ./

# Copiar el código fuente (necesario para instalación editable con hatchling)
COPY mcp-tabular/src/ ./src/
COPY shared /workspace/shared

# Instalar todas las dependencias del proyecto al directorio de sistema
# --no-cache: evita almacenar caché de pip en la imagen
# --system: instala en el Python del sistema, no en un venv
RUN uv pip install --system --no-cache /workspace/shared && \
    uv pip install --system --no-cache \
    "fastmcp>=2.3" \
    "pandas>=2.2" \
    "openpyxl>=3.1" \
    "xlrd>=2.0" \
    "odfpy>=1.4" \
    "chardet>=5.2" \
    "pyarrow>=16.0" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.3" \
    "structlog>=24.1" \
    "rich>=13.7"

# ---------------------------------------------------------------------------
# Stage 2: Runtime — imagen mínima de producción
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

LABEL maintainer="MCP Framework Team" \
      version="1.0.0" \
      description="MCP server for reading tabular files (Excel, CSV, ODS, TSV)"

WORKDIR /app

# Copiar librerías Python instaladas desde el builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar el código fuente del servidor
COPY mcp-tabular/src/ ./src/

# Crear usuario no-root para mayor seguridad en producción
RUN useradd --system --uid 1001 --shell /bin/false --no-create-home mcpuser \
    && chown -R mcpuser:mcpuser /app

# Cambiar al usuario no-root
USER mcpuser

# Variables de entorno por defecto (sobreescribibles vía docker-compose o --env)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO \
    LOG_FORMAT=json \
    MCP_TRANSPORT=stdio \
    MCP_PORT=8000

# Health check: verifica que el módulo se puede importar correctamente
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD python -c "import mcp_tabular; print('ok')" || exit 1

# Punto de entrada: ejecutar el servidor MCP en modo stdio (para Claude Desktop)
CMD ["python", "-m", "mcp_tabular.server"]
