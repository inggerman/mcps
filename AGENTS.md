# AGENTS.md — mcps

> Catálogo de servidores MCP. Proyecto canónico: `mcps` → `docs/projects/mcps/`

## Project

Catálogo de servidores MCP (Model Context Protocol) con FastMCP, desplegados en K3s namespace `mcp-services`.

## Stack

Python 3.11, uv workspaces, FastMCP, Docker, pytest, ruff, mypy.

## Build & Test

```bash
uv sync                    # instalar dependencias
pytest                     # tests
ruff check . && mypy .     # lint + types
```

## Convenciones específicas

- **Capas:** probar primero la lógica de `tools/`; mantener `server.py` como capa MCP delgada.
- **Cardinalidad:** no asumir que carpeta, manifest `uv`, `docker-compose.yml` y despliegue en cluster representan el mismo catálogo. Verificar cada uno por separado.
- **Transportes:** validar stdio y HTTP solo en entornos autorizados; marcar runtime `unverified` mientras no se ejecute.
- **Secretos:** no leer ni registrar `.env`, tokens, claves ni certificados. Usar env vars o Vault.
- **`k8s/all-mcps.yaml` está desactualizado** vs el runtime (namespace `mcps` vs `mcp-services`, ~35 vs 57 deployments). No usarlo como fuente de verdad.

## Scripts: nada suelto en la raiz

El 2026-09-10 se archivaron **198 scripts `.sh` sueltos** de la raiz de este repo
(escombro de sesiones de agente: `check-argo-wf5.sh`, `fix-argo-noauth2.sh`,
`rebuild-all-v7.sh`, `build-agents-kaniko-v8.sh`...). El rol `secret-scanner` encontro
50 hallazgos de riesgo `high` en 18 de ellos.

Reglas desde entonces:

- **Un script de un solo uso va a `scratch/`**, nunca a la raiz de `mcps/`.
- **Un script reutilizable va a `docs/scripts/<categoria>/`** y se registra en
  `docs/scripts/_manifest.json` e `INDEX.md`.
- **Nunca hardcodees credenciales ni rutas de kubeconfig.** Usa env vars o Vault.
- Antes de crear uno, busca en `docs/scripts/_manifest.json`: 11 capacidades de este
  repo ya se promovieron alli.

Archivo historico (solo lectura, valores comprometidos):
`archive/legacy-scripts/mcps-adhoc/` — ver su `README.md`.
Clasificacion reproducible: `python docs/scripts/mcp/classify-adhoc-scripts.py`.

## Artefactos pesados

`mcp-all-images.tar` ocupa **1.6 GB** de los 3.9 GB del repo. Esta en `.gitignore`,
asi que es un artefacto local regenerable: no lo trates como fuente y no lo copies.

## Workspace context

Este repo es parte del workspace `engineering/`. Sigue `../AGENTS.md` (raíz) para reglas transversales. Documentación canónica del proyecto: `../docs/projects/mcps/`.
