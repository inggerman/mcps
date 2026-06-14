# MCP Framework — Manual de Onboarding

> **Para quien nunca escuchó hablar de MCP:** Este documento explica desde cero qué es MCP, para qué sirve este proyecto, cómo usarlo hoy mismo y cómo extenderlo. Léelo de principio a fin la primera vez; después úsalo como referencia.

---

## Tabla de Contenidos

1. [¿Qué es MCP? (la idea en 5 minutos)](#1-qué-es-mcp-la-idea-en-5-minutos)
2. [¿Para qué sirve este proyecto?](#2-para-qué-sirve-este-proyecto)
3. [Arquitectura general](#3-arquitectura-general)
4. [Catálogo de servidores](#4-catálogo-de-servidores)
5. [Prerrequisitos e instalación](#5-prerrequisitos-e-instalación)
6. [Uso local con Claude Desktop / Cursor / Windsurf](#6-uso-local-con-claude-desktop--cursor--windsurf)
7. [Desarrollo y pruebas](#7-desarrollo-y-pruebas)
8. [Despliegue en producción con Docker](#8-despliegue-en-producción-con-docker)
9. [La librería compartida `mcp_shared`](#9-la-librería-compartida-mcp_shared)
10. [Cómo crear un nuevo servidor MCP](#10-cómo-crear-un-nuevo-servidor-mcp)
11. [Variables de entorno de referencia](#11-variables-de-entorno-de-referencia)
12. [Referencia de comandos Makefile](#12-referencia-de-comandos-makefile)
13. [Convenciones y estándares de código](#13-convenciones-y-estándares-de-código)
14. [Preguntas frecuentes (FAQ)](#14-preguntas-frecuentes-faq)

---

## 1. ¿Qué es MCP? (la idea en 5 minutos)

### El problema que MCP resuelve

Los modelos de lenguaje (Claude, GPT, Gemini…) son muy buenos generando texto, pero viven "encerrados" — no pueden leer tus archivos, consultar tu base de datos, ni llamar a tus APIs internas. Cada integración se construía a mano, de forma distinta en cada herramienta.

**MCP (Model Context Protocol)** es el estándar abierto creado por Anthropic en 2024 que define *cómo* un modelo de IA se comunica con herramientas externas de forma universal. Es como USB para la IA: cualquier cliente que hable MCP puede usar cualquier servidor MCP, sin código de pegamento.

### Los tres componentes del protocolo

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTE MCP                          │
│        (Claude Desktop, Cursor, Windsurf, tu app…)          │
│                                                             │
│  El modelo de IA le dice al cliente: "necesito leer        │
│  un Excel". El cliente llama al servidor correcto.          │
└───────────────────────┬─────────────────────────────────────┘
                        │  Protocolo JSON-RPC 2.0
                        │  (via stdio o HTTP)
┌───────────────────────▼─────────────────────────────────────┐
│                      SERVIDOR MCP                           │
│           (este proyecto — mcp-tabular, etc.)               │
│                                                             │
│  Proceso Python independiente que expone "tools",           │
│  "resources" y "prompts" al modelo.                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                 SISTEMA EXTERNO                              │
│     (archivos del disco, APIs web, bases de datos…)         │
└─────────────────────────────────────────────────────────────┘
```

### Los tres tipos de capacidades que expone un servidor

| Tipo | ¿Qué es? | Ejemplo |
|------|----------|---------|
| **Tool** | Función que el modelo puede llamar | `read_excel("ventas.xlsx")` |
| **Resource** | Datos que el modelo puede leer | El contenido de un archivo |
| **Prompt** | Plantilla de instrucciones reutilizable | "Eres un analista de datos…" |

Este proyecto usa principalmente **tools** — son las más versátiles.

### Los dos modos de transporte

| Modo | Cuándo usarlo | Cómo funciona |
|------|--------------|---------------|
| **stdio** | Local (Claude Desktop, Cursor, Windsurf) | El cliente lanza el servidor como subproceso; se comunican por stdin/stdout |
| **streamable-http** | Producción (servidor remoto, múltiples clientes) | El servidor escucha en un puerto HTTP; el cliente hace requests |

> **Regla de oro:** durante desarrollo usa `stdio`. En producción usa `streamable-http` con Docker.

---

## 2. ¿Para qué sirve este proyecto?

Este repositorio es un **framework propio** de servidores MCP, diseñado para:

- Correr **localmente** en la máquina del desarrollador (integrado con Claude Desktop, Cursor o Windsurf).
- Desplegarse **en producción** en un servidor remoto de forma transparente — cambiando solo una variable de entorno (`MCP_TRANSPORT`).
- Compartir código de infraestructura (logging, configuración, manejo de errores) entre todos los servidores a través de la librería `mcp_shared`.
- Seguir estándares de producción: tipado estático, tests, Docker multi-stage, usuarios no-root y healthchecks.

---

## 3. Arquitectura general

```
mcps/                              ← raíz del workspace uv
│
├── shared/                        ← librería compartida (se instala como paquete)
│   └── src/mcp_shared/
│       ├── config.py              ← BaseMcpSettings (base de configuración)
│       ├── errors.py              ← jerarquía de errores tipados
│       ├── logging.py             ← setup_logging() con structlog
│       └── models.py              ← modelos Pydantic reutilizables
│
├── mcp-tabular/                   ← servidor de archivos tabulares
│   ├── src/mcp_tabular/
│   │   ├── config.py              ← Settings (hereda BaseMcpSettings)
│   │   ├── server.py              ← instancia FastMCP + tools registradas
│   │   └── tools/                 ← lógica de negocio pura
│   ├── Dockerfile                 ← build multi-stage
│   └── pyproject.toml             ← dependencias del servidor
│
├── mcp-calendar/                  ← servidor de calendario y divisas
├── mcp-markdown/                  ← servidor de archivos Markdown
├── mcp-prompt-engineer/           ← servidor de ingeniería de prompts
│
├── docker-compose.yml             ← orquestación (modo HTTP / producción)
├── pyproject.toml                 ← workspace root: ruff, mypy, pytest
├── Makefile                       ← comandos operacionales
├── claude_desktop_config.json     ← config para Claude Desktop (modo stdio)
└── .env.example                   ← plantilla de variables de entorno
```

### Principio de diseño: separación en capas

```
server.py          ← CAPA MCP: registra tools, maneja errores MCP, logging
    │
tools/*.py         ← CAPA DE NEGOCIO: lógica pura, sin dependencias MCP
    │
mcp_shared/        ← CAPA COMPARTIDA: config, errores, logging, modelos
```

Esto significa que puedes probar la lógica de `tools/` con tests unitarios normales, sin necesidad de levantar un servidor MCP.

---

## 4. Catálogo de servidores

### `mcp-tabular` — Archivos tabulares

Lee y procesa Excel (`.xlsx`, `.xls`), CSV, TSV, ODS y Parquet. Convierte todo a JSON estructurado para que el modelo pueda analizarlo.

| Tool | Qué hace |
|------|----------|
| `read_excel` | Lee una hoja de un archivo Excel |
| `read_csv` | Lee un CSV/TSV con detección automática de delimitador |
| `list_sheets` | Lista las hojas de un Excel |
| `get_column_info` | Tipos de datos, valores únicos, estadísticas por columna |
| `filter_rows` | Filtra filas por condición |
| `aggregate_data` | Agrupa y agrega (suma, promedio, conteo…) |
| `merge_files` | Une dos archivos por columnas clave |
| `export_to_json` | Exporta resultado a JSON |

**Caso de uso típico:** "Analiza el archivo `ventas_Q1.xlsx` y dime las 5 categorías con más ingresos."

---

### `mcp-calendar` — Días hábiles y divisas

Calcula días hábiles para más de 100 países y obtiene tasas de cambio en tiempo real vía la API gratuita de Frankfurter (Banco Central Europeo).

#### Tools de días hábiles

| Tool | Qué hace |
|------|----------|
| `get_holidays` | Lista feriados de un país y año |
| `calculate_business_days` | Días hábiles entre dos fechas |
| `add_business_days` | Suma N días hábiles a una fecha |
| `is_business_day` | Verifica si una fecha es hábil |
| `next_business_day` | Siguiente día hábil |
| `previous_business_day` | Día hábil anterior |
| `business_days_in_month` | Total de días hábiles en un mes |
| `get_mexico_holidays` | Feriados MX con descripción histórica en español |
| `get_country_list` | Países soportados con subdivisiones |

#### Tools de divisas

| Tool | Qué hace |
|------|----------|
| `get_exchange_rate` | Tasa de cambio actual entre dos divisas |
| `convert_currency` | Convierte un monto de divisa a divisa |
| `get_historical_rate` | Tasa de cambio histórica (desde 1999) |
| `get_mx_rates` | MXN vs principales divisas mundiales |
| `list_supported_currencies` | Todas las divisas disponibles (ISO 4217) |
| `get_rate_history` | Serie histórica de tasas entre dos fechas |

**Caso de uso típico:** "¿Cuántos días hábiles hay en septiembre 2025 en México? ¿Y si el equipo en Alemania tiene que entregar el mismo día?"

---

### `mcp-markdown` — Archivos Markdown

Lee, analiza y transforma archivos `.md`. Extrae estructura, convierte formatos, valida sintaxis.

| Tool | Qué hace |
|------|----------|
| `read_markdown` | Lee un archivo .md del disco |
| `extract_headings` | Extrae la jerarquía de títulos |
| `extract_links` | Lista todos los enlaces (internos y externos) |
| `extract_code_blocks` | Extrae bloques de código por lenguaje |
| `get_toc` | Genera tabla de contenidos automática |
| `markdown_to_html` | Convierte a HTML |
| `markdown_to_plain_text` | Convierte a texto plano |
| `validate_markdown` | Detecta errores de sintaxis y enlaces rotos |
| `search_in_markdown` | Búsqueda con regex dentro del archivo |
| `format_markdown` | Normaliza el formato del Markdown |
| `get_frontmatter` | Extrae metadatos YAML del frontmatter |
| `list_markdown_files` | Lista archivos .md en un directorio |

**Caso de uso típico:** "Lee toda la documentación técnica en `/docs` y dame un resumen de los endpoints disponibles."

---

### `mcp-prompt-engineer` — Ingeniería de prompts

Analiza y mejora prompts para LLMs. Todo el procesamiento es local — sin llamadas a APIs externas ni costos adicionales.

| Tool | Qué hace |
|------|----------|
| `analyze_prompt` | Análisis completo: tokens, idioma, claridad (0–10), problemas |
| `classify_prompt` | Clasifica el tipo (instrucción, pregunta, few-shot, sistema…) |
| `estimate_tokens` | Estima tokens en GPT-4, Claude, GPT-3.5 simultáneamente |
| `improve_prompt` | Mejora automática con diff de cambios |
| `generate_variations` | Genera N variaciones con distintos enfoques (CoT, rol, formato…) |
| `create_system_prompt` | Crea un system prompt estructurado desde rol + contexto |
| `decompose_task` | Descompone tareas complejas en subtareas |
| `get_prompt_template` | Retorna un template optimizado para un caso de uso |

**Caso de uso típico:** "Analiza este prompt que escribí para el bot de soporte y dime cómo mejorarlo."

---

### Catálogo completo

Además de los cuatro servidores descritos arriba, el workspace incluye:

| Grupo | Servidores |
|---|---|
| Datos | `mcp-database`, `mcp-filesystem`, `mcp-object-storage`, `mcp-documents` |
| APIs | `mcp-fetch`, `mcp-openapi`, `mcp-browser`, `mcp-kafka`, `mcp-github` |
| IA | `mcp-structured-output`, `mcp-llm-router`, `mcp-project-memory` |
| Ingeniería | `mcp-git`, `mcp-code-quality`, `mcp-architecture`, `mcp-design-patterns`, `mcp-security-champion` |
| Flujos | `mcp-event-driven`, `mcp-orchestrator`, `mcp-best-practices`, `mcp-ci-cd` |
| Plataforma | `mcp-docker`, `mcp-kubernetes`, `mcp-observability`, `mcp-terraform` |

El inventario operativo, puertos y perfiles está en
[`docs/servers-reference.md`](docs/servers-reference.md).

---

## 5. Prerrequisitos e instalación

### Herramientas necesarias

| Herramienta | Para qué | Instalación |
|-------------|----------|-------------|
| Python 3.11+ | Ejecutar los servidores | [python.org](https://python.org) |
| **uv** | Gestor de paquetes y entornos | Ver abajo |
| Docker Desktop | Modo producción | [docker.com](https://docker.com) |
| Node.js / npx | MCP Inspector (opcional) | [nodejs.org](https://nodejs.org) |

### Instalar `uv`

`uv` es el gestor de paquetes de este proyecto. Es mucho más rápido que pip y maneja workspaces de Python.

```powershell
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verificar instalación
uv --version
```

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clonar e instalar el proyecto

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd mcps

# 2. Instalar todas las dependencias (crea el entorno virtual automáticamente)
uv sync --all-packages

# 3. Instalar con dev tools (para contribuir al código)
uv sync --all-packages --all-extras
uv run pre-commit install

# 4. Crear tu archivo .env
cp .env.example .env
```

Después de `uv sync`, verás una carpeta `.venv/` en la raíz. No necesitas activarla manualmente — `uv run` la usa automáticamente.

---

## 6. Uso local con Claude Desktop / Cursor / Windsurf

En modo local, el cliente de IA lanza cada servidor como un subproceso y se comunican por **stdio** (sin abrir puertos, sin red). Es la forma más simple y segura de usar los MCPs en tu máquina.

### Paso 1 — Verificar que los servidores funcionan

```bash
# Prueba rápida: inicia un servidor manualmente
cd mcp-calendar
uv run python -m mcp_calendar.server
# Debería iniciar sin errores (Ctrl+C para parar)
```

### Paso 2 — Configurar Claude Desktop

Copia el archivo `claude_desktop_config.json` de este repositorio a la carpeta de configuración de Claude Desktop:

| Sistema operativo | Ruta |
|-------------------|------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |

> **Importante:** actualiza las rutas absolutas dentro del JSON. Busca `C:/Users/germa/Documents/IA/mcps` y reemplázalas con tu ruta real.

```json
{
  "mcpServers": {
    "mcp-calendar": {
      "command": "uv",
      "args": [
        "--directory", "C:/TU_RUTA/mcps/mcp-calendar",
        "run", "python", "-m", "mcp_calendar.server"
      ],
      "env": {
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "console",
        "DEFAULT_COUNTRY": "MX"
      }
    }
  }
}
```

### Paso 3 — Reiniciar Claude Desktop

Cierra y vuelve a abrir Claude Desktop. En la barra inferior verás el icono de herramientas — al hacer click verás los MCPs disponibles y sus tools.

### Configurar Cursor o Windsurf

Estos editores tienen una sección "MCP Servers" en su configuración. El formato es idéntico al de Claude Desktop.

---

## 7. Desarrollo y pruebas

### Iniciar un servidor en modo desarrollo

```bash
# Opción A: modo dev con hot-reload (recomienda para desarrollo activo)
make dev-mcp-tabular

# Opción B: ejecución directa
cd mcp-tabular
uv run python -m mcp_tabular.server

# Opción C: MCP Inspector (interfaz web visual para probar tools)
make inspect SERVER=mcp-tabular
# Abre http://localhost:5173 en el navegador
```

### Ejecutar tests

```bash
# Todos los tests del workspace
make test

# Tests de un servidor específico
make test-mcp-calendar

# Tests rápidos (sin coverage, para verificar rápido)
make test-fast

# Con coverage detallado
uv run pytest --cov=. --cov-report=html
# Abre htmlcov/index.html en el navegador
```

### Linting y formateo

```bash
# Verificar calidad del código (ruff + mypy)
make lint

# Formatear código automáticamente
make format

# Verificar que todo está en orden antes de un commit
make check
```

Pre-commit está configurado para ejecutar estas verificaciones automáticamente antes de cada `git commit`.

### Estructura de un servidor (para leer el código)

Cuando abres cualquier servidor, encontrarás esta estructura:

```
mcp-tabular/
└── src/mcp_tabular/
    ├── __init__.py        ← versión del paquete, exports públicos
    ├── config.py          ← Settings: todas las variables de entorno del servidor
    ├── server.py          ← PUNTO DE ENTRADA: instancia FastMCP, registra tools
    └── tools/
        ├── __init__.py    ← exports públicos de las tools
        └── tabular_tools.py  ← implementación real (sin dependencias MCP)
```

**Flujo de una llamada MCP:**

```
Cliente llama tool "read_excel"
        │
        ▼
server.py: @mcp.tool("read_excel")  ← recibe parámetros validados
        │
        ▼
tools/tabular_tools.py: read_excel()  ← lógica pura, testeable
        │
        ▼
Resultado → serializado a JSON → devuelto al cliente
```

---

## 8. Despliegue en producción con Docker

Los servidores corren como contenedores HTTP y Compose publica sus puertos solo
en `127.0.0.1`. Para acceso remoto se requiere un reverse proxy con TLS y
autenticación; no expongas estos puertos directamente a Internet.

### Configurar el entorno de producción

```bash
# 1. Crear .env de producción
cp .env.example .env

# 2. Ajustar las variables clave en .env:
#    LOG_FORMAT=json          (logs JSON para ELK/Datadog)
#    LOG_LEVEL=INFO
#    MCP_TRANSPORT=streamable-http   (ya lo fija docker-compose)
#    MCP_DATA_DIR=/ruta/a/tus/datos
```

### Build y arranque

```bash
# Build de todas las imágenes (primera vez o tras cambios)
make build

# Levantar todos los servicios en background
make up

# mcp-docker requiere acceso privilegiado al socket del daemon
docker compose --profile privileged-tools up -d mcp-docker

# Kubernetes, observabilidad y Terraform
make up-platform

# Todos los perfiles opcionales, incluido S3 y Playwright
make up-extended

# Ver estado
make ps

# Ver logs en tiempo real
make logs

# Logs de un servidor específico
make logs-mcp-calendar

# Parar todo
make down
```

### Puertos expuestos

| Servidor | Puerto | URL |
|----------|--------|-----|
| `mcp-tabular` | 8001 | `http://127.0.0.1:8001/` |
| `mcp-calendar` | 8002 | `http://127.0.0.1:8002/` |
| `mcp-markdown` | 8003 | `http://127.0.0.1:8003/` |
| `mcp-prompt-engineer` | 8004 | `http://127.0.0.1:8004/` |
| `mcp-structured-output` | 8005 | `http://127.0.0.1:8005/` |
| `mcp-fetch` | 8006 | `http://127.0.0.1:8006/` |
| `mcp-docker` | 8007 | `http://127.0.0.1:8007/` |
| `mcp-kafka` | 8008 | `http://127.0.0.1:8008/` |
| `mcp-project-memory` | 8009 | `http://127.0.0.1:8009/` |
| `mcp-llm-router` | 8010 | `http://127.0.0.1:8010/` |
| `mcp-git` | 8011 | `http://127.0.0.1:8011/` |
| `mcp-github` | 8012 | `http://127.0.0.1:8012/` |
| `mcp-code-quality` | 8013 | `http://127.0.0.1:8013/` |
| `mcp-architecture` | 8014 | `http://127.0.0.1:8014/` |
| `mcp-event-driven` | 8015 | `http://127.0.0.1:8015/` |
| `mcp-orchestrator` | 8016 | `http://127.0.0.1:8016/` |
| `mcp-best-practices` | 8017 | `http://127.0.0.1:8017/` |
| `mcp-ci-cd` | 8018 | `http://127.0.0.1:8018/` |
| `mcp-design-patterns` | 8019 | `http://127.0.0.1:8019/` |
| `mcp-security-champion` | 8020 | `http://127.0.0.1:8020/` |
| `mcp-database` | 8021 | `http://127.0.0.1:8021/` |
| `mcp-filesystem` | 8022 | `http://127.0.0.1:8022/` |
| `mcp-object-storage` | 8023 | `http://127.0.0.1:8023/` |
| `mcp-openapi` | 8024 | `http://127.0.0.1:8024/` |
| `mcp-documents` | 8025 | `http://127.0.0.1:8025/` |
| `mcp-browser` | 8026 | `http://127.0.0.1:8026/` |
| `mcp-kubernetes` | 8027 | `http://127.0.0.1:8027/` |
| `mcp-observability` | 8028 | `http://127.0.0.1:8028/` |
| `mcp-terraform` | 8029 | `http://127.0.0.1:8029/` |

### Healthcheck

Cada contenedor verifica su propia disponibilidad:

```bash
# Ver estado de salud de todos los contenedores
docker compose ps

# Verificar manualmente un servidor HTTP
python -c "import socket; socket.create_connection(('localhost', 8002), timeout=5); print('OK')"
```

### Acceso mediante reverse proxy

El endpoint público del ejemplo debe terminar TLS y exigir autenticación antes
de reenviar tráfico al puerto local:

```json
{
  "mcpServers": {
    "mcp-calendar": {
      "transport": "streamable-http",
      "url": "http://tu-servidor.com:8002/"
    }
  }
}
```

---

## 9. La librería compartida `mcp_shared`

Todos los servidores importan de `mcp_shared`. No dupliques lo que ya está ahí.

### `BaseMcpSettings` — Configuración base

La mayoría de los servidores heredan de esta clase. Markdown y Prompt Engineer
mantienen settings propios compatibles con las mismas variables globales.

```python
from mcp_shared.config import BaseMcpSettings
from pydantic import Field

class MiSettings(BaseMcpSettings):
    mi_api_key: str = Field(default="", description="API key del servicio.")
    max_items: int = Field(default=100, ge=1)

settings = MiSettings()
# Lee MCP_HOST, MCP_PORT, MCP_TRANSPORT, LOG_LEVEL, LOG_FORMAT, etc.
# + MCP_MI_API_KEY, MCP_MAX_ITEMS (si defines env_prefix="MCP_")
```

Variables que hereda **todo servidor** de `BaseMcpSettings`:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `LOG_FORMAT` | `json` | `json` (prod) o `console` (dev) |
| `MCP_HOST` | `0.0.0.0` | Host del servidor HTTP |
| `MCP_PORT` | `8000` | Puerto del servidor HTTP |
| `MCP_SERVER_NAME` | `mcp-server` | Nombre en logs |
| `MCP_TRANSPORT` | `stdio` | `stdio` o `streamable-http` |
| `MCP_DEBUG` | `false` | Modo debug |
| `MCP_WORKERS` | `1` | Workers del servidor |

### `setup_logging` — Logging estructurado

```python
from mcp_shared.logging import setup_logging, get_logger

# Llamar UNA vez al inicio del servidor (antes de crear FastMCP)
setup_logging(
    log_level=settings.log_level,   # "INFO", "DEBUG", etc.
    log_format=settings.log_format,  # "json" o "console"
    server_name="mi-servidor",
)

# En cualquier módulo:
logger = get_logger(__name__)
logger.info("Procesando archivo", path="/data/ventas.xlsx", rows=1500)
```

En `LOG_FORMAT=console` (desarrollo) los logs son coloridos y legibles. En `LOG_FORMAT=json` (producción) son JSON de una línea, listos para ingestar en ELK o Datadog.

### `McpError` y subclases — Errores tipados

```python
from mcp_shared.errors import (
    ValidationError,    # Parámetro inválido
    NotFoundError,      # Recurso no encontrado
    InvalidValueError,  # Valor fuera de rango
    ApiError,           # Error de API externa
    NetworkError,       # Error de red
    NetworkTimeoutError,# Timeout de red
)

# Uso en tools:
def mi_tool(path: str) -> dict:
    if not Path(path).exists():
        raise NotFoundError(resource="archivo", identifier=path)

    if len(path) > 1000:
        raise ValidationError(field="path", message="Ruta demasiado larga")
```

En `server.py` se capturan y convierten a `SdkMcpError` para que el cliente MCP reciba un error estructurado:

```python
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError

@mcp.tool("mi_tool")
def tool_mi_tool(path: str) -> dict:
    try:
        return mi_tool(path)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))
    except Exception as exc:
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor."))
```

---

## 10. Cómo crear un nuevo servidor MCP

Sigue estos pasos para agregar `mcp-database` (ejemplo):

### Paso 1 — Crear la estructura de carpetas

```
mcp-database/
├── src/
│   └── mcp_database/
│       ├── __init__.py
│       ├── config.py
│       ├── server.py
│       └── tools/
│           ├── __init__.py
│           └── database_tools.py
├── tests/
│   └── test_server.py
├── Dockerfile
└── pyproject.toml
```

### Paso 2 — `pyproject.toml`

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
    "mcp-shared",        # librería compartida del workspace
    "sqlalchemy>=2.0",   # dependencia específica de este servidor
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mcp_database"]
```

### Paso 3 — `config.py`

```python
from pydantic import Field
from pydantic_settings import SettingsConfigDict
from mcp_shared.config import BaseMcpSettings

class DatabaseSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_DB_",   # lee MCP_DB_DATABASE_URL, etc.
        env_file=".env",
        extra="ignore",
    )

    database_url: str = Field(
        default="sqlite:///./data.db",
        description="URL de conexión a la base de datos.",
    )

settings = DatabaseSettings()
```

### Paso 4 — `tools/database_tools.py`

```python
# Lógica pura — sin imports de MCP ni FastMCP
from mcp_shared.errors import NotFoundError, ValidationError

def query_table(table: str, limit: int = 100) -> list[dict]:
    """Ejecuta una query SELECT sobre una tabla."""
    if not table.isidentifier():
        raise ValidationError(field="table", message="Nombre de tabla inválido.")
    # ... implementación real
    return []
```

### Paso 5 — `server.py`

```python
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

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-database",
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-database")
    logger.info("Servidor mcp-database iniciando", db_url=settings.database_url)
    yield
    logger.info("Servidor mcp-database detenido")


mcp = FastMCP(
    name="mcp-database",
    instructions="Servidor MCP para consultar bases de datos.",
    lifespan=lifespan,
)


@mcp.tool(
    name="query_table",
    description="Ejecuta SELECT sobre una tabla. Parámetros: table (str), limit (int, default 100).",
)
def tool_query_table(table: str, limit: int = 100) -> list[dict[str, Any]]:
    try:
        return query_table(table=table, limit=limit)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))
    except Exception as exc:
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor."))


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
```

### Paso 6 — Registrar en el workspace

**`pyproject.toml` (raíz):**
```toml
[tool.uv.workspace]
members = [
    "shared",
    "mcp-tabular",
    "mcp-calendar",
    "mcp-markdown",
    "mcp-prompt-engineer",
    "mcp-database",     # ← agregar aquí
]
```

**`docker-compose.yml`:**
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

**`claude_desktop_config.json`:**
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

### Paso 7 — Sincronizar e instalar

```bash
uv sync --all-packages
make test-mcp-database
```

---

## 11. Variables de entorno de referencia

Copia `.env.example` a `.env` y ajusta según tu entorno.

### Variables globales (todos los servidores)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | `stdio` (local) o `streamable-http` (producción) |
| `MCP_HOST` | `0.0.0.0` | Host del servidor HTTP |
| `MCP_PORT` | `8000` | Puerto base (docker-compose asigna uno por servidor) |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FORMAT` | `json` | `json` (producción) o `console` (desarrollo) |
| `MCP_DATA_DIR` | `./data` | Directorio de datos montado en Docker |

### Variables específicas por servidor

| Variable | Servidor | Descripción |
|----------|----------|-------------|
| `DEFAULT_COUNTRY` | `mcp-calendar` | País por defecto para días hábiles (ej: `MX`) |
| `EXCHANGE_CACHE_TTL_SECONDS` | `mcp-calendar` | TTL del caché de tasas (default: 3600) |
| `TABULAR_ALLOWED_ROOT` | `mcp-tabular` | Raíz opcional permitida para leer archivos |
| `MCP_MARKDOWN_ALLOWED_ROOT` | `mcp-markdown` | Raíz opcional permitida para leer archivos |
| `MCP_FETCH_ALLOW_PRIVATE_NETWORKS` | `mcp-fetch` | Permite redes privadas; default `false` |

---

## 12. Referencia de comandos Makefile

```bash
# Setup
make install              # Instala todas las dependencias (uv sync)
make install-dev          # Instala con dev tools + pre-commit
make setup-env            # Crea .env desde .env.example
make status               # Verifica herramientas instaladas

# Desarrollo
make dev-mcp-tabular      # Inicia servidor con hot-reload
make run-mcp-calendar     # Ejecuta directamente un servidor
make inspect SERVER=mcp-tabular  # Abre MCP Inspector visual

# Testing
make test                 # Todos los tests con coverage
make test-mcp-calendar    # Tests de un servidor específico
make test-fast            # Tests rápidos sin coverage

# Calidad de código
make lint                 # ruff check + mypy
make format               # ruff format + ruff check --fix

# Docker (producción)
make build                # Build todas las imágenes
make build-mcp-tabular    # Build una imagen específica
make up                   # Levantar servicios sin acceso al socket Docker
docker compose --profile privileged-tools up -d mcp-docker
make down                 # Parar todos los servicios
make logs                 # Ver logs en tiempo real
make logs-mcp-calendar    # Logs de un servidor
make ps                   # Estado de los contenedores
make restart              # down + up

# Utilidades
make claude-config        # Muestra cómo configurar Claude Desktop
make clean                # Limpia __pycache__, .pytest_cache, etc.
make help                 # Lista todos los comandos disponibles
```

---

## 13. Convenciones y estándares de código

### Python
- **Versión mínima:** Python 3.11 (se usan `match`, `str | None`, `TypeAlias`, etc.)
- **Tipos:** tipo hints en todas las funciones públicas (`ANN` activado en ruff)
- **Strings:** dobles `"` siempre
- **Longitud de línea:** 100 caracteres
- **Imports:** agrupados y ordenados por isort (`I` en ruff)

### Naming
- Funciones de tool (en `server.py`): prefijo `tool_` → `tool_read_excel`
- Funciones de lógica pura (en `tools/*.py`): sin prefijo → `read_excel`
- Clases de configuración: `Settings` o `XSettings` (ej: `CalendarSettings`)
- Variables de entorno: `UPPER_SNAKE_CASE`

### Errores
- Usa **siempre** las clases de `mcp_shared.errors` en la capa de tools
- Convierte a `SdkMcpError` **solo** en `server.py`
- Nunca hagas `raise Exception("mensaje vago")` — usa la clase específica

### Logging
- Llama `setup_logging()` **una sola vez** al inicio de `server.py`
- Obtén loggers con `get_logger(__name__)` — no uses `print()`
- Incluye contexto estructurado: `logger.info("msg", key=value, otro=valor)`
- En la capa de tools, no hagas logging — solo en `server.py`

### Tests
- Cada servidor tiene su carpeta `tests/`
- Tests unitarios de `tools/*.py`: no requieren servidor MCP
- Cobertura mínima: 55% (configurado en `pyproject.toml`)

---

## 14. Preguntas frecuentes (FAQ)

**¿Por qué `uv` y no `pip` o `poetry`?**
`uv` es entre 10x y 100x más rápido que pip, maneja workspaces de Python nativamente (un solo `uv sync` instala todos los paquetes de todos los servidores) y genera lock files reproducibles. En Docker usamos la imagen oficial de `ghcr.io/astral-sh/uv` para el stage de build.

**¿Qué es un "workspace" de uv?**
Un workspace permite tener múltiples paquetes Python en un repositorio y que se referencien entre sí. El `pyproject.toml` raíz declara los miembros. `mcp_shared` se instala como un paquete real disponible para todos los servidores, sin necesidad de `sys.path` hacks.

**¿Puedo usar los MCPs desde código Python propio (sin Claude Desktop)?**
Sí. Con `MCP_TRANSPORT=streamable-http` cada servidor expone un endpoint HTTP estándar. Puedes conectarte con el cliente oficial:
```python
from fastmcp import Client

async with Client("http://localhost:8002/") as client:
    result = await client.call_tool("calculate_business_days", {
        "start_date": "2025-01-01",
        "end_date": "2025-03-31",
    })
```

**¿Por qué los Dockerfiles usan usuarios no-root?**
Buena práctica de seguridad. Si un atacante logra ejecutar código dentro del contenedor, no tiene privilegios de root en el host. Todos los Dockerfiles crean un usuario con UID 1001.

**¿Cómo depuro si una tool falla en producción?**
```bash
# 1. Ver logs del contenedor
make logs-mcp-calendar

# 2. Los logs JSON tienen: tool, error_code, error_type, mensaje
# 3. Para debug más detallado, agrega MCP_DEBUG=true y LOG_LEVEL=DEBUG en .env
# 4. Reiniciar con: make restart
```

**¿FastMCP v1 o v2?**
Este proyecto usa **FastMCP v2** (`fastmcp>=2.3`, paquete standalone). La v1 venía incluida en `mcp[cli]` de Anthropic. La v2 tiene mejor soporte para transporte HTTP, mejor manejo del lifespan y una API más limpia.

**¿Qué pasa si `MCP_TRANSPORT` no está definido?**
El default es `stdio`. El servidor arranca en modo local. Nunca fallará por falta de esta variable.

**¿Puedo agregar autenticación al transporte HTTP?**
Sí. FastMCP v2 soporta middleware ASGI. Para producción se recomienda poner un reverse proxy (nginx, Caddy) con autenticación delante de los servidores MCP, en lugar de manejar auth dentro del servidor.

---

*Última actualización: junio 2026 — FastMCP v2, Python 3.11+, uv workspaces*
