# Project State

**Ultima actualizacion:** 2026-06-13
**Estado:** 29 servidores MCP implementados e integrados.

## Resumen

El repositorio es un workspace `uv` de servidores FastMCP v2. Cada servidor
mantiene su configuracion, capa MCP, logica de negocio, pruebas y Dockerfile.
La infraestructura comun vive en `shared/src/mcp_shared`.

## Inventario

### Datos y contenido

- `mcp-tabular`
- `mcp-calendar`
- `mcp-markdown`
- `mcp-documents`
- `mcp-database`
- `mcp-filesystem`
- `mcp-object-storage`

### APIs e integraciones

- `mcp-fetch`
- `mcp-openapi`
- `mcp-browser`
- `mcp-kafka`
- `mcp-github`
- `mcp-structured-output`
- `mcp-llm-router`

### Ingenieria

- `mcp-prompt-engineer`
- `mcp-project-memory`
- `mcp-git`
- `mcp-code-quality`
- `mcp-architecture`
- `mcp-design-patterns`
- `mcp-security-champion`
- `mcp-event-driven`
- `mcp-orchestrator`
- `mcp-best-practices`
- `mcp-ci-cd`

### Plataforma

- `mcp-docker`
- `mcp-kubernetes`
- `mcp-observability`
- `mcp-terraform`

## Operacion

- Local: `stdio` mediante `claude_desktop_config.json`.
- Contenedores: `streamable-http` mediante `docker-compose.yml`.
- Servicios base: `docker compose up -d`.
- Plataforma: `make up-platform`.
- Todos los perfiles: `make up-extended`.
- Escrituras y acciones destructivas estan deshabilitadas por defecto en
  Database, Filesystem, Object Storage, OpenAPI, Kubernetes y Terraform.

## Calidad

- Tests: 345 pruebas verdes con `uv run pytest -q`
- Cobertura global: 65.87% (minimo requerido: 55%)
- Lint: `uv run ruff check .`
- Tipos: `uv run mypy .`
- Compose: `docker compose --profile privileged-tools --profile platform-tools --profile cloud --profile browser config --quiet`
