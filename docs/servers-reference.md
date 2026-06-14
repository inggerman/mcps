# Servers Reference
**Última actualización:** 2026-06-13T20:48:00.165625

Documentación autogenerada basada en la configuración de Claude Desktop.

## mcp-tabular
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-tabular run python -m mcp_tabular.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console

## mcp-calendar
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-calendar run python -m mcp_calendar.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `DEFAULT_COUNTRY`: MX

## mcp-markdown
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-markdown run python -m mcp_markdown.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console

## mcp-prompt-engineer
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-prompt-engineer run python -m mcp_prompt_engineer.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console

## mcp-kafka
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-kafka run python -m mcp_kafka.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `MCP_KAFKA_BOOTSTRAP_SERVERS`: localhost:9092

## mcp-docker
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-docker run python -m mcp_docker.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console

## mcp-fetch
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-fetch run python -m mcp_fetch.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console

## mcp-structured-output
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-structured-output run python -m mcp_structured_output.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `MCP_SO_AWS_REGION`: us-east-1

## mcp-project-memory
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-project-memory run python -m mcp_project_memory.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `MEMORY_DIR`: C:/Users/germa/Documents/IA/mcps/.ai-memory
  - `MEMORY_PROJECT_NAME`: mcps
  - `MEMORY_PROJECT_ROOT`: C:/Users/germa/Documents/IA/mcps
  - `MEMORY_AUTO_SYNC`: false

## mcp-llm-router
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-llm-router run python -m mcp_llm_router.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `ROUTER_LMSTUDIO_BASE_URL`: http://localhost:1234/v1
  - `ROUTER_COMPLEXITY_THRESHOLD`: 6
  - `ROUTER_MAX_LOCAL_TOKENS`: ********
  - `ROUTER_MODEL_FAST`: qwen3-8b
  - `ROUTER_MODEL_CODE`: devstral-small-2507
  - `ROUTER_MODEL_REASON`: deepseek-r1-0528-qwen3-8b
  - `ROUTER_MODEL_LARGE`: qwen2.5-14b-instruct-1m
  - `ROUTER_CLOUD_PROVIDER`: anthropic
  - `ROUTER_CLOUD_MODEL`: claude-sonnet-4-5

## mcp-git
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-git run python -m mcp_git.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `GIT_REPO_PATH`: C:/Users/germa/Documents/IA/mcps
  - `GIT_DEFAULT_BRANCH`: main
  - `GIT_ALLOW_FORCE_PUSH`: false

## mcp-github
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-github run python -m mcp_github.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `GITHUB_API_URL`: https://api.github.com
  - `GITHUB_OWNER`: inggerman
  - `GITHUB_REPO`: mcps

## mcp-code-quality
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-code-quality run python -m mcp_code_quality.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `CQ_PROJECT_PATH`: C:/Users/germa/Documents/IA/mcps
  - `CQ_LINTER_CMD`: uv run ruff check
  - `CQ_FORMATTER_CMD`: uv run ruff format
  - `CQ_TEST_CMD`: uv run pytest

## mcp-architecture
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-architecture run python -m mcp_architecture.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `ARCH_PROJECT_PATH`: C:/Users/germa/Documents/IA/mcps

## mcp-event-driven
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-event-driven run python -m mcp_event_driven.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `EVENT_SCHEMAS_PATH`: C:/Users/germa/Documents/IA/mcps/schemas

## mcp-orchestrator
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-orchestrator run python -m mcp_orchestrator.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `ORCH_DAGS_PATH`: C:/Users/germa/Documents/IA/mcps/dags

## mcp-best-practices
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-best-practices run python -m mcp_best_practices.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `BP_PROJECT_PATH`: C:/Users/germa/Documents/IA/mcps
  - `BP_DOCS_PATH`: C:/Users/germa/Documents/IA/mcps/docs

## mcp-ci-cd
- **Comando:** `uv --directory C:/Users/germa/Documents/IA/mcps/mcp-ci-cd run python -m mcp_ci_cd.server`
- **Variables de entorno (Locales):**
  - `LOG_LEVEL`: INFO
  - `LOG_FORMAT`: console
  - `CICD_PROJECT_PATH`: C:/Users/germa/Documents/IA/mcps
