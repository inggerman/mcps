# =============================================================================
# MCP Framework Makefile
# =============================================================================
.DEFAULT_GOAL := help
SHELL := /bin/bash

# Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
CYAN   := \033[0;36m
RESET  := \033[0m

SERVERS := mcp-tabular mcp-calendar mcp-markdown mcp-prompt-engineer mcp-structured-output mcp-fetch mcp-docker mcp-kafka mcp-project-memory mcp-llm-router mcp-git mcp-github mcp-code-quality mcp-architecture mcp-event-driven mcp-orchestrator mcp-best-practices mcp-ci-cd mcp-design-patterns mcp-security-champion

##@ Setup

.PHONY: install
install: ## Instala todas las dependencias (uv workspace sync)
	@echo "$(CYAN)→ Sincronizando workspace uv...$(RESET)"
	uv sync --all-packages
	@echo "$(GREEN)✓ Dependencias instaladas$(RESET)"

.PHONY: install-dev
install-dev: ## Instala dependencias incluyendo dev tools
	uv sync --all-packages --all-extras
	uv run pre-commit install
	@echo "$(GREEN)✓ Dev tools instalados y pre-commit configurado$(RESET)"

.PHONY: setup-env
setup-env: ## Crea .env desde .env.example si no existe
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(YELLOW)⚠ Creado .env desde .env.example — revisa y ajusta las variables$(RESET)"; \
	else \
		echo "$(GREEN)✓ .env ya existe$(RESET)"; \
	fi

##@ Desarrollo Local (sin Docker)

.PHONY: dev
dev: ## Inicia todos los MCPs en modo dev (usa un servidor a la vez)
	@echo "$(YELLOW)Usa 'make dev-SERVER' para iniciar un servidor específico$(RESET)"
	@echo "Servidores disponibles: $(SERVERS)"

.PHONY: dev-%
dev-%: ## Inicia un servidor MCP en modo dev  [Ej: make dev-mcp-tabular]
	@echo "$(CYAN)→ Iniciando $* en modo dev...$(RESET)"
	cd $* && uv run mcp dev src/$$(echo $* | tr '-' '_')/server.py

.PHONY: inspect
inspect: ## Abre MCP Inspector para un servidor  [Ej: make inspect SERVER=mcp-tabular]
	@if [ -z "$(SERVER)" ]; then echo "$(YELLOW)Usa: make inspect SERVER=mcp-tabular$(RESET)"; exit 1; fi
	@echo "$(CYAN)→ Abriendo MCP Inspector para $(SERVER)...$(RESET)"
	cd $(SERVER) && npx @modelcontextprotocol/inspector uv run python -m $$(echo $(SERVER) | tr '-' '_').server

.PHONY: run-%
run-%: ## Ejecuta directamente un servidor MCP  [Ej: make run-mcp-calendar]
	@echo "$(CYAN)→ Ejecutando $*...$(RESET)"
	cd $* && uv run python -m $$(echo $* | tr '-' '_').server

##@ Testing

.PHONY: test
test: ## Ejecuta todos los tests
	@echo "$(CYAN)→ Ejecutando tests...$(RESET)"
	uv run pytest \
		--cov=mcp_shared \
		--cov=mcp_calendar \
		--cov=mcp_docker \
		--cov=mcp_fetch \
		--cov=mcp_kafka \
		--cov=mcp_markdown \
		--cov=mcp_prompt_engineer \
		--cov=mcp_structured_output \
		--cov=mcp_tabular \
		--cov=mcp_project_memory \
		--cov=mcp_llm_router \
		--cov=mcp_git \
		--cov=mcp_github \
		--cov=mcp_code_quality \
		--cov=mcp_architecture \
		--cov=mcp_event_driven \
		--cov=mcp_orchestrator \
		--cov=mcp_best_practices \
		--cov=mcp_ci_cd \
		--cov=mcp_design_patterns \
		--cov=mcp_security_champion \
		--cov-report=term-missing

.PHONY: test-%
test-%: ## Tests de un servidor específico  [Ej: make test-mcp-tabular]
	@echo "$(CYAN)→ Tests de $*...$(RESET)"
	cd $* && uv run pytest -v

.PHONY: test-fast
test-fast: ## Tests rápidos (sin coverage)
	uv run pytest -x -q

##@ Calidad de Código

.PHONY: lint
lint: ## Linting con ruff + type check con mypy
	@echo "$(CYAN)→ Ruff lint...$(RESET)"
	uv run ruff check .
	@echo "$(CYAN)→ Mypy type check...$(RESET)"
	uv run mypy .
	@echo "$(GREEN)✓ Sin errores$(RESET)"

.PHONY: format
format: ## Formatea código con ruff
	@echo "$(CYAN)→ Formateando con ruff...$(RESET)"
	uv run ruff format .
	uv run ruff check --fix .
	@echo "$(GREEN)✓ Código formateado$(RESET)"

.PHONY: check
check: lint ## Alias para lint

##@ Docker

.PHONY: build
build: ## Build de todas las imágenes Docker
	@echo "$(CYAN)→ Building Docker images...$(RESET)"
	docker compose build

.PHONY: build-%
build-%: ## Build imagen de un servidor  [Ej: make build-mcp-tabular]
	docker compose build $*

.PHONY: up
up: ## Levanta todos los MCPs en Docker (modo producción)
	@echo "$(CYAN)→ Levantando servicios...$(RESET)"
	docker compose up -d
	@echo "$(GREEN)✓ Servicios corriendo$(RESET)"
	docker compose ps

.PHONY: down
down: ## Para todos los servicios Docker
	docker compose down

.PHONY: logs
logs: ## Ver logs de todos los servicios
	docker compose logs -f

.PHONY: logs-%
logs-%: ## Ver logs de un servicio  [Ej: make logs-mcp-tabular]
	docker compose logs -f $*

.PHONY: ps
ps: ## Estado de los servicios Docker
	docker compose ps

.PHONY: restart
restart: down up ## Reinicia todos los servicios

##@ Claude Desktop

.PHONY: claude-config
claude-config: ## Muestra la ruta para copiar claude_desktop_config.json
	@echo "$(CYAN)Config para Claude Desktop:$(RESET)"
	@echo "Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
	@echo "macOS:   ~/Library/Application Support/Claude/claude_desktop_config.json"
	@echo ""
	@cat claude_desktop_config.json

##@ Utilidades

.PHONY: clean
clean: ## Limpia caché y archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Limpieza completada$(RESET)"

.PHONY: status
status: ## Verifica que todas las dependencias están instaladas
	@echo "$(CYAN)Verificando herramientas...$(RESET)"
	@command -v uv >/dev/null 2>&1 && echo "$(GREEN)✓ uv$(RESET)" || echo "$(YELLOW)✗ uv no instalado — instalar: pip install uv$(RESET)"
	@command -v docker >/dev/null 2>&1 && echo "$(GREEN)✓ docker$(RESET)" || echo "$(YELLOW)✗ docker no instalado$(RESET)"
	@command -v tesseract >/dev/null 2>&1 && echo "$(GREEN)✓ tesseract$(RESET)" || echo "$(YELLOW)⚠ tesseract no instalado (requerido para OCR)$(RESET)"
	@command -v npx >/dev/null 2>&1 && echo "$(GREEN)✓ npx (MCP Inspector)$(RESET)" || echo "$(YELLOW)⚠ npx no disponible$(RESET)"

.PHONY: help
help: ## Muestra esta ayuda
	@awk 'BEGIN {FS = ":.*##"; printf "\n$(CYAN)MCP Framework$(RESET) — Comandos disponibles\n\n"} \
		/^[a-zA-Z_0-9%-]+:.*?##/ { printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)
