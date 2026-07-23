import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
INVENTORY_FILE = ROOT / ".mcp_inventory.json"

BASE_FIELDS = {
    "log_level", "log_format", "mcp_host", "mcp_port", "mcp_server_name",
    "mcp_debug", "mcp_workers", "mcp_transport",
}

META = {
    "mcp-agent-runner": {
        "title": "Orquestación de agentes",
        "desc": "Dispara webhooks (ej. n8n) y ejecuta scripts locales para delegar tareas a sub-agentes.",
        "use": "Automatiza un workflow de n8n o ejecuta un script de mantenimiento desde Claude.",
        "group": "Flujos",
    },
    "mcp-architecture": {
        "title": "Análisis de arquitectura",
        "desc": "Explora la estructura de un proyecto Python, analiza dependencias por AST y detecta violaciones a principios SOLID.",
        "use": "Entiende el acoplamiento de un módulo nuevo o revisa si una clase cumple SOLID.",
        "group": "Ingeniería",
    },
    "mcp-best-practices": {
        "title": "Documentación retroactiva",
        "desc": "Mantiene actualizados docs/project-state.md y docs/servers-reference.md escaneando el repositorio.",
        "use": "Pídele que refresque la referencia de servidores tras agregar un nuevo MCP.",
        "group": "Flujos",
    },
    "mcp-browser": {
        "title": "Automatización web",
        "desc": "Navega sitios con Playwright, extrae contenido visible y toma screenshots.",
        "use": "Lee el contenido de una documentación web o captura un screenshot de una UI.",
        "group": "APIs",
    },
    "mcp-calendar": {
        "title": "Días hábiles y divisas",
        "desc": "Calcula días hábiles y feriados para más de 100 países y consulta tasas de cambio vía Frankfurter.",
        "use": "Calcula fechas de entrega entre México y Alemania y convierte montos a EUR.",
        "group": "Datos",
    },
    "mcp-ci-cd": {
        "title": "Simulación de pipelines",
        "desc": "Ejecuta pipelines CI/CD locales configurables sobre el repositorio.",
        "use": "Corre un pipeline de validación antes de hacer commit.",
        "group": "Flujos",
    },
    "mcp-code-quality": {
        "title": "Calidad de código",
        "desc": "Ejecuta linters, formateadores y tests sobre el proyecto.",
        "use": "Verifica rápido que el código pase ruff y pytest.",
        "group": "Ingeniería",
    },
    "mcp-database": {
        "title": "Consultas SQL",
        "desc": "Inspecciona esquemas y ejecuta queries SQL de forma controlada (read-only por defecto).",
        "use": "Consulta tablas de una base SQLite de analytics sin salir del chat.",
        "group": "Datos",
    },
    "mcp-design-patterns": {
        "title": "Patrones de diseño",
        "desc": "Detecta anti-patrones en el código y sugiere patrones de diseño aplicables.",
        "use": "Refactoriza una clase con muchas responsabilidades sugiriendo Strategy o Factory.",
        "group": "Ingeniería",
    },
    "mcp-docker": {
        "title": "Gestión Docker",
        "desc": "Lista contenedores, imágenes, logs, exec y gestiona el ciclo de vida de contenedores e imágenes.",
        "use": "Consulta logs de un contenedor o ejecuta un comando ad-hoc sin abrir la terminal.",
        "group": "Plataforma",
    },
    "mcp-documents": {
        "title": "Documentos PDF/DOCX/PPTX",
        "desc": "Extrae texto y metadatos de documentos de oficina.",
        "use": "Resume el contenido de un contrato PDF o extrae diapositivas de una presentación.",
        "group": "Datos",
    },
    "mcp-event-driven": {
        "title": "Event-driven architecture",
        "desc": "Parsea esquemas de eventos, analiza coreografía y genera payloads de prueba.",
        "use": "Diseña un flujo event-driven validando que los consumidores cubren todos los eventos.",
        "group": "Flujos",
    },
    "mcp-fetch": {
        "title": "HTTP y web scraping",
        "desc": "Realiza peticiones GET/POST, extrae texto de HTML y consume JSON.",
        "use": "Obtén el contenido de una API REST o extrae el artículo de una página de noticias.",
        "group": "APIs",
    },
    "mcp-filesystem": {
        "title": "Filesystem sandbox",
        "desc": "Lista, lee, busca y escribe archivos dentro de una raíz configurable.",
        "use": "Lee logs o busca archivos de configuración dentro del proyecto.",
        "group": "Datos",
    },
    "mcp-git": {
        "title": "Operaciones Git",
        "desc": "Status, diff, log, add, commit en dos pasos, pull, push y gestión de ramas.",
        "use": "Prepara un commit revisando el diff y confirma de forma segura.",
        "group": "Ingeniería",
    },
    "mcp-github": {
        "title": "Integración GitHub",
        "desc": "Crea issues, pull requests, comentarios y consulta diffs vía API REST de GitHub.",
        "use": "Abre un issue con el contexto de un error o revisa un PR desde el chat.",
        "group": "APIs",
    },
    "mcp-java-build": {
        "title": "Builds Java",
        "desc": "Ejecuta comandos Maven y Gradle sobre proyectos Java.",
        "use": "Compila un proyecto Spring Boot o ejecuta tests con Maven.",
        "group": "Plataforma",
    },
    "mcp-kafka": {
        "title": "Apache Kafka",
        "desc": "Lista topics, describe configuraciones, produce y consume mensajes, revisa consumer groups.",
        "use": "Depura un consumer group atascado o publica un mensaje de prueba en un topic.",
        "group": "APIs",
    },
    "mcp-kubernetes": {
        "title": "Kubernetes",
        "desc": "Lista namespaces, pods y deployments, obtiene logs y escala deployments.",
        "use": "Consulta logs de un pod en staging o escala un deployment ante pico de tráfico.",
        "group": "Plataforma",
    },
    "mcp-llm-router": {
        "title": "Ruteo inteligente de LLMs",
        "desc": "Rutea tareas entre modelos locales (LM Studio) y modelos en la nube según complejidad, privacidad y tokens.",
        "use": "Delega una pregunta simple a un modelo local y una tarea compleja a Claude.",
        "group": "IA",
    },
    "mcp-markdown": {
        "title": "Archivos Markdown",
        "desc": "Lee, analiza, valida y transforma archivos Markdown: headings, links, code blocks, frontmatter.",
        "use": "Genera un resumen de /docs o valida que no haya enlaces rotos.",
        "group": "Datos",
    },
    "mcp-object-storage": {
        "title": "Object Storage S3/MinIO",
        "desc": "Lista buckets y objetos, sube/descarga texto, genera URLs presignadas y elimina objetos.",
        "use": "Sube un reporte JSON a S3 o genera una URL temporal de descarga.",
        "group": "Datos",
    },
    "mcp-observability": {
        "title": "Observabilidad",
        "desc": "Ejecuta queries PromQL y LogQL, y realiza health checks a endpoints.",
        "use": "Consulta el error rate de las últimas horas o busca logs de un servicio.",
        "group": "Plataforma",
    },
    "mcp-openapi": {
        "title": "OpenAPI client",
        "desc": "Descubre operaciones de una especificación OpenAPI y las invoca con un allowlist.",
        "use": "Lista los endpoints de una API interna documentada en OpenAPI y llama uno permitido.",
        "group": "APIs",
    },
    "mcp-orchestrator": {
        "title": "Orquestación de DAGs",
        "desc": "Parsea DAGs de Airflow, valida acyclicidad y genera código boilerplate.",
        "use": "Valida que un nuevo DAG no tenga ciclos antes de subirlo.",
        "group": "Flujos",
    },
    "mcp-personal-vault": {
        "title": "Bóveda personal cifrada",
        "desc": "Almacena y recupera contexto personal cifrado (preferencias, contactos, trayectoria).",
        "use": "Recuerda preferencias del usuario entre sesiones sin exponer datos sensibles.",
        "group": "Personal",
    },
    "mcp-project-memory": {
        "title": "Memoria de proyecto persistente",
        "desc": "Mantiene estado, decisiones, tareas y snapshots entre sesiones de agentes de IA.",
        "use": "Recupera el contexto completo al inicio de una sesión y guárdalo al finalizar.",
        "group": "IA",
    },
    "mcp-prompt-engineer": {
        "title": "Ingeniería de prompts",
        "desc": "Analiza, mejora, clasifica y genera variaciones de prompts para LLMs.",
        "use": "Optimiza un prompt de soporte al cliente para mayor claridad.",
        "group": "IA",
    },
    "mcp-security-champion": {
        "title": "Seguridad y compliance",
        "desc": "Audita código buscando secretos y funciones inseguras, y revisa compliance financiero básico.",
        "use": "Revisa un archivo antes de commit en busca de tokens hardcodeados.",
        "group": "Ingeniería",
    },
    "mcp-snyk": {
        "title": "Snyk SAST/SCA",
        "desc": "Ejecuta `snyk test` sobre el proyecto y reporta vulnerabilidades en dependencias.",
        "use": "Escanea vulnerabilidades de una rama antes del merge.",
        "group": "Plataforma",
    },
    "mcp-sonar": {
        "title": "SonarQube/SonarCloud",
        "desc": "Ejecuta análisis de calidad con sonar-scanner y resume bugs, code smells y cobertura.",
        "use": "Obtén un resumen de deuda técnica del proyecto.",
        "group": "Plataforma",
    },
    "mcp-structured-output": {
        "title": "Structured Output (LLMs JSON Schema)",
        "desc": "Invoca LLMs (Bedrock, OpenAI-compatible) con salida forzada a JSON Schema; incluye validación y generación de schemas.",
        "use": "Extrae entidades estructuradas de texto o genera un schema compatible con Bedrock.",
        "group": "IA",
    },
    "mcp-tabular": {
        "title": "Archivos tabulares",
        "desc": "Lee Excel, CSV, TSV, ODS y Parquet; filtra, agrega y exporta a JSON.",
        "use": "Analiza ventas_Q1.xlsx y muestra las 5 categorías con más ingresos.",
        "group": "Datos",
    },
    "mcp-terraform": {
        "title": "Infraestructura como código",
        "desc": "Ejecuta comandos Terraform init, plan, validate y apply (deshabilitado por defecto).",
        "use": "Valida un cambio de infraestructura con `terraform plan` antes de aplicar.",
        "group": "Plataforma",
    },
}

PORT_ORDER = [
    "mcp-tabular", "mcp-calendar", "mcp-markdown", "mcp-prompt-engineer",
    "mcp-structured-output", "mcp-fetch", "mcp-docker", "mcp-kafka",
    "mcp-project-memory", "mcp-llm-router", "mcp-git", "mcp-github",
    "mcp-code-quality", "mcp-architecture", "mcp-event-driven", "mcp-orchestrator",
    "mcp-best-practices", "mcp-ci-cd", "mcp-design-patterns", "mcp-security-champion",
    "mcp-database", "mcp-filesystem", "mcp-object-storage", "mcp-openapi",
    "mcp-documents", "mcp-browser", "mcp-kubernetes", "mcp-observability",
    "mcp-terraform", "mcp-snyk", "mcp-sonar", "mcp-java-build", "mcp-agent-runner",
    "mcp-personal-vault",
]
PORTS = {name: 8000 + i for i, name in enumerate(PORT_ORDER, start=1)}

PROFILES = {
    "mcp-docker": "privileged-tools",
    "mcp-object-storage": "cloud",
    "mcp-browser": "browser",
    "mcp-kubernetes": "platform-tools",
    "mcp-observability": "platform-tools",
    "mcp-terraform": "platform-tools",
    "mcp-personal-vault": "personal",
}

LOCAL_BASE = "C:/Users/germa/Documents/IA/mcps"

VOLUMES = {
    "mcp-tabular": [("mcp-data", "/data", "ro")],
    "mcp-markdown": [("mcp-data", "/data", "ro")],
    "mcp-project-memory": [("mcp-memory", "/app/.ai-memory", "")],
    "mcp-docker": [("/var/run/docker.sock", "/var/run/docker.sock", "ro")],
    "mcp-git": [(".", "/repo", "")],
    "mcp-code-quality": [(".", "/repo", "")],
    "mcp-architecture": [(".", "/repo", "")],
    "mcp-event-driven": [("./schemas", "/schemas", "")],
    "mcp-orchestrator": [("./dags", "/dags", "")],
    "mcp-best-practices": [(".", "/repo", "")],
    "mcp-ci-cd": [(".", "/repo", "")],
    "mcp-design-patterns": [(".", "/repo", "")],
    "mcp-security-champion": [(".", "/repo", "")],
    "mcp-database": [("mcp-data", "/data", "")],
    "mcp-filesystem": [("mcp-data", "/data", "ro")],
    "mcp-openapi": [("mcp-data", "/data", "ro")],
    "mcp-documents": [("mcp-data", "/data", "ro")],
    "mcp-browser": [("mcp-data", "/data", "")],
    "mcp-kubernetes": [("${KUBECONFIG_DIR:-./data/kube}", "/home/mcpuser/.kube", "ro")],
    "mcp-terraform": [(".", "/workspace", "")],
    "mcp-snyk": [(".", "/repo", "")],
    "mcp-sonar": [(".", "/repo", "")],
    "mcp-java-build": [(".", "/repo", "")],
    "mcp-agent-runner": [(".", "/repo", "")],
    "mcp-personal-vault": [("mcp-personal-vault", "/vault", "")],
}

EXTRA_ENV = {
    "mcp-tabular": {"TABULAR_ALLOWED_ROOT": "/data"},
    "mcp-markdown": {"MCP_MARKDOWN_ALLOWED_ROOT": "/data"},
    "mcp-project-memory": {"MEMORY_MEMORY_DIR": "/app/.ai-memory", "MEMORY_MEMORY_FILE": "project_memory.json", "MEMORY_PROJECT_NAME": "mcps"},
    "mcp-llm-router": {
        "ROUTER_LMSTUDIO_BASE_URL": "http://host.docker.internal:1234/v1",
        "ROUTER_COMPLEXITY_THRESHOLD": "6",
        "ROUTER_MODEL_FAST": "qwen3-8b",
        "ROUTER_MODEL_CODE": "devstral-small-2507",
        "ROUTER_MODEL_REASON": "deepseek-r1-0528-qwen3-8b",
        "ROUTER_MODEL_LARGE": "qwen2.5-14b-instruct-1m",
    },
    "mcp-git": {"GIT_REPO_PATH": "/repo", "GIT_DEFAULT_BRANCH": "main", "GIT_ALLOW_FORCE_PUSH": "false"},
    "mcp-code-quality": {
        "CQ_PROJECT_PATH": "/repo",
        "CQ_LINTER_CMD": "uv run ruff check",
        "CQ_FORMATTER_CMD": "uv run ruff format",
        "CQ_TEST_CMD": "uv run pytest",
    },
    "mcp-architecture": {"ARCH_PROJECT_PATH": "/repo"},
    "mcp-event-driven": {"EVENT_SCHEMAS_PATH": "/schemas"},
    "mcp-orchestrator": {"ORCH_DAGS_PATH": "/dags"},
    "mcp-best-practices": {"BP_PROJECT_PATH": "/repo", "BP_DOCS_PATH": "/repo/docs"},
    "mcp-ci-cd": {"CICD_PROJECT_PATH": "/repo"},
    "mcp-design-patterns": {"DP_PROJECT_PATH": "/repo"},
    "mcp-security-champion": {"SEC_PROJECT_PATH": "/repo"},
    "mcp-database": {"DATABASE_URL": "sqlite:////data/database.db", "DATABASE_READ_ONLY": "true"},
    "mcp-filesystem": {"FILESYSTEM_ROOT": "/data", "FILESYSTEM_ALLOW_WRITE": "false"},
    "mcp-object-storage": {"OBJECT_STORAGE_ALLOW_WRITE": "false"},
    "mcp-openapi": {"OPENAPI_SPEC": "/data/openapi.yaml", "OPENAPI_ALLOWED_ROOT": "/data", "OPENAPI_ALLOW_INVOKE": "false"},
    "mcp-documents": {"DOCUMENTS_ROOT": "/data"},
    "mcp-browser": {"BROWSER_HEADLESS": "true", "BROWSER_OUTPUT_DIR": "/data/browser"},
    "mcp-kubernetes": {"KUBERNETES_ALLOW_WRITE": "false"},
    "mcp-terraform": {"TERRAFORM_ROOT": "/workspace", "TERRAFORM_ALLOW_APPLY": "false"},
    "mcp-snyk": {"SNYK_PROJECT_PATH": "/repo"},
    "mcp-sonar": {"SONAR_PROJECT_PATH": "/repo"},
    "mcp-java-build": {"JAVA_PROJECT_PATH": "/repo"},
    "mcp-agent-runner": {
        "AGENT_PROJECT_PATH": "/repo",
        "AGENT_N8N_WEBHOOK_BASE_URL": "http://localhost:5678/webhook",
    },
    "mcp-personal-vault": {
        "PERSONAL_VAULT_DATABASE_PATH": "/vault/personal.db",
        "PERSONAL_VAULT_KEY_FILE": "/vault/vault.key",
        "PERSONAL_VAULT_ALLOW_WRITE": "true",
        "PERSONAL_VAULT_ALLOW_HIGHLY_SENSITIVE": "false",
        "PERSONAL_VAULT_ALLOW_SECRETS": "false",
    },
}

LOCAL_ENV_OVERRIDES = {
    "mcp-tabular": {"TABULAR_ALLOWED_ROOT": LOCAL_BASE},
    "mcp-markdown": {"MCP_MARKDOWN_ALLOWED_ROOT": LOCAL_BASE},
    "mcp-project-memory": {
        "MEMORY_MEMORY_DIR": f"{LOCAL_BASE}/.ai-memory",
        "MEMORY_MEMORY_FILE": "project_memory.json",
        "MEMORY_PROJECT_NAME": "mcps",
        "MEMORY_PROJECT_ROOT": LOCAL_BASE,
        "MEMORY_AUTO_SYNC": "false",
    },
    "mcp-llm-router": {
        "ROUTER_LMSTUDIO_BASE_URL": "http://localhost:1234/v1",
        "ROUTER_COMPLEXITY_THRESHOLD": "6",
        "ROUTER_MAX_LOCAL_TOKENS": "6000",
        "ROUTER_MODEL_FAST": "qwen3-8b",
        "ROUTER_MODEL_CODE": "devstral-small-2507",
        "ROUTER_MODEL_REASON": "deepseek-r1-0528-qwen3-8b",
        "ROUTER_MODEL_LARGE": "qwen2.5-14b-instruct-1m",
        "ROUTER_CLOUD_PROVIDER": "anthropic",
        "ROUTER_CLOUD_MODEL": "claude-sonnet-4-5",
    },
    "mcp-git": {
        "GIT_REPO_PATH": LOCAL_BASE,
        "GIT_DEFAULT_BRANCH": "main",
        "GIT_ALLOW_FORCE_PUSH": "false",
    },
    "mcp-code-quality": {
        "CQ_PROJECT_PATH": LOCAL_BASE,
        "CQ_LINTER_CMD": "uv run ruff check",
        "CQ_FORMATTER_CMD": "uv run ruff format",
        "CQ_TEST_CMD": "uv run pytest",
    },
    "mcp-architecture": {"ARCH_PROJECT_PATH": LOCAL_BASE},
    "mcp-event-driven": {"EVENT_SCHEMAS_PATH": f"{LOCAL_BASE}/schemas"},
    "mcp-orchestrator": {"ORCH_DAGS_PATH": f"{LOCAL_BASE}/dags"},
    "mcp-best-practices": {
        "BP_PROJECT_PATH": LOCAL_BASE,
        "BP_DOCS_PATH": f"{LOCAL_BASE}/docs",
    },
    "mcp-ci-cd": {"CICD_PROJECT_PATH": LOCAL_BASE},
    "mcp-design-patterns": {"DP_PROJECT_PATH": LOCAL_BASE},
    "mcp-security-champion": {"SEC_PROJECT_PATH": LOCAL_BASE},
    "mcp-database": {
        "DATABASE_URL": f"sqlite:///{LOCAL_BASE}/data/database.db",
        "DATABASE_READ_ONLY": "true",
    },
    "mcp-filesystem": {
        "FILESYSTEM_ROOT": LOCAL_BASE,
        "FILESYSTEM_ALLOW_WRITE": "false",
    },
    "mcp-object-storage": {
        "OBJECT_STORAGE_REGION": "us-east-1",
        "OBJECT_STORAGE_ALLOW_WRITE": "false",
    },
    "mcp-openapi": {
        "OPENAPI_ALLOWED_ROOT": LOCAL_BASE,
        "OPENAPI_ALLOW_INVOKE": "false",
    },
    "mcp-documents": {"DOCUMENTS_ROOT": LOCAL_BASE},
    "mcp-browser": {
        "BROWSER_HEADLESS": "true",
        "BROWSER_OUTPUT_DIR": f"{LOCAL_BASE}/data/browser",
    },
    "mcp-kubernetes": {
        "KUBERNETES_NAMESPACE": "default",
        "KUBERNETES_ALLOW_WRITE": "false",
    },
    "mcp-observability": {
        "OBSERVABILITY_PROMETHEUS_URL": "http://localhost:9090",
        "OBSERVABILITY_LOKI_URL": "http://localhost:3100",
    },
    "mcp-terraform": {
        "TERRAFORM_ROOT": LOCAL_BASE,
        "TERRAFORM_ALLOW_APPLY": "false",
    },
    "mcp-snyk": {"SNYK_PROJECT_PATH": LOCAL_BASE},
    "mcp-sonar": {
        "SONAR_PROJECT_PATH": LOCAL_BASE,
        "SONAR_HOST_URL": "http://localhost:9000",
    },
    "mcp-java-build": {"JAVA_PROJECT_PATH": LOCAL_BASE},
    "mcp-agent-runner": {
        "AGENT_PROJECT_PATH": LOCAL_BASE,
        "AGENT_N8N_WEBHOOK_BASE_URL": "http://localhost:5678/webhook",
    },
    "mcp-personal-vault": {
        "PERSONAL_VAULT_DATABASE_PATH": f"{LOCAL_BASE}/data/personal-vault/personal.db",
        "PERSONAL_VAULT_KEY_FILE": f"{LOCAL_BASE}/data/personal-vault/vault.key",
        "PERSONAL_VAULT_ALLOW_WRITE": "true",
        "PERSONAL_VAULT_ALLOW_HIGHLY_SENSITIVE": "false",
        "PERSONAL_VAULT_ALLOW_SECRETS": "false",
    },
    "mcp-kafka": {"MCP_KAFKA_BOOTSTRAP_SERVERS": "localhost:9092"},
    "mcp-structured-output": {"MCP_SO_AWS_REGION": "us-east-1"},
    "mcp-github": {
        "GITHUB_API_URL": "https://api.github.com",
        "GITHUB_OWNER": "inggerman",
        "GITHUB_REPO": "mcps",
    },
    "mcp-calendar": {"DEFAULT_COUNTRY": "MX"},
}

GROUPS = {
    "Datos": ["mcp-tabular", "mcp-calendar", "mcp-markdown", "mcp-database", "mcp-filesystem", "mcp-object-storage", "mcp-documents"],
    "APIs": ["mcp-fetch", "mcp-openapi", "mcp-browser", "mcp-kafka", "mcp-github"],
    "IA": ["mcp-structured-output", "mcp-llm-router", "mcp-project-memory", "mcp-prompt-engineer"],
    "Ingeniería": ["mcp-git", "mcp-code-quality", "mcp-architecture", "mcp-design-patterns", "mcp-security-champion"],
    "Flujos": ["mcp-event-driven", "mcp-orchestrator", "mcp-best-practices", "mcp-ci-cd", "mcp-agent-runner"],
    "Plataforma": ["mcp-docker", "mcp-kubernetes", "mcp-observability", "mcp-terraform", "mcp-snyk", "mcp-sonar", "mcp-java-build"],
    "Personal": ["mcp-personal-vault"],
}


def load_inventory() -> dict:
    return json.loads(INVENTORY_FILE.read_text(encoding="utf-8"))


def specific_env_vars(inv: dict, name: str) -> list[dict]:
    return [ev for ev in inv[name]["env_vars"] if ev["field"] not in BASE_FIELDS]


def build_claude_config(inv: dict) -> dict:
    servers = {}
    for name in PORT_ORDER:
        pkg = name.replace("-", "_")
        env = {"LOG_LEVEL": "INFO", "LOG_FORMAT": "console"}
        env.update(LOCAL_ENV_OVERRIDES.get(name, {}))
        servers[name] = {
            "command": "uv",
            "args": [
                "--directory",
                f"{LOCAL_BASE}/{name}",
                "run",
                "python",
                "-m",
                f"{pkg}.server",
            ],
            "env": env,
        }
    return {"mcpServers": servers}


def build_docker_compose(inv: dict) -> str:
    header = [
        "# =============================================================================",
        "# MCP Framework — docker-compose (HTTP / Streamable-HTTP mode)",
        "#",
        "# Todos los servidores corren con MCP_TRANSPORT=streamable-http y exponen",
        "# un puerto HTTP. Para uso local con stdio (Claude Desktop / Cursor) usa",
        "# `uv run python -m mcp_X.server` directamente o `docker run --rm -i`.",
        "#",
        "# Puertos:",
    ]
    for name in PORT_ORDER:
        header.append(f"#   {PORTS[name]} — {name}")
    header.extend([
        "# =============================================================================",
        "",
        "services:",
        "",
    ])
    lines = header[:]

    for name in PORT_ORDER:
        port = PORTS[name]
        short = name.replace("mcp-", "")
        meta = META[name]
        lines.extend([
            f"  # ---------------------------------------------------------------------------",
            f"  # MCP: {meta['title']} ({name})",
            f"  # ---------------------------------------------------------------------------",
            f"  {name}:",
        ])
        if name in PROFILES:
            lines.append(f"    profiles: [\"{PROFILES[name]}\"]")
        lines.extend([
            "    build:",
            "      context: .",
            f"      dockerfile: {name}/Dockerfile",
            "      target: runtime",
            f"    image: {name}:latest",
            f"    container_name: {name}",
            "    restart: unless-stopped",
            "    env_file:",
            "      - path: .env",
            "        required: false",
            "    environment:",
            "      MCP_TRANSPORT: streamable-http",
            '      MCP_HOST: "0.0.0.0"',
            f'      MCP_PORT: "{port}"',
        ])
        for k, v in EXTRA_ENV.get(name, {}).items():
            # Quote string values to avoid YAML interpreting booleans/numbers
            val = f'"{v}"' if isinstance(v, str) else v
            lines.append(f"      {k}: {val}")
        lines.extend([
            "    ports:",
            f'      - "127.0.0.1:{port}:{port}"',
        ])
        vols = VOLUMES.get(name, [])
        if vols:
            lines.append("    volumes:")
            for src, dst, mode in vols:
                suffix = f":{mode}" if mode else ""
                lines.append(f'      - {src}:{dst}{suffix}')
        if name == "mcp-llm-router":
            lines.append("    extra_hosts:")
            lines.append('      - "host.docker.internal:host-gateway"')
        start_period = "30s" if name == "mcp-browser" else "15s"
        lines.extend([
            "    healthcheck:",
            f'      test: ["CMD", "python", "-c", "import socket; socket.create_connection((\'localhost\', {port}), timeout=5)"]',
            "      interval: 30s",
            "      timeout: 10s",
            "      retries: 3",
            f"      start_period: {start_period}",
            "    labels:",
            f'      - "mcp.server={short}"',
            '      - "mcp.version=1.0.0"',
            '      - "mcp.transport=streamable-http"',
            "",
        ])

    lines.extend([
        "# ---------------------------------------------------------------------------",
        "# Volumes",
        "# ---------------------------------------------------------------------------",
        "volumes:",
        "  mcp-data:",
        "    driver: local",
        "    driver_opts:",
        "      type: none",
        "      o: bind",
        "      device: ${MCP_DATA_DIR:-./data}",
        "  mcp-memory:",
        "    driver: local",
        "    driver_opts:",
        "      type: none",
        "      o: bind",
        "      device: ${MCP_MEMORY_DIR:-./.ai-memory}",
        "  mcp-personal-vault:",
        "    driver: local",
        "    driver_opts:",
        "      type: none",
        "      o: bind",
        "      device: ${PERSONAL_VAULT_DIR:-./data/personal-vault}",
        "",
    ])
    return "\n".join(lines)


def build_env_example(inv: dict) -> str:
    lines = [
        "# =============================================================================",
        "# MCP Framework — Environment Variables",
        "# Copia este archivo a .env y llena los valores",
        "# =============================================================================",
        "",
        "# --- Globales (todos los servidores) ---",
        "LOG_LEVEL=INFO                   # DEBUG | INFO | WARNING | ERROR",
        "LOG_FORMAT=json                  # json (prod) | console (dev)",
        "MCP_TRANSPORT=stdio              # stdio (local) | streamable-http (Docker)",
        "MCP_HOST=0.0.0.0                 # Host HTTP (solo streamable-http)",
        "MCP_PORT=8000                    # Puerto base; docker-compose asigna uno por servidor",
        "MCP_DEBUG=false                  # Modo debug del servidor MCP",
        "MCP_WORKERS=1                    # Número de workers HTTP",
        "MCP_DATA_DIR=./data              # Directorio de datos montado en Docker",
        "MCP_MEMORY_DIR=./.ai-memory      # Directorio de memoria de proyecto",
        "PERSONAL_VAULT_DIR=./data/personal-vault  # Directorio de la bóveda personal",
        "",
        "# --- Divisas (mcp-calendar) ---",
        "EXCHANGE_RATE_API_KEY=           # ExchangeRate-API.com key (opcional)",
        "EXCHANGE_RATE_PROVIDER=frankfurter  # frankfurter | exchangerate-api",
        "DEFAULT_COUNTRY=MX               # País por defecto para días hábiles",
        "EXCHANGE_CACHE_TTL_SECONDS=3600  # TTL del caché de tasas",
        "",
        "# --- OCR (mcp-documents) ---",
        "TESSERACT_CMD=tesseract          # Path al binario tesseract",
        "",
    ]

    for group, names in GROUPS.items():
        lines.append(f"# --- {group} ---")
        for name in names:
            for ev in specific_env_vars(inv, name):
                var = ev["var"]
                default = ev["default"]
                desc = ev["description"] or f"Variable {var}"
                if not default:
                    lines.append(f"#{var}=  # {desc}")
                else:
                    if isinstance(default, str) and (" " in default or '"' in default or "'" in default):
                        default = f'"{default}"'
                    lines.append(f"{var}={default}  # {desc}")
        lines.append("")

    lines.extend([
        "# =============================================================================",
        "# Credenciales y secretos (no versionar; usar secret manager en producción)",
        "# =============================================================================",
        "GITHUB_TOKEN=  # PAT de GitHub con permisos de repo",
        "SNYK_API_TOKEN=",
        "SONAR_API_TOKEN=",
        "ROUTER_CLOUD_API_KEY=  # Requerido para ruteo a la nube",
        "MCP_SO_OPENAI_API_KEY=",
        "MCP_SO_AWS_PROFILE=",
        "PERSONAL_VAULT_ENCRYPTION_KEY=  # Fernet key (generar en producción)",
        "AWS_ACCESS_KEY_ID=",
        "AWS_SECRET_ACCESS_KEY=",
        "AWS_SESSION_TOKEN=",
        "",
    ])
    return "\n".join(lines)


def build_servers_reference(inv: dict) -> str:
    lines = ["# Servers Reference"]
    now = datetime.now(timezone.utc).isoformat()
    lines.append(f"**Última actualización:** {now}")
    lines.append("")
    lines.append("Documentación autogenerada con la lista de tools y variables de entorno de cada servidor MCP.")
    lines.append("")
    for name in PORT_ORDER:
        meta = META[name]
        port = PORTS[name]
        pkg = name.replace("-", "_")
        lines.extend([
            f"## {name}",
            f"- **Título:** {meta['title']}",
            f"- **Grupo:** {meta['group']}",
            f"- **Puerto Docker:** {port}",
            f"- **Comando local:** `uv --directory {LOCAL_BASE}/{name} run python -m {pkg}.server`",
            "",
            "### Tools",
            "",
            "| Tool | Descripción |",
            "|------|-------------|",
        ])
        for tool in inv[name]["tools"]:
            desc = tool["description"] or "Sin descripción."
            lines.append(f"| `{tool['name']}` | {desc} |")
        lines.extend([
            "",
            "### Variables de entorno",
            "",
            "| Variable | Default | Descripción |",
            "|----------|---------|-------------|",
        ])
        for ev in specific_env_vars(inv, name):
            default = ev["default"] or "—"
            desc = ev["description"] or "—"
            lines.append(f"| `{ev['var']}` | {default} | {desc} |")
        lines.append("")
    return "\n".join(lines)


def build_project_state(inv: dict) -> str:
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Project State",
        f"**Última actualización:** {now}",
        "**Versión global:** 1.0.0",
        "",
        "## Resumen",
        "Este documento mantiene el estado actual del proyecto de forma retroactiva. Debe ser consultado al inicio de cualquier conversación para entender el contexto.",
        "",
        f"## Servidores MCP Activos ({len(PORT_ORDER)})",
    ]
    for name in PORT_ORDER:
        meta = META[name]
        lines.append(f"- `{name}` — {meta['title']} ({meta['group']})")
    lines.extend([
        "",
        "## Grupos",
        "",
    ])
    groups = {}
    for name in PORT_ORDER:
        groups.setdefault(META[name]["group"], []).append(name)
    for group, names in groups.items():
        lines.append(f"- **{group}:** " + ", ".join(f"`{n}`" for n in names))
    lines.extend([
        "",
        "## Reglas Generales",
        "- Todos los servidores usan `FastMCP` v2.",
        "- Comparten lógica mediante el paquete `mcp-shared`.",
        "- Soportan transporte `stdio` (local) y `streamable-http` (Docker/producción).",
        "- Pruebas ejecutadas con `pytest` y empaquetado manejado por `uv`.",
        "- Configuración por servidor centralizada en `config.py` con `pydantic-settings`.",
        "",
    ])
    return "\n".join(lines)


def build_readme_catalog(inv: dict) -> str:
    blocks = []
    for name in PORT_ORDER:
        meta = META[name]
        blocks.append(f"### `{name}` — {meta['title']}")
        blocks.append("")
        blocks.append(meta["desc"])
        blocks.append("")
        blocks.append("| Tool | Qué hace |")
        blocks.append("|------|----------|")
        for tool in inv[name]["tools"]:
            desc = tool["description"] or "Sin descripción."
            blocks.append(f"| `{tool['name']}` | {desc} |")
        blocks.append("")
        blocks.append(f"**Caso de uso típico:** {meta['use']}")
        blocks.append("")
        blocks.append("---")
        blocks.append("")
    return "\n".join(blocks)


def build_readme_architecture_tree() -> str:
    lines = [
        "mcps/                              ← raíz del workspace uv",
        "│",
        "├── shared/                        ← librería compartida (se instala como paquete)",
        "│   └── src/mcp_shared/",
        "│       ├── config.py              ← BaseMcpSettings (base de configuración)",
        "│       ├── errors.py              ← jerarquía de errores tipados",
        "│       ├── logging.py             ← setup_logging() con structlog",
        "│       └── models.py              ← modelos Pydantic reutilizables",
        "│",
    ]
    for name in PORT_ORDER:
        title = META[name]["title"]
        lines.append(f"├── {name}/{' ' * (25 - len(name))}← {title}")
    lines.extend([
        "│",
        "├── docker-compose.yml             ← orquestación (modo HTTP / producción)",
        "├── pyproject.toml                 ← workspace root: ruff, mypy, pytest",
        "├── Makefile                       ← comandos operacionales",
        "├── claude_desktop_config.json     ← config para Claude Desktop (modo stdio)",
        "└── .env.example                   ← plantilla de variables de entorno",
    ])
    return "\n".join(lines)


def build_readme_ports_table() -> str:
    lines = ["| Servidor | Puerto | URL |", "|----------|--------|-----|"]
    for name in PORT_ORDER:
        port = PORTS[name]
        lines.append(f"| `{name}` | {port} | `http://127.0.0.1:{port}/` |")
    return "\n".join(lines)


def build_readme_env_table(inv: dict) -> str:
    lines = ["| Variable | Servidor | Descripción |", "|----------|----------|-------------|"]
    for name in PORT_ORDER:
        for ev in specific_env_vars(inv, name):
            desc = ev["description"] or "—"
            lines.append(f"| `{ev['var']}` | `{name}` | {desc} |")
    return "\n".join(lines)


def patch_readme(inv: dict) -> None:
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")

    # Section 3: architecture tree
    tree_start = readme.find("```\nmcps/")
    tree_end = readme.find("```\n\n### Principio de diseño")
    if tree_start != -1 and tree_end != -1:
        tree_end_pos = readme.find("\n```", tree_end) + 4
        new_tree = "```\n" + build_readme_architecture_tree() + "\n```"
        readme = readme[:tree_start] + new_tree + readme[tree_end_pos:]

    # Section 4: catalog
    cat_start = readme.find("## 4. Catálogo de servidores")
    cat_end = readme.find("## 5. Prerrequisitos e instalación")
    if cat_start != -1 and cat_end != -1:
        new_cat = "## 4. Catálogo de servidores\n\n" + build_readme_catalog(inv)
        readme = readme[:cat_start] + new_cat + readme[cat_end:]

    # Section 8: ports table
    ports_start = readme.find("### Puertos expuestos")
    ports_end = readme.find("### Healthcheck")
    if ports_start != -1 and ports_end != -1:
        new_ports = "### Puertos expuestos\n\n" + build_readme_ports_table() + "\n\n"
        readme = readme[:ports_start] + new_ports + readme[ports_end:]

    # Section 11: env vars table
    env_start = readme.find("### Variables específicas por servidor")
    env_end = readme.find("## 12. Referencia de comandos Makefile")
    if env_start != -1 and env_end != -1:
        new_env = "### Variables específicas por servidor\n\n" + build_readme_env_table(inv) + "\n\n---\n\n"
        readme = readme[:env_start] + new_env + readme[env_end:]

    readme_path.write_text(readme, encoding="utf-8")


def main() -> None:
    inv = load_inventory()

    (ROOT / "claude_desktop_config.json").write_text(
        json.dumps(build_claude_config(inv), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (ROOT / "docker-compose.yml").write_text(build_docker_compose(inv), encoding="utf-8")
    (ROOT / ".env.example").write_text(build_env_example(inv), encoding="utf-8")
    (ROOT / "docs" / "servers-reference.md").write_text(build_servers_reference(inv), encoding="utf-8")
    (ROOT / "docs" / "project-state.md").write_text(build_project_state(inv), encoding="utf-8")
    patch_readme(inv)

    print("Documentation files regenerated successfully.")


if __name__ == "__main__":
    main()
