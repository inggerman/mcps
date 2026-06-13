# Arquitectura Técnica

---

## Visión general

```
mcps/  (uv workspace root)
│
├── shared/                          paquete Python compartido
│   └── src/mcp_shared/
│       ├── config.py                BaseMcpSettings
│       ├── errors.py                ErrorCode + jerarquía de excepciones
│       ├── logging.py               setup_logging() + get_logger()
│       └── models.py                modelos Pydantic reutilizables
│
├── mcp-tabular/                     servidor — archivos tabulares
├── mcp-calendar/                    servidor — días hábiles + divisas
├── mcp-markdown/                    servidor — archivos Markdown
├── mcp-prompt-engineer/             servidor — ingeniería de prompts
│
├── docker-compose.yml               orquestación HTTP (puertos 8001-8008)
├── pyproject.toml                   workspace: ruff, mypy, pytest config
├── Makefile                         comandos operacionales
├── claude_desktop_config.json       config Claude Desktop (modo stdio)
└── .env.example                     plantilla de variables de entorno
```

---

## Estructura interna de cada servidor

Todos los servidores siguen exactamente la misma estructura:

```
mcp-NOMBRE/
├── src/
│   └── mcp_NOMBRE/
│       ├── __init__.py              versión (__version__), exports públicos
│       ├── config.py                Settings (hereda BaseMcpSettings o BaseSettings)
│       ├── server.py                PUNTO DE ENTRADA — instancia FastMCP + tools
│       └── tools/
│           ├── __init__.py          exports públicos de funciones de negocio
│           └── *.py                 lógica pura sin dependencias MCP
├── tests/
│   └── test_server.py               tests del servidor
├── Dockerfile                       build multi-stage
└── pyproject.toml                   dependencias
```

---

## Separación en capas (el patrón más importante)

```
┌─────────────────────────────────────────────┐
│  server.py  — CAPA MCP                      │
│  • Instancia FastMCP                         │
│  • Registra @mcp.tool(...)                  │
│  • Maneja errores McpError → SdkMcpError    │
│  • Hace logging                              │
│  • Entrypoint stdio / streamable-http        │
├─────────────────────────────────────────────┤
│  tools/*.py  — CAPA DE NEGOCIO              │
│  • Lógica pura de Python                     │
│  • Sin imports de fastmcp ni mcp             │
│  • Sin logging (solo en server.py)           │
│  • Lanza McpError de mcp_shared              │
│  • 100% testeable con pytest unitario        │
├─────────────────────────────────────────────┤
│  mcp_shared/  — CAPA COMPARTIDA             │
│  • BaseMcpSettings                           │
│  • Jerarquía de errores tipados              │
│  • setup_logging() / get_logger()            │
│  • Modelos Pydantic reutilizables            │
└─────────────────────────────────────────────┘
```

**Regla:** Las capas solo se comunican hacia abajo. `server.py` importa de `tools/` y de `mcp_shared`. `tools/` solo importa de `mcp_shared.errors`. Nunca al revés.

---

## Flujo de una llamada MCP completa

```
Cliente MCP (Claude Desktop, Cursor, etc.)
         │
         │  JSON-RPC 2.0 via stdio o HTTP
         ▼
server.py: @mcp.tool("read_tabular_file")
         │
         │  Parámetros validados por FastMCP/Pydantic
         ▼
try:
    result = tools/tabular_reader.read_tabular_file(path, ...)
except McpError as exc:
    raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))
except Exception:
    raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor."))
         │
         ▼
Resultado serializado a JSON → cliente
```

---

## Transporte dual: stdio ↔ streamable-http

El mismo servidor soporta ambos modos con cero cambios de código:

```python
# Patrón en todos los server.py
if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
```

| Escenario | Variable | Cómo se lanza |
|-----------|----------|---------------|
| Claude Desktop / Cursor / Windsurf (local) | `MCP_TRANSPORT=stdio` | El cliente lanza el proceso; `uv run python -m mcp_X.server` |
| Docker / servicio local | `MCP_TRANSPORT=streamable-http` | `docker compose up`; publicado solo en `127.0.0.1` |

---

## Configuración: jerarquía de Settings

```
pydantic BaseSettings
    └── BaseMcpSettings  (shared/src/mcp_shared/config.py)
            ├── TabularSettings   (prefijo TABULAR_)
            └── CalendarSettings  (sin prefijo adicional)

pydantic BaseSettings
    ├── Settings  en mcp-markdown   (prefijo MCP_MARKDOWN_)
    └── Settings  en mcp-prompt-engineer  (prefijo MCP_PE_)
```

> **Nota:** `mcp-markdown` y `mcp-prompt-engineer` no heredan `BaseMcpSettings` (tienen su propio sistema de configuración previo). Para que lean `MCP_TRANSPORT` sin prefijo usan `AliasChoices`:
> ```python
> mcp_transport: str = Field(
>     default="stdio",
>     validation_alias=AliasChoices("MCP_TRANSPORT", "MCP_MARKDOWN_MCP_TRANSPORT"),
> )
> ```

### Prioridad de carga de variables (de mayor a menor)
1. Variables de entorno del sistema operativo
2. Archivo `.env` en el directorio de trabajo
3. Valores `default` definidos en la clase

---

## Docker: arquitectura de contenedores

Todos los Dockerfiles usan **multi-stage build**:

```dockerfile
# Stage 1: builder — instala dependencias con uv
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# ... instalar deps
RUN uv pip install --system --no-cache "fastmcp>=2.3" ...

# Stage 2: runtime — imagen mínima, usuario non-root
FROM python:3.11-slim AS runtime
# Copiar solo lo instalado, sin uv ni cache
COPY --from=builder /usr/local/lib/python3.11/site-packages ...
# Usuario non-root (UID 1001)
RUN useradd --uid 1001 ...
USER mcpuser
ENV MCP_TRANSPORT=stdio MCP_PORT=8000
CMD ["python", "-m", "mcp_X.server"]
```

### Puertos en producción (docker-compose.yml)

| Servicio | Puerto host | Puerto contenedor |
|----------|-------------|-------------------|
| `mcp-tabular` | 8001 | 8001 |
| `mcp-calendar` | 8002 | 8002 |
| `mcp-markdown` | 8003 | 8003 |
| `mcp-prompt-engineer` | 8004 | 8004 |
| `mcp-structured-output` | 8005 | 8005 |
| `mcp-fetch` | 8006 | 8006 |
| `mcp-docker` | 8007 | 8007 |
| `mcp-kafka` | 8008 | 8008 |

`docker-compose.yml` sobreescribe `MCP_TRANSPORT=streamable-http` y el puerto correcto para cada servicio via `environment:`, ignorando el default `stdio` del Dockerfile.

`mcp-docker` requiere `docker compose --profile privileged-tools up -d
mcp-docker`, porque el socket Docker otorga control privilegiado sobre el
daemon.

---

## uv Workspace

El repositorio es un **workspace de uv**. Esto significa:

- Un solo `uv sync --all-packages` instala todo.
- `mcp_shared` es un paquete Python real, no un hack de `sys.path`.
- Cada servidor declara `mcp-shared` como dependencia en su `pyproject.toml`.
- Lock file único en la raíz garantiza reproducibilidad.

```toml
# pyproject.toml raíz
[tool.uv.workspace]
members = ["shared", "mcp-tabular", "mcp-calendar", "mcp-markdown", "mcp-prompt-engineer",
           "mcp-structured-output", "mcp-fetch", "mcp-docker", "mcp-kafka"]
```

---

## Stack tecnológico

| Componente | Tecnología | Versión mínima | Nota |
|------------|-----------|----------------|------|
| Framework MCP | FastMCP | `>=2.3` | Paquete standalone (no bundled con mcp[cli]) |
| SDK base MCP | mcp | depende de fastmcp | Para `McpError`, `ErrorData` |
| Configuración | pydantic-settings | `>=2.3` | Carga desde env + .env |
| Validación | Pydantic | `>=2.7` | V2 — modelos tipados |
| Logging | structlog | `>=24.1` | JSON en prod, colorido en dev |
| Package manager | uv | latest | Workspaces, lock file |
| Linting | ruff | via uv | `E,W,F,I,B,C4,UP,N,S,ANN,PTH,RUF` |
| Type checking | mypy | via uv | definiciones tipadas obligatorias |
| Testing | pytest + pytest-asyncio | via uv | asyncio_mode=auto |
| Contenedores | Docker multi-stage | — | Non-root, healthchecks |

---

*Última actualización: junio 2026*
