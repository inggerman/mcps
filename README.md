# 🧠 MCP Framework Personal

Framework de servidores MCP (Model Context Protocol) production-grade para uso local y producción.

## Servidores incluidos

| Servidor | Descripción | Tools |
|---|---|---|
| `mcp-tabular` | Excel, CSV, ODS, TSV → JSON estándar | 8 tools |
| `mcp-documents` | PDF, Word, PPT, ODT, OCR | 12 tools |
| `mcp-calendar` | Días hábiles México + Divisas | 14 tools |
| `mcp-markdown` | Leer, analizar, transformar .md | 12 tools |
| `mcp-prompt-engineer` | Analizar y mejorar prompts LLM | 10 tools |
| `mcp-utils` | Utilidades generales (hash, regex, JSON...) | 18 tools |

## Stack Técnico

- **SDK**: `mcp[cli]` oficial (Anthropic) + FastMCP 2.x
- **Package manager**: `uv` (workspaces)
- **Tipado**: Pydantic v2 + type hints completos
- **Logging**: structlog (JSON en prod, colorido en dev)
- **Config**: pydantic-settings (12-Factor App)
- **Testing**: pytest + pytest-asyncio
- **Linting**: ruff + mypy
- **Docker**: Multi-stage builds, non-root, healthchecks

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado
- Docker Desktop (para modo producción)
- Tesseract OCR (para OCR en `mcp-documents`)

### Instalar uv (si no lo tienes)
```powershell
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Instalar Tesseract OCR (Windows)
Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
```
Instalador: tesseract-ocr-w64-setup-5.x.x.exe
Agregar al PATH: C:\Program Files\Tesseract-OCR\
```

## Inicio Rápido

### 1. Instalar dependencias
```bash
cd c:/Users/germa/Documents/IA/mcps
uv sync --all-packages
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env si necesitas API keys
```

### 3. Usar con Claude Desktop

Copia el contenido de `claude_desktop_config.json` a tu configuración de Claude Desktop:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Reinicia Claude Desktop. Los MCPs aparecerán automáticamente.

### 4. Probar un servidor (modo desarrollo)
```bash
# Iniciar servidor con hot-reload
make dev-mcp-tabular

# O usar MCP Inspector (interfaz visual)
make inspect SERVER=mcp-tabular
```

## Comandos Makefile

```bash
make help              # Ver todos los comandos
make install           # Instalar todas las dependencias
make install-dev       # Instalar con dev tools + pre-commit
make dev-mcp-tabular   # Iniciar servidor específico en dev
make test              # Ejecutar todos los tests
make lint              # Ruff + mypy
make format            # Formatear código
make build             # Build Docker images
make up                # Levantar en Docker
make down              # Parar Docker
make logs              # Ver logs
make status            # Verificar herramientas instaladas
```

## Estructura del Proyecto

```
mcps/
├── shared/                    # Librería compartida (modelos, logging, config)
├── mcp-tabular/               # Servidor archivos tabulares
├── mcp-documents/             # Servidor documentos ricos
├── mcp-calendar/              # Servidor calendario + divisas
├── mcp-markdown/              # Servidor markdown
├── mcp-prompt-engineer/       # Servidor ingeniería de prompts
├── mcp-utils/                 # Servidor utilidades
├── docker-compose.yml         # Orquestación
├── pyproject.toml             # Workspace root
├── Makefile                   # CLI operacional
├── claude_desktop_config.json # Config Claude Desktop
└── .env.example               # Variables de entorno
```

## Despliegue en Producción (Docker)

```bash
# Copiar y configurar .env
cp .env.example .env
nano .env

# Build y levantar
make build
make up

# Verificar estado
make ps
make logs
```

## Configuración para Claude Desktop (producción Docker)

Si usas Docker en producción, actualiza `claude_desktop_config.json` para usar los contenedores:

```json
{
  "mcpServers": {
    "mcp-tabular": {
      "command": "docker",
      "args": ["run", "--rm", "-i",
               "-v", "C:/ruta/a/datos:/data:ro",
               "mcp-tabular:latest"]
    }
  }
}
```

## Agregar Nuevos MCPs

1. Crea la carpeta `mcp-nuevo/` con la estructura estándar
2. Agrega al workspace en `pyproject.toml`
3. Agrega el servicio en `docker-compose.yml`
4. Agrega la entrada en `claude_desktop_config.json`
5. Agrega target en `Makefile`

## Roadmap

- [ ] `mcp-database` — SQLite + PostgreSQL + MySQL
- [ ] `mcp-web-scraper` — Playwright async
- [ ] `mcp-git` — Operaciones Git completas
- [ ] `mcp-search` — Búsqueda semántica local (ChromaDB)
- [ ] `mcp-code-analyzer` — Análisis AST Python/JS/TS
- [ ] `mcp-email` — IMAP/SMTP
- [ ] `mcp-diagram` — Mermaid, PlantUML, Graphviz

## Soporte

Cada servidor tiene su propio `README.md` con documentación completa de tools y ejemplos de uso.
