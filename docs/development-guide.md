# Guía de Desarrollo

---

## Setup del entorno (primera vez)

```powershell
# 1. Instalar uv (gestor de paquetes)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Verificar: uv --version

# 2. Clonar e instalar el workspace
git clone <repo>
cd mcps
uv sync --all-packages           # instala todas las dependencias
uv sync --all-packages --all-extras  # + dev tools (pytest, ruff, mypy)
uv run pre-commit install        # hooks de git

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env si necesitas cambiar valores

# 4. Verificar que todo funciona
make status     # verifica herramientas instaladas
make test-fast  # tests rápidos
```

---

## Comandos del día a día

```bash
make dev-mcp-tabular         # iniciar servidor con hot-reload
make inspect SERVER=mcp-calendar  # abrir MCP Inspector web en localhost:5173
make test                    # todos los tests con coverage
make test-mcp-prompt-engineer # tests de un servidor específico
make lint                    # ruff + mypy
make format                  # formatear código automáticamente
```

---

## Crear un nuevo servidor MCP — Checklist

Sigue estos pasos **en orden**. El ejemplo usa `mcp-database`.

### 1. Estructura de archivos

```
mcp-database/
├── src/mcp_database/
│   ├── __init__.py
│   ├── config.py
│   ├── server.py
│   └── tools/
│       ├── __init__.py
│       └── database_tools.py
├── tests/
│   └── test_server.py
├── Dockerfile
└── pyproject.toml
```

### 2. `pyproject.toml`

```toml
[project]
name = "mcp-database"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.3",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "structlog>=24.1",
    "rich>=13.7",
    "mcp-shared",         # librería compartida del workspace
    # tus dependencias específicas:
    "sqlalchemy>=2.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mcp_database"]
```

### 3. `src/mcp_database/__init__.py`

```python
"""mcp-database — Servidor MCP para consultar bases de datos."""

from __future__ import annotations

__version__ = "1.0.0"
```

### 4. `src/mcp_database/config.py`

```python
"""Configuración del servidor mcp-database."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from mcp_shared.config import BaseMcpSettings


class DatabaseSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_url: str = Field(
        default="sqlite:///./data.db",
        description="URL de conexión. Variable: MCP_DB_DATABASE_URL.",
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base["database_url"] = self.database_url.split("@")[-1]  # ocultar credenciales
        return base


settings = DatabaseSettings()
```

### 5. `src/mcp_database/tools/database_tools.py`

```python
"""Lógica de negocio pura — sin imports de MCP ni FastMCP."""

from __future__ import annotations

from typing import Any

from mcp_shared.errors import NotFoundError, ValidationError


def query_table(table: str, limit: int = 100) -> list[dict[str, Any]]:
    """
    Ejecuta SELECT sobre una tabla.

    Args:
        table: Nombre de la tabla.
        limit: Máximo de filas a retornar.

    Returns:
        Lista de filas como dicts.

    Raises:
        ValidationError: Si el nombre de tabla es inválido.
        NotFoundError: Si la tabla no existe.
    """
    if not table.replace("_", "").isalnum():
        raise ValidationError(field="table", message=f"Nombre de tabla inválido: '{table}'")

    # ... implementación real con SQLAlchemy
    return []
```

### 6. `src/mcp_database/server.py`

```python
"""Servidor FastMCP para mcp-database."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData

from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging
from mcp_database.config import settings
from mcp_database.tools.database_tools import query_table

# ---------------------------------------------------------------------------
# Setup (antes de crear FastMCP)
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-database",
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-database")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

# ---------------------------------------------------------------------------
# Instancia del servidor
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-database",
    instructions="Servidor MCP para consultar bases de datos SQL.",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="query_table",
    description=(
        "Ejecuta SELECT sobre una tabla de la base de datos configurada. "
        "Parámetros: table (nombre de tabla), limit (máx. filas, default 100)."
    ),
)
def tool_query_table(table: str, limit: int = 100) -> list[dict[str, Any]]:
    try:
        return query_table(table=table, limit=limit)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))
    except Exception as exc:
        logger.exception("Error inesperado en query_table", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor."))

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
```

### 7. `tests/test_server.py`

```python
"""Tests básicos del servidor mcp-database."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from mcp_database.server import mcp


class TestServer:
    def test_server_is_fastmcp_instance(self) -> None:
        assert isinstance(mcp, FastMCP)

    def test_server_name(self) -> None:
        assert mcp.name == "mcp-database"

    def test_tools_registered(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        tool_names = {t.name for t in tools}
        assert "query_table" in tool_names

    def test_tool_count(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) >= 1
```

### 8. `Dockerfile`

Copia el Dockerfile de `mcp-calendar/Dockerfile` como base y ajusta:
- Nombre del paquete (busca/reemplaza `mcp_calendar` → `mcp_database`)
- Dependencias específicas en el `uv pip install`
- Variables de entorno específicas
- Puerto (`MCP_PORT=8005`)

### 9. Registrar en el workspace

**`pyproject.toml` (raíz)** — agregar en `members`:
```toml
[tool.uv.workspace]
members = [
    "shared", "mcp-tabular", "mcp-calendar",
    "mcp-markdown", "mcp-prompt-engineer",
    "mcp-database",   # ← nuevo
]
```

**`docker-compose.yml`** — nuevo servicio:
```yaml
mcp-database:
  build:
    context: .
    dockerfile: mcp-database/Dockerfile
    target: runtime
  image: mcp-database:latest
  container_name: mcp-database
  restart: unless-stopped
  env_file: .env
  environment:
    MCP_TRANSPORT: streamable-http
    MCP_HOST: "0.0.0.0"
    MCP_PORT: "8005"
  ports:
    - "127.0.0.1:8009:8005"
  healthcheck:
    test: ["CMD", "python", "-c", "import socket; socket.create_connection(('localhost', 8005), timeout=5)"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 15s
```

**`claude_desktop_config.json`** — nueva entrada:
```json
"mcp-database": {
  "command": "uv",
  "args": [
    "--directory", "C:/TU_RUTA/mcps/mcp-database",
    "run", "python", "-m", "mcp_database.server"
  ],
  "env": { "LOG_LEVEL": "INFO", "LOG_FORMAT": "console" }
}
```

### 10. Instalar y verificar

```bash
uv sync --all-packages
make test-mcp-database
make run-mcp-database  # verificar que arranca sin errores
```

---

## Convenciones de código

### Naming

| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Función de tool en `server.py` | `tool_` + nombre del tool | `tool_read_excel` |
| Función de negocio en `tools/*.py` | sin prefijo | `read_excel` |
| Clase de settings | `XSettings` o `Settings` | `DatabaseSettings` |
| Variable de entorno | `UPPER_SNAKE_CASE` | `MCP_DB_DATABASE_URL` |
| Archivo de tools | `*_tools.py` o nombre descriptivo | `database_tools.py` |

### Python

- **Python 3.11+** — usar `str | None`, `match`, `TypeAlias`, etc.
- **`from __future__ import annotations`** en todos los archivos
- **Type hints completos** en todas las funciones públicas
- **Strings con comillas dobles** `"` siempre
- **Líneas máximo 100 caracteres**
- **Imports agrupados:** stdlib → third-party → local (isort)

### Errores — reglas

1. En `tools/*.py`: usa siempre `McpError` y subclases de `mcp_shared.errors`
2. En `server.py`: convierte `McpError` → `SdkMcpError` en el bloque `try/except`
3. Nunca: `raise Exception("algo salió mal")` — usa la clase específica
4. Siempre captura `Exception` genérica como fallback en `server.py`

### Logging — reglas

1. `setup_logging()` se llama **una sola vez** en `server.py`, antes de `FastMCP(...)`
2. Los módulos de `tools/*.py` **no hacen logging** — solo la capa de servidor
3. Usa siempre contexto estructurado: `logger.info("msg", key=value)`, nunca f-strings en el mensaje
4. En el lifespan: `bind_contextvars(server_name="...")` para contexto automático

### Tests — reglas

- Test de instancia FastMCP: siempre
- Test de nombre del servidor: siempre
- Test de tools registradas: verificar `expected.issubset(tool_names)`
- Tests de tools de negocio en `tools/*.py`: sin levantar servidor
- Cobertura mínima: 55% (configurado en `pyproject.toml`)

---

## Cómo agregar una tool a un servidor existente

1. **Implementar** la función en `tools/*.py` (lógica pura)
2. **Exportar** desde `tools/__init__.py`
3. **Registrar** en `server.py` con `@mcp.tool(name="...", description="...")`
4. **Agregar** el nombre al `expected` set en `test_server.py`
5. **Ejecutar** `make test-mcp-NOMBRE` para verificar

---

## Variables de entorno — cómo se leen

Para un servidor con `env_prefix="MCP_DB_"`:

```
Campo Python        Variable de entorno
─────────────────────────────────────
database_url    →   MCP_DB_DATABASE_URL
max_connections →   MCP_DB_MAX_CONNECTIONS
```

Para los campos de transport en servidores con prefijo propio (`AliasChoices`):

```
Campo Python        Variable de entorno aceptada
──────────────────────────────────────────────────
mcp_transport   →   MCP_TRANSPORT  (sin prefijo, global)
                    MCP_MARKDOWN_MCP_TRANSPORT  (con prefijo, fallback)
```

---

## Docker — build y verificación

```bash
# Build de un servidor específico
docker compose build mcp-database

# Verificar que arranca en modo HTTP
docker compose up mcp-database

# Verificar healthcheck
docker compose ps mcp-database

# Ver logs
docker compose logs -f mcp-database

# Verificar TCP
python -c "import socket; socket.create_connection(('localhost', 8005), timeout=5); print('OK')"
```

---

*Última actualización: junio 2026*
