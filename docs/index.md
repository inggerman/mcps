# /docs — Índice de Documentación del Proyecto MCP

> **Nota para agentes IA:** Este directorio es el punto de memoria permanente del proyecto. Léelo al inicio de cada sesión de trabajo para tener contexto completo. El archivo más importante para saber *qué hacer a continuación* es [`project-state.md`](./project-state.md).

---

## Estructura de la documentación

| Archivo | Contenido | Cuándo leerlo |
|---------|-----------|---------------|
| [`project-state.md`](./project-state.md) | Estado actual, cambios recientes, pendientes, decisiones de diseño | **Siempre — primer archivo a leer** |
| [`architecture.md`](./architecture.md) | Arquitectura técnica, capas, patrones, estructura de archivos | Al entender cómo encaja todo |
| [`servers-reference.md`](./servers-reference.md) | Catálogo completo de tools reales por servidor (firmas exactas) | Al trabajar en tools específicas |
| [`shared-library.md`](./shared-library.md) | API completa de `mcp_shared`: config, logging, errores, modelos | Al usar o extender la librería compartida |
| [`development-guide.md`](./development-guide.md) | Guía para crear nuevos servidores, convenciones, checklist | Al agregar un nuevo servidor |

---

## Resumen ultra-rápido del proyecto

**Qué es:** Framework propio de servidores MCP (Model Context Protocol) en Python, basado en FastMCP v2. Permite a LLMs (Claude, GPT, Gemini) usar herramientas externas de forma estándar.

**Servidores implementados:**
- `mcp-tabular` — lee Excel, CSV, ODS, TSV, Parquet (8 tools)
- `mcp-calendar` — días hábiles 100+ países + divisas vía Frankfurter API (15 tools)
- `mcp-markdown` — lee, analiza y transforma archivos `.md` (12 tools)
- `mcp-prompt-engineer` — analiza y mejora prompts de LLM localmente (8 tools)
- `mcp-structured-output` — salidas estructuradas con JSON Schema: Bedrock + OpenAI-compatible (4 tools)
- `mcp-fetch` — HTTP GET/POST, extracción de texto HTML, consumo de APIs JSON (4 tools)
- `mcp-docker` — gestión de contenedores Docker: listar, logs, exec, run, stop, imágenes (8 tools)
- `mcp-kafka` — Apache Kafka: topics, consumer groups, produce y consume mensajes (6 tools)

**Transporte dual:** `MCP_TRANSPORT=stdio` para uso local (Claude Desktop, Cursor, Windsurf) — `MCP_TRANSPORT=streamable-http` para producción en Docker.

**Stack:** Python 3.11+, FastMCP v2, Pydantic v2, pydantic-settings, structlog, uv workspaces, Docker multi-stage.

---

## Rutas clave del proyecto

```
c:\Users\germa\Documents\IA\mcps\          ← raíz del workspace
├── shared/src/mcp_shared/                  ← librería compartida
├── mcp-tabular/src/mcp_tabular/            ← servidor tabular
├── mcp-calendar/src/mcp_calendar/          ← servidor calendario
├── mcp-markdown/src/mcp_markdown/          ← servidor markdown
├── mcp-prompt-engineer/src/mcp_prompt_engineer/  ← servidor prompts
├── mcp-structured-output/src/mcp_structured_output/ ← servidor structured output
├── mcp-fetch/src/mcp_fetch/                ← servidor HTTP fetch
├── mcp-docker/src/mcp_docker/              ← servidor Docker
├── mcp-kafka/src/mcp_kafka/               ← servidor Kafka
├── docker-compose.yml                      ← orquestación HTTP (puertos 8001-8008)
├── claude_desktop_config.json              ← config Claude Desktop (modo stdio)
├── .env.example                            ← plantilla variables de entorno
└── Makefile                                ← comandos operacionales
```

---

*Última actualización: junio 2026 — mcp-fetch, mcp-docker, mcp-kafka implementados*
