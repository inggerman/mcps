# Project State
**Última actualización:** 2026-07-15T00:34:53.617816+00:00
**Versión global:** 1.0.0

## Resumen
Este documento mantiene el estado actual del proyecto de forma retroactiva. Debe ser consultado al inicio de cualquier conversación para entender el contexto.

## Servidores MCP Activos (34)
- `mcp-tabular` — Archivos tabulares (Datos)
- `mcp-calendar` — Días hábiles y divisas (Datos)
- `mcp-markdown` — Archivos Markdown (Datos)
- `mcp-prompt-engineer` — Ingeniería de prompts (IA)
- `mcp-structured-output` — Structured Output (LLMs JSON Schema) (IA)
- `mcp-fetch` — HTTP y web scraping (APIs)
- `mcp-docker` — Gestión Docker (Plataforma)
- `mcp-kafka` — Apache Kafka (APIs)
- `mcp-project-memory` — Memoria de proyecto persistente (IA)
- `mcp-llm-router` — Ruteo inteligente de LLMs (IA)
- `mcp-git` — Operaciones Git (Ingeniería)
- `mcp-github` — Integración GitHub (APIs)
- `mcp-code-quality` — Calidad de código (Ingeniería)
- `mcp-architecture` — Análisis de arquitectura (Ingeniería)
- `mcp-event-driven` — Event-driven architecture (Flujos)
- `mcp-orchestrator` — Orquestación de DAGs (Flujos)
- `mcp-best-practices` — Documentación retroactiva (Flujos)
- `mcp-ci-cd` — Simulación de pipelines (Flujos)
- `mcp-design-patterns` — Patrones de diseño (Ingeniería)
- `mcp-security-champion` — Seguridad y compliance (Ingeniería)
- `mcp-database` — Consultas SQL (Datos)
- `mcp-filesystem` — Filesystem sandbox (Datos)
- `mcp-object-storage` — Object Storage S3/MinIO (Datos)
- `mcp-openapi` — OpenAPI client (APIs)
- `mcp-documents` — Documentos PDF/DOCX/PPTX (Datos)
- `mcp-browser` — Automatización web (APIs)
- `mcp-kubernetes` — Kubernetes (Plataforma)
- `mcp-observability` — Observabilidad (Plataforma)
- `mcp-terraform` — Infraestructura como código (Plataforma)
- `mcp-snyk` — Snyk SAST/SCA (Plataforma)
- `mcp-sonar` — SonarQube/SonarCloud (Plataforma)
- `mcp-java-build` — Builds Java (Plataforma)
- `mcp-agent-runner` — Orquestación de agentes (Flujos)
- `mcp-personal-vault` — Bóveda personal cifrada (Personal)

## Grupos

- **Datos:** `mcp-tabular`, `mcp-calendar`, `mcp-markdown`, `mcp-database`, `mcp-filesystem`, `mcp-object-storage`, `mcp-documents`
- **IA:** `mcp-prompt-engineer`, `mcp-structured-output`, `mcp-project-memory`, `mcp-llm-router`
- **APIs:** `mcp-fetch`, `mcp-kafka`, `mcp-github`, `mcp-openapi`, `mcp-browser`
- **Plataforma:** `mcp-docker`, `mcp-kubernetes`, `mcp-observability`, `mcp-terraform`, `mcp-snyk`, `mcp-sonar`, `mcp-java-build`
- **Ingeniería:** `mcp-git`, `mcp-code-quality`, `mcp-architecture`, `mcp-design-patterns`, `mcp-security-champion`
- **Flujos:** `mcp-event-driven`, `mcp-orchestrator`, `mcp-best-practices`, `mcp-ci-cd`, `mcp-agent-runner`
- **Personal:** `mcp-personal-vault`

## Reglas Generales
- Todos los servidores usan `FastMCP` v2.
- Comparten lógica mediante el paquete `mcp-shared`.
- Soportan transporte `stdio` (local) y `streamable-http` (Docker/producción).
- Pruebas ejecutadas con `pytest` y empaquetado manejado por `uv`.
- Configuración por servidor centralizada en `config.py` con `pydantic-settings`.
