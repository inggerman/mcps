# Resumen de recursos por MCP

**Generado automáticamente desde `.mcp_inventory.json`**.

Para cada servidor se listan: puerto Docker, tools y variables de entorno específicas.

## mcp-agent-runner

- **Tools:** 2
- **Variables de entorno específicas:** 3

### Tools

| Tool | Descripción |
|------|-------------|
| `agent_trigger_webhook` | Dispara un webhook REST HTTP (ej. n8n) enviando un payload en JSON. |
| `agent_run_local_script` | Ejecuta un sub-agente o script Python en local y espera su resultado. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `AGENT_PROJECT_PATH` | — | Ruta base del proyecto. |
| `AGENT_N8N_WEBHOOK_BASE_URL` | http://localhost:5678/webhook | URL base para webhooks de n8n. |
| `AGENT_N8N_AUTH_TOKEN` | — | Token opcional para autenticar webhooks de n8n. |

## mcp-architecture

- **Tools:** 3
- **Variables de entorno específicas:** 1

### Tools

| Tool | Descripción |
|------|-------------|
| `arch_get_project_tree` | Retorna la estructura de carpetas y archivos del proyecto. Útil para entender la arquitectura macro. |
| `arch_analyze_dependencies` | Usa AST para extraer todas las importaciones de un archivo .py y entender su acoplamiento. |
| `arch_check_solid_principles` | Revisa un archivo buscando heurísticas como Clases Gigantes o demasiados argumentos, que violan SOLID. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `ARCH_PROJECT_PATH` | — | Ruta base del proyecto a analizar. |

## mcp-best-practices

- **Tools:** 2
- **Variables de entorno específicas:** 2

### Tools

| Tool | Descripción |
|------|-------------|
| `bp_update_project_state` | Genera o actualiza el archivo docs/project-state.md escaneando la estructura actual del proyecto. |
| `bp_update_servers_reference` | Genera o actualiza docs/servers-reference.md leyendo claude_desktop_config.json de la raíz. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `BP_PROJECT_PATH` | — | Ruta base del proyecto. |
| `BP_DOCS_PATH` | ./docs | Ruta donde se almacenará la documentación retroactiva. |

## mcp-browser

- **Tools:** 2
- **Variables de entorno específicas:** 4

### Tools

| Tool | Descripción |
|------|-------------|
| `browser_extract` |  |
| `browser_screenshot` |  |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `BROWSER_HEADLESS` | true | — |
| `BROWSER_TIMEOUT_MS` | 30000 | — |
| `BROWSER_ALLOWED_HOSTS` | — | — |
| `BROWSER_OUTPUT_DIR` | ./data/browser | — |

## mcp-calendar

- **Tools:** 15
- **Variables de entorno específicas:** 3

### Tools

| Tool | Descripción |
|------|-------------|
| `get_holidays` | Lista todos los feriados de un país para un año dado. Soporta más de 100 países usando ISO 3166-1 alpha-2 (ej: 'MX', 'US', 'DE'). Parámetros: country (código de país), year (año ej: 2025), state (subdivisión opcional ej: 'CDMX', 'CA'). Retorna: lista de feriados con fecha, nombre, país y región. |
| `calculate_business_days` | Calcula los días hábiles entre dos fechas (ambas inclusive). Excluye fines de semana y feriados del país. Parámetros: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), country (ISO alpha-2, por defecto 'MX'). Retorna: business_days, total_days, weekend_days, holidays_excluded, country. |
| `add_business_days` | Suma N días hábiles a una fecha de inicio. Si n_days es negativo, resta días hábiles hacia atrás. La fecha de inicio NO cuenta como día hábil a sumar. Parámetros: start_date (YYYY-MM-DD), n_days (entero, puede ser negativo), country (ISO alpha-2, por defecto 'MX'). Retorna: fecha resultante en formato ISO 8601 (YYYY-MM-DD). |
| `is_business_day` | Verifica si una fecha específica es día hábil en el país dado. Parámetros: check_date (YYYY-MM-DD), country (ISO alpha-2, por defecto 'MX'). Retorna: is_business_day, is_weekend, is_holiday, holiday_name, holiday_description, day_of_week, country. |
| `next_business_day` | Retorna el siguiente día hábil después de la fecha dada. Si la fecha dada ya es hábil, retorna el SIGUIENTE (no el mismo día). Parámetros: check_date (YYYY-MM-DD), country (ISO alpha-2, por defecto 'MX'). Retorna: fecha del siguiente día hábil en formato ISO 8601. |
| `previous_business_day` | Retorna el día hábil anterior a la fecha dada. Si la fecha dada ya es hábil, retorna el ANTERIOR (no el mismo día). Parámetros: check_date (YYYY-MM-DD), country (ISO alpha-2, por defecto 'MX'). Retorna: fecha del día hábil anterior en formato ISO 8601. |
| `business_days_in_month` | Calcula el total de días hábiles en un mes completo. Parámetros: year (ej: 2025), month (1–12), country (ISO alpha-2, por defecto 'MX'). Retorna: year, month, month_name, business_days, total_days, weekend_days, holiday_count, holidays, country. |
| `get_mexico_holidays` | Retorna todos los feriados oficiales de México para el año dado, con descripciones en español de su contexto histórico y cultural. Incluye la base legal (Ley Federal del Trabajo, Art. 74). Parámetro: year (ej: 2025). Retorna: lista de feriados con date, name, description, is_fixed, day_of_week, legal_basis. |
| `get_country_list` | Retorna la lista de todos los países soportados para cálculo de días hábiles. Incluye código ISO alpha-2, nombre del país y subdivisiones disponibles. Útil para validar códigos de país antes de llamar otras herramientas. No requiere parámetros. Retorna: lista con code, name, has_subdivisions, subdivisions. |
| `get_exchange_rate` | Obtiene la tasa de cambio actual entre dos divisas vía Frankfurter API (BCE). Las tasas se actualizan diariamente y se cachean en memoria. Parámetros: from_currency (ISO 4217 ej: 'USD'), to_currency (ISO 4217 ej: 'MXN'), ttl_seconds (TTL del caché, por defecto 3600). Retorna: base_currency, target_currency, rate, timestamp, source. |
| `convert_currency` | Convierte un monto de una divisa a otra usando la tasa de cambio actual. Parámetros: amount (monto a convertir, >=0), from_currency (ISO 4217), to_currency (ISO 4217), ttl_seconds (TTL del caché, por defecto 3600). Retorna: original_amount, converted_amount, rate (tasa utilizada). |
| `get_historical_rate` | Obtiene la tasa de cambio histórica entre dos divisas para una fecha específica. Datos disponibles desde 1999-01-04 (inicio del BCE). Parámetros: from_currency (ISO 4217), to_currency (ISO 4217), rate_date (YYYY-MM-DD, no puede ser fecha futura). Retorna: base_currency, target_currency, rate, timestamp, source. |
| `get_mx_rates` | Obtiene las tasas de cambio entre MXN y las principales monedas mundiales (USD, EUR, GBP, CAD, JPY, CHF, CNY). Parámetros: base (divisa base, por defecto 'MXN'), ttl_seconds (TTL del caché, por defecto 3600). Retorna: base, date, rates (mapa código→rate), source. |
| `list_supported_currencies` | Lista todas las divisas soportadas por Frankfurter API (ISO 4217). Incluye el código y el nombre completo en inglés de cada divisa. No requiere parámetros. Los resultados se cachean 24 horas. Retorna: lista de dicts con 'code' y 'name', ordenados alfabéticamente. |
| `get_rate_history` | Obtiene el historial de tasas de cambio entre dos divisas para un rango de fechas. Solo incluye días hábiles del BCE (no fines de semana ni feriados europeos). Parámetros: from_currency (ISO 4217), to_currency (ISO 4217), start_date (YYYY-MM-DD), end_date (YYYY-MM-DD). Retorna: lista de tasas de cambio diarias ordenadas por fecha ascendente. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DEFAULT_COUNTRY` | MX | Código de país ISO 3166-1 alpha-2 usado por defecto en todas las operaciones de calendario cuando no se especifica explícitamente. Variable de entorno: DEFAULT_COUNTRY. |
| `EXCHANGE_CACHE_TTL_SECONDS` | 3600 | Tiempo de vida del caché de tasas de cambio en segundos. Rango válido: 60–86400 (1 minuto a 24 horas). Variable de entorno: EXCHANGE_CACHE_TTL_SECONDS. |
| `MCP_SERVER_NAME` | mcp-calendar | Nombre identificador del servidor MCP en logs y metadatos. |

## mcp-ci-cd

- **Tools:** 1
- **Variables de entorno específicas:** 4

### Tools

| Tool | Descripción |
|------|-------------|
| `cicd_run_pipeline` | Ejecuta un pipeline local que incluye linting, testing y simulación de despliegue. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CICD_PROJECT_PATH` | — | Ruta base del proyecto. |
| `CICD_TEST_CMD` | uv run pytest | Comando de test. |
| `CICD_LINT_CMD` | uv run ruff check | Comando de lint. |
| `CICD_DEPLOY_CMD` | echo 'Despliegue simulado exitoso' | Comando de despliegue. |

## mcp-code-quality

- **Tools:** 3
- **Variables de entorno específicas:** 4

### Tools

| Tool | Descripción |
|------|-------------|
| `quality_run_lint` | Ejecuta el linter sobre el proyecto. Puedes especificar un archivo/carpeta con 'target'. |
| `quality_run_format` | Ejecuta el formateador de código. Usa check_only=True para ver qué cambiaría sin modificar. |
| `quality_run_tests` | Ejecuta los tests unitarios. Puedes pasar un archivo de tests específico con 'target'. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CQ_PROJECT_PATH` | — | Ruta base del proyecto a analizar. |
| `CQ_LINTER_CMD` | uv run ruff check | Comando usado para linting de código. |
| `CQ_FORMATTER_CMD` | uv run ruff format | Comando usado para formateo de código. |
| `CQ_TEST_CMD` | uv run pytest | Comando usado para correr tests unitarios. |

## mcp-database

- **Tools:** 4
- **Variables de entorno específicas:** 4

### Tools

| Tool | Descripción |
|------|-------------|
| `database_info` |  |
| `database_list_tables` |  |
| `database_describe_table` |  |
| `database_query` |  |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | sqlite:///./data/database.db | — |
| `DATABASE_READ_ONLY` | true | — |
| `DATABASE_MAX_ROWS` | 500 | — |
| `DATABASE_STATEMENT_TIMEOUT_SECONDS` | 30 | — |

## mcp-design-patterns

- **Tools:** 2
- **Variables de entorno específicas:** 1

### Tools

| Tool | Descripción |
|------|-------------|
| `dp_analyze_code_patterns` | Analiza un archivo Python (.py) para detectar posibles antipatrones como God Objects o Long Methods. |
| `dp_suggest_pattern` | Sugiere un patrón de diseño (GoF) basado en la descripción del problema de software a resolver. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DP_PROJECT_PATH` | — | Ruta base del proyecto. |

## mcp-docker

- **Tools:** 8
- **Variables de entorno específicas:** 3

### Tools

| Tool | Descripción |
|------|-------------|
| `containers_list` | Lista contenedores Docker. Parámetros: all_containers (bool, default false = solo running), filters (dict opcional, ej: {"name": "web", "status": "running"}). Retorna: containers[], count, showing. |
| `containers_stats` | Estadísticas de recursos de un contenedor: CPU %, memoria MB, red, disco. Parámetros: container_id (ID o nombre, requerido). Retorna: cpu_percent, memory_mb, memory_limit_mb, memory_percent, net_rx_mb, net_tx_mb, block_read_mb, block_write_mb. |
| `container_logs` | Obtiene los logs de un contenedor. Parámetros: container_id (requerido), lines (int, default 100), since (str opcional, ej: '1h', '30m', '2024-01-01T10:00:00'), timestamps (bool, default false). Retorna: logs (texto), container_id, container_name, lines_requested, status. |
| `container_exec` | Ejecuta un comando dentro de un contenedor en ejecución (debe estar running). Parámetros: container_id (requerido), command (string, requerido), workdir (string opcional), user (string opcional, ej: 'root'), environment (dict opcional). Retorna: exit_code, output, success, container_id, command. |
| `run_container` | Crea y arranca un contenedor Docker. Parámetros: image (requerido, ej: 'nginx:latest'), command (string opcional), name (string opcional), detach (bool, default true = background), ports (dict container→host, ej: {'80': '8080'}), environment (dict), volumes (dict host_path→container_path), remove_on_exit (bool, default false). Retorna: id, name, status, image, ports. |
| `stop_container` | Detiene un contenedor Docker en ejecución. Parámetros: container_id (ID o nombre, requerido), timeout (int segundos antes de SIGKILL, default 10), remove (bool, si True elimina tras detener, default false). Retorna: container_id, name, action, removed. |
| `images_list` | Lista imágenes Docker locales. Parámetros: name (string opcional, filtrar por nombre/tag), dangling (bool, incluir imágenes sin tag, default false). Retorna: images[], count. |
| `image_pull` | Descarga una imagen Docker desde un registry (Docker Hub, ECR, GHCR, etc.). Parámetros: image (requerido, ej: 'nginx', 'python', 'my-registry/app'), tag (string, default 'latest'). Retorna: image, tag, id, tags[], size_mb. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_DOCKER_DOCKER_HOST` | — | URL del daemon Docker. None = usa DOCKER_HOST del entorno o socket por defecto. Variable: MCP_DOCKER_DOCKER_HOST. Ej: unix:///var/run/docker.sock o tcp://host:2376 |
| `MCP_DOCKER_LOG_LINES` | 100 | Número de líneas de logs a retornar por defecto. Variable: MCP_DOCKER_LOG_LINES. |
| `MCP_DOCKER_EXEC_TIMEOUT` | 30 | Timeout en segundos para exec en contenedor. Variable: MCP_DOCKER_EXEC_TIMEOUT. |

## mcp-documents

- **Tools:** 2
- **Variables de entorno específicas:** 3

### Tools

| Tool | Descripción |
|------|-------------|
| `documents_extract` |  |
| `documents_metadata` |  |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DOCUMENTS_ROOT` | . | — |
| `DOCUMENTS_MAX_FILE_SIZE_MB` | 50 | — |
| `DOCUMENTS_MAX_PAGES` | 200 | — |

## mcp-event-driven

- **Tools:** 3
- **Variables de entorno específicas:** 1

### Tools

| Tool | Descripción |
|------|-------------|
| `event_parse_schema` | Parsea un esquema de evento (JSON Schema o AsyncAPI) para extraer metadata y propiedades. |
| `event_analyze_choreography` | Escanea el directorio de esquemas configurado para encontrar todos los eventos registrados. |
| `event_generate_mock_payload` | Genera un payload JSON simulado para un evento, dado un arreglo de sus propiedades. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `EVENT_SCHEMAS_PATH` | ./schemas | Ruta donde se almacenan los esquemas de eventos. |

## mcp-fetch

- **Tools:** 4
- **Variables de entorno específicas:** 6

### Tools

| Tool | Descripción |
|------|-------------|
| `fetch_url` | Realiza un GET HTTP y devuelve el contenido crudo + metadatos. Parámetros: url (requerido), headers (dict opcional), timeout (segundos, default 30), max_bytes (default 5MB). Retorna: url, status_code, content_type, content, truncated, headers, elapsed_ms. |
| `fetch_post` | Realiza un POST HTTP con cuerpo JSON o form-data. Parámetros: url (requerido), json_body (dict para application/json), form_data (dict para form-urlencoded), headers, timeout, max_bytes. Solo uno de json_body o form_data puede estar presente. Retorna: url, status_code, content_type, content, truncated, headers, elapsed_ms. |
| `extract_text` | Descarga una página HTML y extrae el texto limpio (sin tags HTML, scripts ni estilos). Ideal para leer documentación: Spring Boot docs, Kafka docs, Kubernetes docs, Terraform registry, Javadoc, Stack Overflow, artículos, etc. Parámetros: url (requerido), headers, timeout, include_links (bool, default false), include_title (bool, default true). Retorna: url, title, text, word_count, links (si include_links=true), status_code. |
| `fetch_json` | Descarga una URL y parsea la respuesta como JSON. Opcionalmente navega el resultado con un path tipo 'data.items[0].name'. Ideal para consultar APIs REST: GitHub API, Docker Hub API, Kubernetes API, Terraform Cloud API, Kafka REST Proxy, Spring Boot Actuator, etc. Parámetros: url (requerido), headers, timeout, jq_path (string opcional, notación punto+índice). Retorna: url, data (JSON completo o sub-valor), status_code, path_used. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_FETCH_DEFAULT_TIMEOUT` | 30.0 | Timeout en segundos para peticiones HTTP. Variable: MCP_FETCH_DEFAULT_TIMEOUT. |
| `MCP_FETCH_MAX_CONTENT_LENGTH` | 5242880 | Tamaño máximo de respuesta en bytes (default 5 MB). Variable: MCP_FETCH_MAX_CONTENT_LENGTH. |
| `MCP_FETCH_USER_AGENT` | mcp-fetch/1.0 (MCP HTTP client) | User-Agent enviado en peticiones. Variable: MCP_FETCH_USER_AGENT. |
| `MCP_FETCH_FOLLOW_REDIRECTS` | false | Seguir redirecciones HTTP. Desactivado por defecto para reducir riesgo SSRF. Variable: MCP_FETCH_FOLLOW_REDIRECTS. |
| `MCP_FETCH_ALLOW_PRIVATE_NETWORKS` | false | Permitir destinos loopback, privados, link-local o reservados. Variable: MCP_FETCH_ALLOW_PRIVATE_NETWORKS. |
| `MCP_FETCH_VERIFY_SSL` | true | Verificar certificados SSL. Variable: MCP_FETCH_VERIFY_SSL. |

## mcp-filesystem

- **Tools:** 4
- **Variables de entorno específicas:** 4

### Tools

| Tool | Descripción |
|------|-------------|
| `filesystem_list` |  |
| `filesystem_read_text` |  |
| `filesystem_search` |  |
| `filesystem_write_text` |  |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `FILESYSTEM_ROOT` | . | — |
| `FILESYSTEM_ALLOW_WRITE` | false | — |
| `FILESYSTEM_MAX_READ_BYTES` | 2097152 | — |
| `FILESYSTEM_MAX_RESULTS` | 500 | — |

## mcp-git

- **Tools:** 10
- **Variables de entorno específicas:** 3

### Tools

| Tool | Descripción |
|------|-------------|
| `get_git_status` | Retorna el estado de git: branch actual, cambios sin trackear y en stage. |
| `get_git_diff` | Retorna el diff de cambios. Parámetros: staged (bool), file_path (str opcional). |
| `get_git_log` | Retorna el historial reciente. Parámetro: max_count (int, default 10). |
| `git_add` | Agrega archivos al stage. Parámetro: files (lista de strings, o ['.'] para todos). |
| `git_reset` | Quita archivos del stage (unstage). Si no se proveen files, quita todos. |
| `git_branch` | Cambia de rama (checkout). Usa create=True para crearla (-b). |
| `prepare_commit` | PASO 1 de commit: Prepara el commit con el mensaje dado, revisa qué hay en el stage y genera un TOKEN. DEBES pedir autorización al usuario mostrando el diff antes de usar confirm_commit. |
| `confirm_commit` | PASO 2 de commit: Aplica el commit previamente preparado usando el TOKEN devuelto por prepare_commit. SOLO USAR si el usuario aprobó el diff. |
| `git_pull` | Descarga e integra cambios remotos en la rama actual (git pull). |
| `git_push` | Sube los commits locales al repositorio remoto. Para --force usa force=True. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GIT_REPO_PATH` | — | Ruta al repositorio Git sobre el que operará el servidor. Variable de entorno: GIT_REPO_PATH. |
| `GIT_DEFAULT_BRANCH` | main | Nombre de la rama principal por defecto. Variable de entorno: GIT_DEFAULT_BRANCH. |
| `GIT_ALLOW_FORCE_PUSH` | false | Si es true, permite al agente usar push --force (peligroso). Variable de entorno: GIT_ALLOW_FORCE_PUSH. |

## mcp-github

- **Tools:** 5
- **Variables de entorno específicas:** 5

### Tools

| Tool | Descripción |
|------|-------------|
| `github_create_issue` | Crea un issue en GitHub. Parámetros owner y repo son obligatorios si no están en .env. |
| `github_get_issue` | Obtiene información detallada de un issue por su número. |
| `github_create_pull_request` | Crea un Pull Request de la rama 'head' a 'base'. |
| `github_get_pull_request_diff` | Obtiene el diff completo de un Pull Request. |
| `github_add_issue_comment` | Agrega un comentario a un issue o Pull Request. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `GITHUB_TOKEN` | — | Personal Access Token (PAT) de GitHub para autenticación. Requerido para la mayoría de operaciones. Variable de entorno: GITHUB_TOKEN. |
| `GITHUB_OWNER` | — | Usuario u organización propietaria del repositorio. Variable de entorno: GITHUB_OWNER. |
| `GITHUB_REPO` | — | Nombre del repositorio objetivo principal. Variable de entorno: GITHUB_REPO. |
| `GITHUB_API_URL` | https://api.github.com | URL base de la API de GitHub. Útil para GitHub Enterprise Server. Variable de entorno: GITHUB_API_URL. |
| `GITHUB_TIMEOUT_SECONDS` | 30 | Timeout para peticiones a la API en segundos. |

## mcp-java-build

- **Tools:** 2
- **Variables de entorno específicas:** 1

### Tools

| Tool | Descripción |
|------|-------------|
| `java_mvn` | Ejecuta un comando Maven en el proyecto. Provee los argumentos (ej. 'clean install'). |
| `java_gradle` | Ejecuta un comando Gradle en el proyecto. Provee los argumentos (ej. 'build'). |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `JAVA_PROJECT_PATH` | — | Ruta base del proyecto Java. |

## mcp-kafka

- **Tools:** 6
- **Variables de entorno específicas:** 9

### Tools

| Tool | Descripción |
|------|-------------|
| `topics_list` | Lista todos los topics del cluster Kafka. Parámetros: prefix (string opcional, filtrar por prefijo), exclude_internal (bool, default true, excluye topics __). Retorna: topics[], count, cluster_id, broker_count. |
| `topic_describe` | Describe un topic Kafka: particiones, líder, réplicas e ISR. Parámetros: topic (requerido). Retorna: topic, partition_count, replication_factor, partitions[]. |
| `consumer_groups_list` | Lista todos los consumer groups del cluster Kafka. Parámetros: prefix (string opcional, filtrar por prefijo). Retorna: groups[], count, errors[]. |
| `consumer_group_offsets` | Obtiene los offsets actuales de un consumer group. Parámetros: group_id (requerido), topics (list de strings opcional). Retorna: group_id, offsets[] (topic, partition, offset), partition_count. |
| `produce_message` | Produce un mensaje en un topic Kafka. Parámetros: topic (requerido), value (string o dict → se serializa como JSON), key (string opcional), partition (int opcional), headers (dict opcional). Retorna: topic, partition, offset, timestamp_ms, key, value_size_bytes. |
| `consume_messages` | Consume mensajes de un topic Kafka. Parámetros: topic (requerido), group_id (default 'mcp-kafka-consumer'), max_messages (int, default 50), from_beginning (bool, default false), timeout (float segundos, default 5), parse_json (bool, default true). Retorna: topic, group_id, messages[] (partition, offset, key, value, timestamp_ms, headers), count. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_KAFKA_BOOTSTRAP_SERVERS` | localhost:9092 | Brokers Kafka (comma-separated). Variable: MCP_KAFKA_BOOTSTRAP_SERVERS. Ej: localhost:9092 o broker1:9092,broker2:9092 |
| `MCP_KAFKA_SECURITY_PROTOCOL` | PLAINTEXT | Protocolo de seguridad: PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL. Variable: MCP_KAFKA_SECURITY_PROTOCOL. |
| `MCP_KAFKA_SASL_MECHANISM` | — | Mecanismo SASL: PLAIN, SCRAM-SHA-256, SCRAM-SHA-512. Variable: MCP_KAFKA_SASL_MECHANISM. |
| `MCP_KAFKA_SASL_USERNAME` | — | Usuario SASL. Variable: MCP_KAFKA_SASL_USERNAME. |
| `MCP_KAFKA_SASL_PASSWORD` | — | Contraseña SASL. Variable: MCP_KAFKA_SASL_PASSWORD. |
| `MCP_KAFKA_SSL_CA_LOCATION` | — | Ruta al CA certificate para SSL. Variable: MCP_KAFKA_SSL_CA_LOCATION. |
| `MCP_KAFKA_CONSUME_TIMEOUT` | 5.0 | Timeout en segundos para consumir mensajes. Variable: MCP_KAFKA_CONSUME_TIMEOUT. |
| `MCP_KAFKA_MAX_CONSUME_MESSAGES` | 50 | Número máximo de mensajes a consumir por llamada. Variable: MCP_KAFKA_MAX_CONSUME_MESSAGES. |
| `MCP_KAFKA_ADMIN_TIMEOUT` | 10.0 | Timeout en segundos para operaciones admin (list topics, etc.). Variable: MCP_KAFKA_ADMIN_TIMEOUT. |

## mcp-kubernetes

- **Tools:** 5
- **Variables de entorno específicas:** 5

### Tools

| Tool | Descripción |
|------|-------------|
| `kubernetes_list_namespaces` |  |
| `kubernetes_list_pods` |  |
| `kubernetes_list_deployments` |  |
| `kubernetes_pod_logs` |  |
| `kubernetes_scale_deployment` |  |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `KUBERNETES_CONTEXT` | — | — |
| `KUBERNETES_NAMESPACE` | default | — |
| `KUBERNETES_IN_CLUSTER` | false | — |
| `KUBERNETES_ALLOW_WRITE` | false | — |
| `KUBERNETES_LOG_TAIL_LINES` | 200 | — |

## mcp-llm-router

- **Tools:** 8
- **Variables de entorno específicas:** 14

### Tools

| Tool | Descripción |
|------|-------------|
| `route_task` | Analiza un prompt y decide qué modelo usar: local (LM Studio) o nube. Retorna destination, model recomendado, task_type, complexity_score (1-10), estimated_tokens y razonamiento de la decisión. Parámetros: prompt (obligatorio), context (contexto adicional), force_local (bool), force_cloud (bool). |
| `estimate_task_complexity` | Evalúa la complejidad de un prompt (score 1-10) sin tomar decisión de ruteo. Retorna complexity_score, task_type, estimated_tokens, complexity_label y factores. Parámetros: prompt, context (opcional). |
| `get_routing_config` | Retorna la configuración actual del router: modelos locales asignados por rol, modelo de nube, umbrales de complejidad y tokens, modo privacidad. |
| `get_routing_history` | Retorna el historial de decisiones de ruteo tomadas por el servidor. Muestra destination, model, task_type y complexity_score por decisión. Parámetro limit: máximo de entradas (default 50). |
| `check_lmstudio_health` | Verifica si LM Studio está corriendo y lista los modelos disponibles. Retorna status, available_models y model_count. Parámetro timeout: segundos de espera (default 5). |
| `list_local_models` | Lista todos los modelos disponibles en LM Studio con sus metadatos completos (id, object, etc.). Útil para verificar qué modelos están cargados. |
| `call_local_model` | Ejecuta un prompt directamente en un modelo local de LM Studio. Retorna response_text, tokens_used y elapsed_seconds. Parámetros: prompt, model (nombre en LM Studio), system (prompt de sistema), temperature (0-2, default 0.7), max_tokens (default 2048). |
| `call_cloud_model` | Ejecuta un prompt en el modelo de nube configurado (Anthropic o OpenAI). Requiere ROUTER_CLOUD_API_KEY configurado en el .env. Retorna response_text, tokens_used y elapsed_seconds. Parámetros: prompt, system (prompt de sistema), temperature (default 0.7), max_tokens (default 4096). |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `ROUTER_LMSTUDIO_BASE_URL` | http://localhost:1234/v1 | URL base de la API de LM Studio (compatible con OpenAI). Variable de entorno: ROUTER_LMSTUDIO_BASE_URL. |
| `ROUTER_COMPLEXITY_THRESHOLD` | 6 | Umbral de complejidad (1-10) por encima del cual se usa la nube. Tareas con score >= threshold van a la nube. Variable de entorno: ROUTER_COMPLEXITY_THRESHOLD. |
| `ROUTER_MAX_LOCAL_TOKENS` | 6000 | Número máximo de tokens estimados para usar modelo local. Si la tarea requiere más tokens, se ruta a la nube. Variable de entorno: ROUTER_MAX_LOCAL_TOKENS. |
| `ROUTER_PRIVACY_MODE` | false | Si es true, fuerza el uso de modelos locales siempre. Nunca envía datos a la nube, independientemente de la complejidad. Variable de entorno: ROUTER_PRIVACY_MODE. |
| `ROUTER_HISTORY_MAX` | 500 | Número máximo de entradas a conservar en el historial de ruteo. Variable de entorno: ROUTER_HISTORY_MAX. |
| `ROUTER_MODEL_FAST` | qwen3-8b | Modelo local rápido para tareas simples (< complexity 3, < 2K tokens). Ejemplo: qwen3-8b. Variable de entorno: ROUTER_MODEL_FAST. |
| `ROUTER_MODEL_CODE` | devstral-small-2507 | Modelo local especializado en código. Usado para generación, review y refactoring de código. Variable de entorno: ROUTER_MODEL_CODE. |
| `ROUTER_MODEL_REASON` | deepseek-r1-0528-qwen3-8b | Modelo local con capacidades de razonamiento (chain-of-thought). Usado para análisis complejos que no requieren la nube. Variable de entorno: ROUTER_MODEL_REASON. |
| `ROUTER_MODEL_LARGE_CONTEXT` | qwen2.5-14b-instruct-1m | Modelo local con ventana de contexto grande (1M tokens). Usado para tareas con mucho contexto que pueden hacerse localmente. Variable de entorno: ROUTER_MODEL_LARGE. |
| `ROUTER_CLOUD_PROVIDER` | anthropic | Proveedor de modelos en la nube: 'anthropic' o 'openai'. Variable de entorno: ROUTER_CLOUD_PROVIDER. |
| `ROUTER_CLOUD_MODEL` | claude-sonnet-4-5 | Nombre del modelo de nube a usar para tareas complejas. Variable de entorno: ROUTER_CLOUD_MODEL. |
| `ROUTER_CLOUD_API_KEY` | — | API key del proveedor de nube. Dejar vacío si solo se usa local. Variable de entorno: ROUTER_CLOUD_API_KEY. |
| `ROUTER_LMSTUDIO_TIMEOUT_SECONDS` | 120 | Timeout en segundos para llamadas a LM Studio. Variable: ROUTER_LMSTUDIO_TIMEOUT_SECONDS. |
| `ROUTER_CLOUD_TIMEOUT_SECONDS` | 60 | Timeout en segundos para llamadas a la nube. Variable: ROUTER_CLOUD_TIMEOUT_SECONDS. |

## mcp-markdown

- **Tools:** 12
- **Variables de entorno específicas:** 12

### Tools

| Tool | Descripción |
|------|-------------|
| `read_markdown` | Lee y analiza un archivo Markdown de forma completa. Retorna el contenido crudo, frontmatter YAML, título (primer H1), recuento de palabras, headings, links, bloques de código e imágenes. |
| `extract_headings` | Extrae todos los encabezados (H1-H6) de un archivo Markdown. Cada encabezado incluye su nivel (1-6), texto y anchor HTML. |
| `extract_links` | Extrae todos los enlaces de un archivo Markdown, incluyendo imágenes. Cada enlace indica texto, URL, si es externo y si es imagen. |
| `extract_code_blocks` | Extrae todos los bloques de código (fenced code blocks) de un archivo Markdown. Incluye el lenguaje declarado, el contenido y la línea de inicio. |
| `get_toc` | Genera una tabla de contenidos Markdown para el archivo, con enlaces de anclaje a cada encabezado. Se puede limitar la profundidad (1-6). |
| `markdown_to_html` | Convierte un archivo Markdown (o texto Markdown directo) a HTML5 completo con estilos básicos embebidos. Soporta tablas, strikethrough y autolinks. |
| `markdown_to_plain_text` | Convierte Markdown a texto plano eliminando todo el markup (encabezados, énfasis, links, bloques de código, tablas, etc.). |
| `validate_markdown` | Valida un archivo Markdown y reporta problemas: H1 faltante o múltiple, encabezados duplicados, enlaces locales rotos, y ausencia de título. Retorna valid=True solo si no hay warnings. |
| `search_in_markdown` | Busca un texto en un archivo Markdown línea por línea. Retorna cada coincidencia con número de línea, contexto completo y el encabezado bajo el cual aparece. |
| `format_markdown` | Formatea y normaliza un archivo Markdown (o texto directo) usando mdformat. Estandariza encabezados, listas, espaciado y bloques de código. |
| `get_frontmatter` | Extrae solo el frontmatter YAML de un archivo Markdown. Retorna un dict vacío si el archivo no tiene frontmatter. |
| `list_markdown_files` | Lista todos los archivos Markdown en un directorio. Para cada archivo retorna la ruta, título, recuento de palabras, tamaño y frontmatter. Soporta búsqueda recursiva. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_MARKDOWN_SERVER_NAME` | mcp-markdown | Nombre del servidor MCP. |
| `MCP_MARKDOWN_SERVER_VERSION` | 1.0.0 | Versión del servidor. |
| `MCP_MARKDOWN_LOG_LEVEL` | INFO | Nivel de log: DEBUG \| INFO \| WARNING \| ERROR. |
| `MCP_MARKDOWN_LOG_FORMAT` | json | Formato de log: json (producción) \| console (desarrollo). |
| `MCP_MARKDOWN_MAX_FILE_SIZE_MB` | 10.0 | Tamaño máximo permitido de archivo Markdown en MB. |
| `MCP_MARKDOWN_ALLOWED_EXTENSIONS` | ['.md', '.markdown', '.mdx', '.mdown', '.mkd'] | Extensiones de archivo reconocidas como Markdown. |
| `MCP_MARKDOWN_DEFAULT_MAX_TOC_DEPTH` | 3 | Profundidad máxima por defecto para la tabla de contenidos. |
| `MCP_MARKDOWN_VALIDATE_EXTERNAL_LINKS` | false | Si True, valida que los enlaces externos respondan (requiere red). |
| `MCP_MARKDOWN_ALLOWED_ROOT` | — | Directorio raíz opcional al que se restringe el acceso a archivos. Variable: MCP_MARKDOWN_ALLOWED_ROOT. |
| `MCP_MARKDOWN_MCP_TRANSPORT` | stdio | Protocolo de transporte: 'stdio' \| 'streamable-http'. Variable: MCP_TRANSPORT. |
| `MCP_MARKDOWN_MCP_HOST` | 0.0.0.0 | Host del servidor HTTP (solo usado con mcp_transport=streamable-http). |
| `MCP_MARKDOWN_MCP_PORT` | 8000 | Puerto del servidor HTTP (solo usado con mcp_transport=streamable-http). |

## mcp-object-storage

- **Tools:** 6
- **Variables de entorno específicas:** 5

### Tools

| Tool | Descripción |
|------|-------------|
| `storage_list_buckets` |  |
| `storage_list_objects` |  |
| `storage_object_metadata` |  |
| `storage_presign_download` |  |
| `storage_upload_text` |  |
| `storage_delete_object` |  |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `OBJECT_STORAGE_ENDPOINT_URL` | — | — |
| `OBJECT_STORAGE_REGION` | us-east-1 | — |
| `OBJECT_STORAGE_PROFILE` | — | — |
| `OBJECT_STORAGE_ALLOW_WRITE` | false | — |
| `OBJECT_STORAGE_MAX_KEYS` | 500 | — |

## mcp-observability

- **Tools:** 3
- **Variables de entorno específicas:** 5

### Tools

| Tool | Descripción |
|------|-------------|
| `observability_prometheus_query` |  |
| `observability_loki_query` |  |
| `observability_health_check` |  |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `OBSERVABILITY_PROMETHEUS_URL` | — | — |
| `OBSERVABILITY_LOKI_URL` | — | — |
| `OBSERVABILITY_TIMEOUT_SECONDS` | 30.0 | — |
| `OBSERVABILITY_BEARER_TOKEN` | — | — |
| `OBSERVABILITY_MAX_ENTRIES` | 500 | — |

## mcp-openapi

- **Tools:** 3
- **Variables de entorno específicas:** 5

### Tools

| Tool | Descripción |
|------|-------------|
| `openapi_list_operations` |  |
| `openapi_describe_operation` |  |
| `openapi_invoke` |  |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `OPENAPI_SPEC` | ./openapi.yaml | — |
| `OPENAPI_ALLOWED_ROOT` | . | — |
| `OPENAPI_TIMEOUT_SECONDS` | 30.0 | — |
| `OPENAPI_ALLOW_INVOKE` | false | — |
| `OPENAPI_ALLOWED_HOSTS` | — | — |

## mcp-orchestrator

- **Tools:** 3
- **Variables de entorno específicas:** 1

### Tools

| Tool | Descripción |
|------|-------------|
| `orch_parse_airflow_dag` | Parsea un archivo de Python que contiene un DAG de Airflow y extrae tareas y sus dependencias (AST). |
| `orch_validate_dag` | Valida que un conjunto de aristas (dependencias) formen un grafo acíclico dirigido (DAG) válido. |
| `orch_generate_boilerplate` | Genera código Python (Airflow DAG) a partir de un dag_id y una lista de nombres de tareas. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `ORCH_DAGS_PATH` | ./dags | Ruta donde se almacenan los archivos de DAGs. |

## mcp-personal-vault

- **Tools:** 6
- **Variables de entorno específicas:** 7

### Tools

| Tool | Descripción |
|------|-------------|
| `personal_vault_status` |  |
| `personal_upsert` |  |
| `personal_get` |  |
| `personal_list` |  |
| `search_personal_context` |  |
| `personal_delete` |  |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `PERSONAL_VAULT_DATABASE_PATH` | data/personal-vault/personal.db | — |
| `PERSONAL_VAULT_KEY_FILE` | data/personal-vault/vault.key | — |
| `PERSONAL_VAULT_ENCRYPTION_KEY` | — | — |
| `PERSONAL_VAULT_ALLOW_WRITE` | false | — |
| `PERSONAL_VAULT_ALLOW_HIGHLY_SENSITIVE` | false | — |
| `PERSONAL_VAULT_ALLOW_SECRETS` | false | — |
| `PERSONAL_VAULT_MAX_RESULTS` | 25 | — |

## mcp-project-memory

- **Tools:** 15
- **Variables de entorno específicas:** 6

### Tools

| Tool | Descripción |
|------|-------------|
| `get_project_state` | Retorna el estado completo del proyecto: componentes, decisiones activas, tareas pendientes, invariantes y resumen de la última sesión. LLAMA ESTE TOOL AL INICIO DE CADA SESIÓN para recuperar el contexto completo. |
| `generate_project_brief` | Genera un resumen ejecutivo del proyecto en Markdown. Ideal para iniciar una nueva sesión con un agente que no tiene contexto previo. |
| `get_component_map` | Retorna el mapa de todos los componentes del proyecto con su estado, versión, número de tools y descripción. |
| `get_decisions_history` | Retorna el historial de decisiones de arquitectura y diseño. Parámetro opcional status_filter: 'active', 'superseded' o 'rejected'. |
| `get_session_history` | Retorna el historial de sesiones de trabajo registradas, ordenadas de más reciente a más antigua. Parámetro limit: máximo de sesiones a retornar (default 20). |
| `search_memory` | Búsqueda de texto en toda la memoria del proyecto: decisiones, tareas, sesiones e invariantes. Parámetro query: texto a buscar (mínimo 2 caracteres). |
| `diff_state` | Compara el estado actual del proyecto con el estado al finalizar una sesión anterior. Muestra componentes nuevos, decisiones tomadas y tareas completadas desde esa sesión. Parámetro session_id: ID de la sesión a comparar (ej: 'SES-0003'). |
| `export_memory_snapshot` | Exporta toda la memoria del proyecto como JSON estructurado. Útil para backup, migración o inspección completa del estado. |
| `snapshot_session` | Guarda un snapshot de la sesión de trabajo actual. LLAMA ESTE TOOL AL FINALIZAR CADA SESIÓN para preservar el contexto. Parámetros: summary (resumen de lo hecho), changes_made (lista de archivos/componentes modificados), decisions_taken (int), tasks_completed (int), agent (nombre del agente). |
| `update_component_status` | Actualiza o registra un componente del proyecto. Parámetros: component_name (ej: 'mcp-tabular'), status ('draft'\|'ready'\|'deprecated'), version (ej: '1.0.0'), description (str), tools (int), port (int). |
| `record_decision` | Registra una decisión de arquitectura o diseño con su justificación. Parámetros: title (título conciso), rationale (justificación), alternatives_rejected (lista de alternativas descartadas), tags (lista de etiquetas). |
| `add_pending_task` | Agrega una tarea pendiente al backlog del proyecto. Parámetros: title (descripción corta), context (detalles), priority ('high'\|'medium'\|'low'). |
| `complete_pending_task` | Marca una tarea pendiente como completada. Parámetros: task_id (ej: 'TASK-0001'), resolution (cómo se resolvió). |
| `initialize_project` | Inicializa o actualiza los datos base del proyecto en la memoria. Idempotente: no borra sesiones ni decisiones existentes. Parámetros: project_name, description, tech_stack (lista), invariants (reglas que nunca deben violarse). |
| `sync_from_filesystem` | Escanea el filesystem del proyecto y registra automáticamente los directorios 'mcp-*' detectados como componentes en la memoria. No elimina componentes existentes. Parámetro project_root: ruta raíz del proyecto (default: directorio actual). |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MEMORY_MEMORY_DIR` | .ai-memory | Directorio donde se almacena el archivo JSON de memoria del proyecto. Puede ser relativo al directorio de trabajo o absoluto. Variable de entorno: MEMORY_DIR. |
| `MEMORY_MEMORY_FILE` | project_memory.json | Nombre del archivo JSON que almacena la memoria del proyecto. Variable de entorno: MEMORY_FILE. |
| `MEMORY_PROJECT_NAME` | mcps | Nombre del proyecto para identificación en los metadatos. Variable de entorno: MEMORY_PROJECT_NAME. |
| `MEMORY_AUTO_SYNC` | false | Si es true, sincroniza automáticamente el estado de componentes con el filesystem al leer el estado del proyecto. Variable de entorno: MEMORY_AUTO_SYNC. |
| `MEMORY_PROJECT_ROOT` | — | Ruta raíz del proyecto para sincronización con el filesystem. Variable de entorno: MEMORY_PROJECT_ROOT. |
| `MEMORY_MAX_SESSIONS` | 100 | Número máximo de sesiones a conservar en el historial. Las más antiguas se eliminan al superar el límite. Variable de entorno: MEMORY_MAX_SESSIONS. |

## mcp-prompt-engineer

- **Tools:** 8
- **Variables de entorno específicas:** 12

### Tools

| Tool | Descripción |
|------|-------------|
| `analyze_prompt` | Analiza un prompt de LLM de forma exhaustiva usando heurísticas reales. Detecta: tokens estimados, conteo de palabras, idioma, tipo de prompt, puntuación de claridad (0–10), problemas (críticos/warnings/info) y fortalezas. Parámetros: prompt (texto a analizar), target_model (modelo objetivo opcional: 'gpt-4', 'claude-3-5', etc.). Retorna: token_count, word_count, language, prompt_type, clarity_score, issues, strengths, suggestions, has_role, has_examples, has_format_spec. |
| `classify_prompt` | Clasifica el tipo de un prompt con una puntuación de confianza. Tipos posibles: instruction (tarea directa), question (pregunta abierta), closed_question (sí/no), few_shot (con ejemplos), system (system prompt), conversation (conversacional), creative (creativo), code (código). Parámetro: prompt (texto a clasificar). Retorna: type, confidence, indicators_found. |
| `estimate_tokens` | Estima el número de tokens para un texto en múltiples modelos de lenguaje. Usa tiktoken para modelos OpenAI y heurísticas para Claude. También indica si el texto cabe en el contexto de cada modelo. Parámetros: text (texto a analizar), model (modelo de referencia, por defecto 'gpt-4o'). Retorna: text_length, word_count, method, tokens (por modelo), context_fit. |
| `improve_prompt` | Mejora automáticamente un prompt aplicando buenas prácticas de prompt engineering. Las mejoras son heurísticas: agrega contexto, clarifica instrucciones, añade formato si falta, elimina ambigüedades. Parámetros: prompt (prompt original), goal (objetivo del prompt, opcional), target_model (modelo objetivo, opcional), style (estilo deseado: formal \| casual \| technical \| simple \| concise, opcional). Retorna: original, improved, changes (lista de cambios aplicados), score_before, score_after, improvement_delta. |
| `generate_variations` | Genera N variaciones del prompt con diferentes enfoques de prompt engineering: role_injection (añade rol experto), chain_of_thought (razonamiento paso a paso), structured_output (plantilla de salida), concise (versión condensada), audience_context (adapta para audiencia específica). Parámetros: prompt (prompt base), n (número de variaciones, 1–10, por defecto 3). Retorna: lista de variaciones con variation, approach, description, clarity_score. |
| `create_system_prompt` | Crea un system prompt estructurado y completo a partir de componentes. Parámetros: role (rol o persona del asistente, ej: 'experto en finanzas'), context (contexto de uso o empresa), constraints (restricciones o reglas a seguir, opcional). Retorna: system_prompt (texto listo para usar como system message). |
| `decompose_task` | Descompone una tarea compleja en subtareas numeradas y manejables. Útil para tareas de múltiples pasos que abruman al modelo en un solo prompt. Parámetro: task (descripción de la tarea compleja). Retorna: lista de subtareas con step, title, description, prompt_suggestion. |
| `get_prompt_template` | Retorna un template de prompt optimizado para un caso de uso específico. Casos de uso disponibles: analysis, code_review, code_generation, writing, translation, summarization, classification, extraction, qa, brainstorming, debugging, documentation, refactoring, testing, explanation. Parámetro: use_case (nombre del caso de uso). Retorna: use_case, template, placeholders (variables a reemplazar), description, tips. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_PE_LOG_LEVEL` | INFO | Nivel de logging: DEBUG \| INFO \| WARNING \| ERROR |
| `MCP_PE_LOG_FORMAT` | json | Formato de logging: json (producción) \| console (desarrollo) |
| `MCP_PE_MAX_PROMPT_LENGTH` | 100000 | Longitud máxima del prompt en caracteres. |
| `MCP_PE_MAX_VARIATIONS` | 10 | Número máximo de variaciones a generar. |
| `MCP_PE_DEFAULT_VARIATIONS` | 3 | Número por defecto de variaciones a generar. |
| `MCP_PE_DEFAULT_MODEL` | gpt-4o | Modelo por defecto para estimación de tokens. |
| `MCP_PE_TIKTOKEN_CACHE_DIR` | — | Directorio de caché para modelos tiktoken (opcional). |
| `MCP_PE_SERVER_NAME` | mcp-prompt-engineer | Nombre del servidor MCP. |
| `MCP_PE_SERVER_VERSION` | 1.0.0 | Versión del servidor MCP. |
| `MCP_PE_MCP_TRANSPORT` | stdio | Protocolo de transporte: 'stdio' \| 'streamable-http'. Variable: MCP_TRANSPORT. |
| `MCP_PE_MCP_HOST` | 0.0.0.0 | Host del servidor HTTP (solo usado con mcp_transport=streamable-http). |
| `MCP_PE_MCP_PORT` | 8000 | Puerto del servidor HTTP (solo usado con mcp_transport=streamable-http). |

## mcp-security-champion

- **Tools:** 2
- **Variables de entorno específicas:** 1

### Tools

| Tool | Descripción |
|------|-------------|
| `sec_audit_code` | Audita código fuente buscando hardcoded secrets o funciones inseguras (OWASP Top 10). |
| `sec_financial_compliance` | Revisa el cumplimiento de normativas financieras como PCI-DSS (enmascaramiento de datos, uso de HTTPS). |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SEC_PROJECT_PATH` | — | Ruta base del proyecto. |

## mcp-snyk

- **Tools:** 1
- **Variables de entorno específicas:** 2

### Tools

| Tool | Descripción |
|------|-------------|
| `snyk_run_test` | Ejecuta 'snyk test' en el proyecto actual y devuelve un reporte de vulnerabilidades. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SNYK_PROJECT_PATH` | — | Ruta base del proyecto. |
| `SNYK_API_TOKEN` | — | Token de API de Snyk (opcional para CLI auth global). |

## mcp-sonar

- **Tools:** 1
- **Variables de entorno específicas:** 3

### Tools

| Tool | Descripción |
|------|-------------|
| `sonar_run_scan` | Ejecuta 'sonar-scanner' en el proyecto actual y devuelve un resumen de calidad. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SONAR_PROJECT_PATH` | — | Ruta base del proyecto. |
| `SONAR_HOST_URL` | http://localhost:9000 | URL del servidor SonarQube. |
| `SONAR_API_TOKEN` | — | Token de API de SonarQube. |

## mcp-structured-output

- **Tools:** 4
- **Variables de entorno específicas:** 8

### Tools

| Tool | Descripción |
|------|-------------|
| `invoke_structured` | Llama a un LLM y garantiza que la respuesta cumpla un JSON Schema. Proveedores: bedrock-converse \| bedrock-invoke-claude \| bedrock-invoke-openweight \| openai-compatible. Credenciales AWS vía entorno/perfil boto3. Parámetros: prompt, schema, schema_name (default 'response'), provider, model_id, system_prompt, max_tokens (default 2048), temperature (default 0.0), region (AWS), base_url (solo openai-compatible). |
| `validate_schema` | Valida localmente que un JSON Schema sea compatible con Bedrock structured output (Draft 2020-12). Detecta: schemas recursivos, $ref externos, additionalProperties != false, constraints numéricas/string no soportadas, minItems fuera de [0,1], enum con tipos complejos. No hace llamadas a AWS. Retorna: valid (bool), issues (lista con path, message, severity). |
| `generate_schema` | Genera un JSON Schema Bedrock-compatible a partir de un objeto JSON de ejemplo. Infiere tipos automáticamente y aplica additionalProperties: false. Parámetros: example (dict JSON), name (nombre del schema, default 'schema'), description (opcional), strict (bool, default true — marca todos los campos como required). Retorna: schema (dict), field_count (int), warnings (list). |
| `sanitize_schema` | Transforma un JSON Schema para que sea compatible con Bedrock structured output. Elimina/transforma automáticamente: constraints numéricas (minimum, maximum, multipleOf), constraints de string (minLength, maxLength), additionalProperties != false, $ref externos, minItems fuera de [0,1], valores complejos en enum. El schema original NO se modifica. Retorna: sanitized (dict), changes (lista con path, action, reason), was_valid (bool). |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_SO_AWS_REGION` | us-east-1 | Región AWS por defecto para Bedrock. Variable: MCP_SO_AWS_REGION. |
| `MCP_SO_AWS_PROFILE` | — | Perfil AWS opcional (boto3 credential chain). Variable: MCP_SO_AWS_PROFILE. |
| `MCP_SO_DEFAULT_PROVIDER` | bedrock-converse | Proveedor por defecto: bedrock-converse \| bedrock-invoke-claude \| bedrock-invoke-openweight \| openai-compatible. Variable: MCP_SO_DEFAULT_PROVIDER. |
| `MCP_SO_DEFAULT_MODEL_ID` | amazon.nova-pro-v1:0 | ID del modelo por defecto. Variable: MCP_SO_DEFAULT_MODEL_ID. |
| `MCP_SO_DEFAULT_MAX_TOKENS` | 2048 | Max tokens por defecto. Variable: MCP_SO_DEFAULT_MAX_TOKENS. |
| `MCP_SO_DEFAULT_TEMPERATURE` | 0.0 | Temperature por defecto (0.0 recomendado para structured output). Variable: MCP_SO_DEFAULT_TEMPERATURE. |
| `MCP_SO_OPENAI_BASE_URL` | — | URL base para endpoints OpenAI-compatible. Variable: MCP_SO_OPENAI_BASE_URL. |
| `MCP_SO_OPENAI_API_KEY` | — | API key para endpoints OpenAI-compatible. Variable: MCP_SO_OPENAI_API_KEY. |

## mcp-tabular

- **Tools:** 8
- **Variables de entorno específicas:** 6

### Tools

| Tool | Descripción |
|------|-------------|
| `read_tabular_file` | Lee un archivo tabular (Excel, CSV, TSV, ODS, Parquet) y retorna los datos en formato JSON. Detecta automáticamente el encoding para archivos CSV/TSV. Parámetros: path (ruta al archivo), sheet (nombre de hoja para Excel/ODS, opcional), encoding ('auto' o nombre de encoding como 'utf-8', 'latin-1'). Retorna: columns (metadatos de columnas), records (filas como dicts), total_rows, returned_rows, truncated, metadata, warnings. |
| `get_sheet_names` | Retorna la lista de nombres de hojas de un archivo Excel (.xlsx, .xls) u ODS. No aplica para CSV, TSV ni Parquet. Parámetro: path (ruta al archivo). Retorna: lista de strings con los nombres de las hojas en orden. |
| `get_file_summary` | Retorna estadísticas completas de un archivo tabular: shape (filas × columnas), tipos de datos, conteo de nulos por columna, y estadísticas descriptivas (mean, std, min, max, percentiles) de columnas numéricas. Parámetros: path (ruta al archivo), sheet (hoja para Excel/ODS, opcional). Retorna: dict con shape, columns, dtypes, null_counts, null_percentages, numeric_describe, size_bytes, size_mb. |
| `read_specific_sheet` | Lee una hoja específica de un archivo Excel (.xlsx, .xls) u ODS por nombre exacto. Retorna un error descriptivo si la hoja no existe, indicando las hojas disponibles. Parámetros: path (ruta al archivo), sheet_name (nombre exacto de la hoja). Retorna: mismo formato que read_tabular_file. |
| `filter_rows` | Filtra filas de un archivo tabular según un criterio en una columna. Operadores soportados: eq (igual), ne (diferente), gt (mayor), lt (menor), gte (mayor o igual), lte (menor o igual), contains (contiene substring, case-insensitive), startswith (empieza con, case-insensitive). Parámetros: path, column (nombre de columna), operator (ver lista), value (valor a comparar como string), sheet (opcional). El valor se convierte automáticamente al tipo de la columna para comparaciones numéricas. Retorna: mismo formato que read_tabular_file pero solo con las filas que cumplen el filtro. |
| `search_in_file` | Busca un texto en todas las columnas del archivo tabular (búsqueda case-insensitive). Retorna todas las celdas que contienen el texto buscado, con el contexto completo de la fila. Parámetros: path, query (texto a buscar), sheet (opcional), max_results (máximo de resultados, por defecto 100). Retorna: lista de matches con row_index, column, value y row (fila completa). |
| `convert_to_csv` | Convierte un archivo tabular (Excel, ODS, Parquet) a formato CSV. Retorna el contenido CSV completo como string, incluyendo encabezados. Útil para exportar datos o usar en otros sistemas que solo aceptan CSV. Parámetros: path, sheet (nombre de hoja para Excel/ODS, opcional), output_encoding (encoding del CSV de salida, por defecto 'utf-8'). Retorna: string con el contenido CSV completo. |
| `get_column_stats` | Retorna estadísticas detalladas de una columna específica del archivo. Para columnas numéricas: mean, std, min, max, percentiles, skewness, kurtosis. Para columnas de texto: value_counts top-10, most_frequent, avg/min/max length. Para columnas de fecha: min_date, max_date, date_range_days. Para todas: null_count, null_percentage, unique_count, dtype, total_count. Parámetros: path, column (nombre exacto de la columna), sheet (opcional). Retorna: dict con stats adaptadas al tipo de la columna. |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `TABULAR_MAX_ROWS_PREVIEW` | 1000 | Máximo de filas retornadas en una respuesta sin paginación. Si el archivo tiene más filas, se trunca y se indica en 'truncated'. Variable de entorno: TABULAR_MAX_ROWS_PREVIEW. |
| `TABULAR_MAX_FILE_SIZE_MB` | 100 | Tamaño máximo permitido de archivo en MB. Archivos más grandes serán rechazados con un error descriptivo. Variable de entorno: TABULAR_MAX_FILE_SIZE_MB. |
| `TABULAR_DEFAULT_ENCODING` | utf-8 | Encoding por defecto para archivos CSV y TSV cuando no se puede detectar automáticamente con chardet. Ejemplos: 'utf-8', 'latin-1', 'cp1252'. Variable de entorno: TABULAR_DEFAULT_ENCODING. |
| `TABULAR_SAMPLE_VALUES_COUNT` | 5 | Número de valores de muestra a incluir por columna en la respuesta. Variable de entorno: TABULAR_SAMPLE_VALUES_COUNT. |
| `TABULAR_CHARDET_CONFIDENCE_THRESHOLD` | 0.7 | Umbral mínimo de confianza para aceptar la detección de encoding con chardet. Si la confianza es menor, se usa default_encoding. Variable de entorno: TABULAR_CHARDET_CONFIDENCE_THRESHOLD. |
| `TABULAR_ALLOWED_ROOT` | — | Directorio raíz opcional al que se restringe el acceso a archivos. Variable de entorno: TABULAR_ALLOWED_ROOT. |

## mcp-terraform

- **Tools:** 1
- **Variables de entorno específicas:** 1

### Tools

| Tool | Descripción |
|------|-------------|
| `tf_run_cmd` | Ejecuta un comando Terraform en el proyecto. Provee los argumentos (ej. 'plan' o 'init'). |

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `TF_PROJECT_PATH` | — | Ruta base donde están los archivos .tf. |
