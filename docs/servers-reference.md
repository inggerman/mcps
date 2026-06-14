# Servers Reference

**Ultima actualizacion:** 2026-06-13

El inventario operativo se deriva de `claude_desktop_config.json` y
`docker-compose.yml`. Todos los puertos se publican solo en `127.0.0.1`.

| Servidor | Puerto | Perfil Compose | Acceso sensible |
|---|---:|---|---|
| `mcp-tabular` | 8001 | base | lectura de `/data` |
| `mcp-calendar` | 8002 | base | API de divisas |
| `mcp-markdown` | 8003 | base | lectura de `/data` |
| `mcp-prompt-engineer` | 8004 | base | ninguno |
| `mcp-structured-output` | 8005 | base | credenciales del proveedor |
| `mcp-fetch` | 8006 | base | red HTTP(S) |
| `mcp-docker` | 8007 | `privileged-tools` | socket Docker |
| `mcp-kafka` | 8008 | base | cluster Kafka |
| `mcp-project-memory` | 8009 | base | volumen persistente |
| `mcp-llm-router` | 8010 | base | LM Studio/proveedor cloud |
| `mcp-git` | 8011 | base | repositorio montado |
| `mcp-github` | 8012 | base | token GitHub |
| `mcp-code-quality` | 8013 | base | repositorio montado |
| `mcp-architecture` | 8014 | base | repositorio montado |
| `mcp-event-driven` | 8015 | base | directorio `schemas` |
| `mcp-orchestrator` | 8016 | base | directorio `dags` |
| `mcp-best-practices` | 8017 | base | repositorio montado |
| `mcp-ci-cd` | 8018 | base | repositorio montado |
| `mcp-design-patterns` | 8019 | base | repositorio montado |
| `mcp-security-champion` | 8020 | base | repositorio montado |
| `mcp-database` | 8021 | base | SQL, solo lectura por defecto |
| `mcp-filesystem` | 8022 | base | sandbox, solo lectura |
| `mcp-object-storage` | 8023 | `cloud` | S3/MinIO, solo lectura |
| `mcp-openapi` | 8024 | base | invocacion deshabilitada |
| `mcp-documents` | 8025 | base | lectura de `/data` |
| `mcp-browser` | 8026 | `browser` | navegacion HTTP(S) |
| `mcp-kubernetes` | 8027 | `platform-tools` | kubeconfig, solo lectura |
| `mcp-observability` | 8028 | `platform-tools` | Prometheus/Loki |
| `mcp-terraform` | 8029 | `platform-tools` | apply deshabilitado |

## Perfiles

```bash
docker compose up -d
docker compose --profile privileged-tools up -d mcp-docker
docker compose --profile platform-tools up -d
docker compose --profile cloud up -d mcp-object-storage
docker compose --profile browser up -d mcp-browser
make up-extended
```

Las variables disponibles y sus valores seguros por defecto estan documentados
en `.env.example`.
