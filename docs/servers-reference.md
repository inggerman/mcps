# Referencia de Servidores — Tools reales

> Todas las firmas y descripciones están extraídas directamente del código fuente. Última lectura: junio 2026.

---

## mcp-tabular

**Módulo:** `mcp_tabular.server`  
**Config:** `TabularSettings(BaseMcpSettings)` — prefijo `TABULAR_`  
**Entrypoint:** `python -m mcp_tabular.server`  
**Puerto (HTTP):** 8001  
**Fuente tools:** `mcp_tabular/tools/tabular_reader.py`

### Variables de entorno específicas

| Variable | Default | Descripción |
|----------|---------|-------------|
| `TABULAR_MAX_ROWS_PREVIEW` | `1000` | Máx. filas retornadas sin paginación |
| `TABULAR_MAX_FILE_SIZE_MB` | `100` | Tamaño máx. de archivo en MB |
| `TABULAR_DEFAULT_ENCODING` | `utf-8` | Encoding por defecto para CSV/TSV |
| `TABULAR_SAMPLE_VALUES_COUNT` | `5` | Valores de muestra por columna |
| `TABULAR_CHARDET_CONFIDENCE_THRESHOLD` | `0.7` | Umbral mínimo de confianza chardet |
| `TABULAR_ALLOWED_ROOT` | `` | Raíz opcional permitida para acceso a archivos |

### Tools registradas

```python
@mcp.tool(name="read_tabular_file")
def tool_read_tabular_file(
    path: str,
    sheet: str | None = None,
    encoding: str = "auto",
) -> dict[str, Any]
# Lee Excel/CSV/TSV/ODS/Parquet → JSON. Retorna: headers, rows, shape, truncated.

@mcp.tool(name="get_sheet_names")
def tool_get_sheet_names(path: str) -> list[str]
# Lista hojas de un Excel u ODS.

@mcp.tool(name="get_file_summary")
def tool_get_file_summary(path: str) -> dict[str, Any]
# Shape, columnas, tipos, valores nulos, muestra de datos.

@mcp.tool(name="read_specific_sheet")
def tool_read_specific_sheet(path: str, sheet_name: str) -> dict[str, Any]
# Lee hoja específica de Excel/ODS por nombre exacto.

@mcp.tool(name="filter_rows")
def tool_filter_rows(
    path: str,
    column: str,
    operator: str,      # "eq", "ne", "gt", "lt", "gte", "lte", "contains", "startswith"
    value: str,
    sheet: str | None = None,
) -> dict[str, Any]
# Filtra filas por criterio en una columna.

@mcp.tool(name="search_in_file")
def tool_search_in_file(
    path: str,
    query: str,
    sheet: str | None = None,
    max_results: int = 100,
) -> list[dict[str, Any]]
# Búsqueda case-insensitive en todas las columnas.

@mcp.tool(name="convert_to_csv")
def tool_convert_to_csv(
    path: str,
    sheet: str | None = None,
    output_encoding: str = "utf-8",
) -> str
# Convierte Excel/ODS/Parquet a CSV string.

@mcp.tool(name="get_column_stats")
def tool_get_column_stats(path: str, column: str, sheet: str | None = None) -> dict[str, Any]
# Estadísticas detalladas de una columna: tipo, nulos, min/max, media, valores únicos.
```

---

## mcp-calendar

**Módulo:** `mcp_calendar.server`  
**Config:** `CalendarSettings(BaseMcpSettings)` — sin prefijo adicional  
**Entrypoint:** `python -m mcp_calendar.server`  
**Puerto (HTTP):** 8002  
**Fuentes tools:** `mcp_calendar/tools/business_days.py`, `mcp_calendar/tools/currency.py`  
**Dependencias externas:** `holidays` (PyPI), `python-dateutil`, Frankfurter API (gratuita, sin key)

### Variables de entorno específicas

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DEFAULT_COUNTRY` | `MX` | País por defecto para días hábiles |
| `EXCHANGE_CACHE_TTL_SECONDS` | `3600` | TTL del caché de tasas en segundos |

### Tools registradas — días hábiles

```python
@mcp.tool(name="get_holidays")
def tool_get_holidays(country: str, year: int, state: str | None = None) -> list[dict[str, Any]]
# Feriados del país para el año. Retorna: date, name, country.

@mcp.tool(name="calculate_business_days")
def tool_calculate_business_days(
    start_date: str,   # ISO: YYYY-MM-DD
    end_date: str,     # ISO: YYYY-MM-DD
    country: str = "MX",
) -> dict[str, Any]
# Días hábiles entre dos fechas (ambas inclusive).
# Retorna: business_days, total_days, weekends, holidays, start_date, end_date, country.

@mcp.tool(name="add_business_days")
def tool_add_business_days(
    start_date: str,
    n_days: int,
    country: str = "MX",
) -> str
# Suma N días hábiles a una fecha. Retorna fecha ISO resultante.

@mcp.tool(name="is_business_day")
def tool_is_business_day(check_date: str, country: str = "MX") -> dict[str, Any]
# Verifica si una fecha es día hábil.
# Retorna: date, is_business_day, reason (si no es hábil), country.

@mcp.tool(name="next_business_day")
def tool_next_business_day(check_date: str, country: str = "MX") -> str
# Siguiente día hábil. Retorna fecha ISO.

@mcp.tool(name="previous_business_day")
def tool_previous_business_day(check_date: str, country: str = "MX") -> str
# Día hábil anterior. Retorna fecha ISO.

@mcp.tool(name="business_days_in_month")
def tool_business_days_in_month(year: int, month: int, country: str = "MX") -> dict[str, Any]
# Total días hábiles en un mes.
# Retorna: year, month, country, business_days, total_days, weekends, holidays.

@mcp.tool(name="get_mexico_holidays")
def tool_get_mexico_holidays(year: int) -> list[dict[str, Any]]
# Feriados MX con descripción histórica en español.

@mcp.tool(name="get_country_list")
def tool_get_country_list() -> list[dict[str, Any]]
# Países soportados por la librería `holidays`. Retorna: code, name, subdivisions.
```

### Tools registradas — divisas (Frankfurter API)

```python
@mcp.tool(name="get_exchange_rate")
def tool_get_exchange_rate(
    from_currency: str,
    to_currency: str,
    ttl_seconds: int = 3600,
) -> dict[str, Any]
# Tasa de cambio actual. Retorna: base, target, rate, date, provider.

@mcp.tool(name="convert_currency")
def tool_convert_currency(amount: float, from_currency: str, to_currency: str) -> dict[str, Any]
# Convierte un monto. Retorna: amount, from, to, converted, rate, date.

@mcp.tool(name="get_historical_rate")
def tool_get_historical_rate(
    from_currency: str,
    to_currency: str,
    rate_date: str,
) -> dict[str, Any]
# Tasa histórica para una fecha específica. date: ISO YYYY-MM-DD.

@mcp.tool(name="get_mx_rates")
def tool_get_mx_rates(base: str = "MXN", ttl_seconds: int = 3600) -> dict[str, Any]
# MXN vs USD, EUR, GBP, JPY, CAD y otras principales.

@mcp.tool(name="list_supported_currencies")
def tool_list_supported_currencies() -> list[dict[str, Any]]
# Todas las divisas ISO 4217 soportadas por Frankfurter.

@mcp.tool(name="get_rate_history")
def tool_get_rate_history(
    from_currency: str,
    to_currency: str,
    start_date: str,
    end_date: str,
) -> list[dict[str, Any]]
# Serie histórica de tasas entre dos fechas.
```

---

## mcp-markdown

**Módulo:** `mcp_markdown.server`  
**Config:** `Settings(BaseSettings)` — prefijo `MCP_MARKDOWN_`  
**Entrypoint:** `python -m mcp_markdown.server` o función `main()`  
**Puerto (HTTP):** 8003  
**Fuente tools:** `mcp_markdown/tools/`

### Variables de entorno específicas

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_MARKDOWN_LOG_LEVEL` | `INFO` | Nivel de log |
| `MCP_MARKDOWN_LOG_FORMAT` | `json` | Formato de log |
| `MCP_MARKDOWN_MAX_FILE_SIZE_MB` | `10` | Tamaño máx. de archivo |
| `MCP_MARKDOWN_MAX_TOC_DEPTH` | `3` | Profundidad máx. para ToC |
| `MCP_MARKDOWN_VALIDATE_EXTERNAL_LINKS` | `false` | Validar enlaces externos |
| `MCP_MARKDOWN_ALLOWED_ROOT` | `` | Raíz opcional permitida para acceso a archivos |
| `MCP_TRANSPORT` | `stdio` | Acepta via AliasChoices |
| `MCP_PORT` | `8000` | Acepta via AliasChoices |
| `MCP_HOST` | `0.0.0.0` | Acepta via AliasChoices |

### Tools registradas

```python
@mcp.tool(name="read_markdown")
def tool_read_markdown(path: str) -> dict[str, Any]
# Lee un .md completo. Retorna: content, frontmatter, headings, word_count, etc.

@mcp.tool(name="extract_headings")
def tool_extract_headings(path: str) -> list[dict[str, Any]]
# Jerarquía de títulos H1-H6. Retorna lista de {level, text, line}.

@mcp.tool(name="extract_links")
def tool_extract_links(path: str) -> list[dict[str, Any]]
# Todos los enlaces (href, text, is_image, line).

@mcp.tool(name="extract_code_blocks")
def tool_extract_code_blocks(path: str) -> list[dict[str, Any]]
# Bloques de código fenced. Retorna: language, code, line.

@mcp.tool(name="get_toc")
def tool_get_toc(path: str, max_depth: int = 3) -> str
# Genera tabla de contenidos en formato Markdown.

@mcp.tool(name="markdown_to_html")
def tool_markdown_to_html(path_or_text: str, is_path: bool = True) -> str
# Convierte a HTML5. Acepta ruta o texto directo (is_path=False).

@mcp.tool(name="markdown_to_plain_text")
def tool_markdown_to_plain_text(path_or_text: str, is_path: bool = True) -> str
# Elimina todo el markup Markdown → texto plano.

@mcp.tool(name="validate_markdown")
def tool_validate_markdown(path: str) -> dict[str, Any]
# Detecta: enlaces rotos, headings mal anidados, imágenes sin alt. Retorna issues[].

@mcp.tool(name="search_in_markdown")
def tool_search_in_markdown(
    path: str,
    query: str,
    case_sensitive: bool = False,
) -> list[dict[str, Any]]
# Búsqueda línea por línea. Retorna lista de {line_number, line, match}.

@mcp.tool(name="format_markdown")
def tool_format_markdown(path_or_text: str, is_path: bool = True) -> str
# Normaliza formato usando mdformat.

@mcp.tool(name="get_frontmatter")
def tool_get_frontmatter(path: str) -> dict[str, Any]
# Extrae solo el YAML frontmatter del archivo.

@mcp.tool(name="list_markdown_files")
def tool_list_markdown_files(directory: str, recursive: bool = True) -> list[dict[str, Any]]
# Lista archivos .md. Por cada uno: path, title, word_count, size, frontmatter.
```

---

## mcp-prompt-engineer

**Módulo:** `mcp_prompt_engineer.server`  
**Config:** `Settings(BaseSettings)` — prefijo `MCP_PE_`  
**Entrypoint:** `python -m mcp_prompt_engineer.server`  
**Puerto (HTTP):** 8004  
**Fuentes tools:** `mcp_prompt_engineer/tools/analyzer.py`, `mcp_prompt_engineer/tools/improver.py`  
**Nota importante:** Todo el procesamiento es **local** — sin llamadas a APIs externas.

### Variables de entorno específicas

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_PE_LOG_LEVEL` | `INFO` | Nivel de log |
| `MCP_PE_MAX_PROMPT_LENGTH` | *(ver config)* | Longitud máx. de prompt |
| `MCP_TRANSPORT` | `stdio` | Acepta via AliasChoices |
| `MCP_PORT` | `8000` | Acepta via AliasChoices |
| `MCP_HOST` | `0.0.0.0` | Acepta via AliasChoices |

### Tools registradas

```python
@mcp.tool(name="analyze_prompt")
def tool_analyze_prompt(prompt: str, target_model: str | None = None) -> dict[str, Any]
# Análisis exhaustivo: token_count, language, prompt_type, clarity_score (0-10),
# issues[], suggestions[], has_role, has_examples, has_format_spec, word_count.

@mcp.tool(name="classify_prompt")
def tool_classify_prompt(prompt: str) -> dict[str, Any]
# Clasifica tipo: instruction, question, few_shot, chain_of_thought, system, etc.
# Retorna: type, confidence (0-1), secondary_types[].

@mcp.tool(name="estimate_tokens")
def tool_estimate_tokens(text: str, model: str = "gpt-4o") -> dict[str, Any]
# Estimación de tokens para múltiples modelos simultáneamente.
# Retorna: {gpt-4o: N, claude-3-5: N, gpt-3.5: N, ...}

@mcp.tool(name="improve_prompt")
def tool_improve_prompt(
    prompt: str,
    goal: str | None = None,
    target_model: str | None = None,
) -> dict[str, Any]
# Mejora automática del prompt.
# Retorna: improved_prompt, changes[], original_clarity, improved_clarity, diff.

@mcp.tool(name="generate_variations")
def tool_generate_variations(prompt: str, n: int = 3) -> list[dict[str, Any]]
# N variaciones con distintos enfoques: CoT, role-based, few-shot, direct, structured.
# Retorna lista de {variation, approach, description}.

@mcp.tool(name="create_system_prompt")
def tool_create_system_prompt(
    role: str,
    context: str,
    constraints: str | None = None,
) -> dict[str, Any]
# Crea un system prompt estructurado. Retorna: system_prompt, components.

@mcp.tool(name="decompose_task")
def tool_decompose_task(task: str) -> list[dict[str, Any]]
# Descompone una tarea compleja en subtareas.
# Retorna lista de {step, description, dependencies[]}.

@mcp.tool(name="get_prompt_template")
def tool_get_prompt_template(use_case: str) -> dict[str, Any]
# Template optimizado para un caso de uso.
# use_case: "summarization", "translation", "code_review", "qa", "creative", etc.
# Retorna: template, variables[], instructions, example.
```

---

## mcp-structured-output

**Módulo:** `mcp_structured_output.server`  
**Config:** `StructuredOutputSettings(BaseMcpSettings)` — prefijo `MCP_SO_`  
**Entrypoint:** `python -m mcp_structured_output.server`  
**Puerto (HTTP):** 8005  
**Fuentes tools:** `mcp_structured_output/tools/schema_tools.py`, `mcp_structured_output/tools/invoke_tools.py`  
**Dependencias externas:** `boto3>=1.34` (Bedrock), `openai>=1.30` (OpenAI-compatible), `jsonschema>=4.22` (validación local)

### Variables de entorno específicas

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_SO_AWS_REGION` | `us-east-1` | Región AWS por defecto para Bedrock |
| `MCP_SO_AWS_PROFILE` | *(boto3 chain)* | Perfil AWS opcional |
| `MCP_SO_DEFAULT_PROVIDER` | `bedrock-converse` | Proveedor por defecto |
| `MCP_SO_DEFAULT_MODEL_ID` | `amazon.nova-pro-v1:0` | Modelo por defecto |
| `MCP_SO_DEFAULT_MAX_TOKENS` | `2048` | Max tokens por defecto |
| `MCP_SO_DEFAULT_TEMPERATURE` | `0.0` | Temperature (0.0 ideal para structured output) |
| `MCP_SO_OPENAI_BASE_URL` | `` | URL base para endpoints OpenAI-compatible |
| `MCP_SO_OPENAI_API_KEY` | `` | API key para OpenAI o compatible |

> Credenciales AWS (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) se leen directamente por boto3 desde el entorno — no se declaran en settings para no exponerlas en logs.

### Proveedores soportados en `invoke_structured`

| Provider | API usada | Campo de schema |
|----------|-----------|-----------------|
| `bedrock-converse` | Bedrock Converse API | `outputConfig.textFormat.structure.jsonSchema.schema` (JSON string) |
| `bedrock-invoke-claude` | Bedrock InvokeModel (Anthropic Claude) | `output_config.format.schema` (objeto) |
| `bedrock-invoke-openweight` | Bedrock InvokeModel (open-weight) | `response_format.json_schema.schema` (objeto) |
| `openai-compatible` | OpenAI Chat Completions | `response_format.json_schema.schema` (objeto) |

### Tools registradas

```python
@mcp.tool(name="invoke_structured")
def tool_invoke_structured(
    prompt: str,
    schema: dict[str, Any],
    schema_name: str = "response",
    provider: str = "bedrock-converse",
    model_id: str = "amazon.nova-pro-v1:0",
    system_prompt: str | None = None,
    max_tokens: int = 2048,
    temperature: float = 0.0,
    region: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]
# Llama al LLM y garantiza que la respuesta cumpla el schema.
# Retorna: {result: {...}, provider: str, model_id: str, usage: {input_tokens: N, output_tokens: N}}

@mcp.tool(name="validate_schema")
def tool_validate_schema(schema: dict[str, Any]) -> dict[str, Any]
# Valida localmente que un JSON Schema sea compatible con Bedrock Draft 2020-12.
# Sin llamadas AWS. Retorna: {valid: bool, issues: [{path, message, severity}]}

@mcp.tool(name="generate_schema")
def tool_generate_schema(
    example: dict[str, Any],
    name: str = "schema",
    description: str | None = None,
    strict: bool = True,
) -> dict[str, Any]
# Genera un JSON Schema Bedrock-compatible desde un objeto JSON de ejemplo.
# Retorna: {schema: {...}, field_count: int, warnings: [str]}

@mcp.tool(name="sanitize_schema")
def tool_sanitize_schema(schema: dict[str, Any]) -> dict[str, Any]
# Transforma un schema para eliminar features no soportadas por Bedrock.
# Retorna: {sanitized: {...}, changes: [{path, action, reason}], was_valid: bool}
```

### Features incompatibles que detecta/elimina

| Feature | validate_schema | sanitize_schema |
|---------|-----------------|-----------------|
| Constraints numéricas (`minimum`, `maximum`, `multipleOf`) | error | removes |
| Constraints de string (`minLength`, `maxLength`) | error | removes |
| `additionalProperties != false` | error | set to false |
| `$ref` externos | error | replace with `{type: string}` |
| `minItems` ≠ 0 o 1 | error | set to 1 |
| Schemas recursivos | error | *(no sanitizable automáticamente)* |
| `enum` con objetos/arrays | error | removes complex values |
| Objeto sin `additionalProperties` | warning | adds false |

---

## mcp-fetch

**Módulo:** `mcp_fetch.server`  
**Config:** `FetchSettings(BaseMcpSettings)` — prefijo `MCP_FETCH_`  
**Entrypoint:** `python -m mcp_fetch.server`  
**Puerto (HTTP):** 8006  
**Fuentes tools:** `mcp_fetch/tools/fetch_tools.py`  
**Dependencias externas:** `httpx>=0.27`, `beautifulsoup4>=4.12`

### Variables de entorno específicas

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_FETCH_DEFAULT_TIMEOUT` | `30` | Timeout HTTP en segundos |
| `MCP_FETCH_MAX_CONTENT_LENGTH` | `5242880` | Tamaño máximo de respuesta (5 MB) |
| `MCP_FETCH_USER_AGENT` | `mcp-fetch/1.0` | User-Agent enviado en requests |
| `MCP_FETCH_FOLLOW_REDIRECTS` | `false` | Seguir redirecciones HTTP |
| `MCP_FETCH_ALLOW_PRIVATE_NETWORKS` | `false` | Permitir destinos no públicos |
| `MCP_FETCH_VERIFY_SSL` | `true` | Verificar certificados SSL |

### Tools registradas

```python
@mcp.tool(name="fetch_url")
def tool_fetch_url(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    max_bytes: int | None = None,
) -> dict[str, Any]
# GET a una URL. Retorna: url, status_code, content_type, content,
# truncated, headers, elapsed_ms.

@mcp.tool(name="fetch_post")
def tool_fetch_post(
    url: str,
    json_body: dict[str, Any] | None = None,
    form_data: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    max_bytes: int | None = None,
) -> dict[str, Any]
# POST con JSON o form data. Misma estructura de retorno que fetch_url.

@mcp.tool(name="extract_text")
def tool_extract_text(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    include_links: bool = False,
    include_title: bool = True,
) -> dict[str, Any]
# Descarga HTML y extrae texto limpio (sin scripts, nav, footer).
# Retorna: url, text, word_count, status_code, title, links.

@mcp.tool(name="fetch_json")
def tool_fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    jq_path: str | None = None,
) -> dict[str, Any]
# Descarga y parsea JSON. jq_path: "data.items[0].name".
# Retorna: url, data, status_code, path_used.
```

---

## mcp-docker

**Módulo:** `mcp_docker.server`  
**Config:** `DockerSettings(BaseMcpSettings)` — prefijo `MCP_DOCKER_`  
**Entrypoint:** `python -m mcp_docker.server`  
**Puerto (HTTP):** 8007  
**Fuentes tools:** `mcp_docker/tools/docker_tools.py`  
**Dependencias externas:** `docker>=7.0` (Docker SDK para Python / libdocker)

> **Nota:** En Docker, montar el socket: `-v /var/run/docker.sock:/var/run/docker.sock:ro`

### Variables de entorno específicas

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_DOCKER_DOCKER_HOST` | *(socket local)* | URL daemon Docker (`unix://…` o `tcp://…`) |
| `MCP_DOCKER_LOG_LINES` | `100` | Líneas de logs por defecto |
| `MCP_DOCKER_EXEC_TIMEOUT` | `30` | Timeout exec en contenedor (segundos) |

### Tools registradas

```python
@mcp.tool(name="containers_list")
def tool_containers_list(
    all_containers: bool = False,
    filters: dict[str, str] | None = None,
) -> dict[str, Any]
# Lista contenedores. Retorna: containers[], count, showing.

@mcp.tool(name="containers_stats")
def tool_containers_stats(container_id: str) -> dict[str, Any]
# CPU %, memoria MB, red, disco de un contenedor.

@mcp.tool(name="container_logs")
def tool_container_logs(
    container_id: str,
    lines: int | None = None,
    since: str | None = None,
    timestamps: bool = False,
) -> dict[str, Any]
# Logs de un contenedor (tail). Retorna: logs, container_name, status.

@mcp.tool(name="container_exec")
def tool_container_exec(
    container_id: str,
    command: str,
    workdir: str | None = None,
    user: str | None = None,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]
# Ejecuta comando en contenedor running. Retorna: exit_code, output, success.

@mcp.tool(name="run_container")
def tool_run_container(
    image: str,
    command: str | None = None,
    name: str | None = None,
    detach: bool = True,
    ports: dict[str, str] | None = None,
    environment: dict[str, str] | None = None,
    volumes: dict[str, str] | None = None,
    remove_on_exit: bool = False,
) -> dict[str, Any]
# Crea y arranca un contenedor. Retorna: id, name, status, image, ports.

@mcp.tool(name="stop_container")
def tool_stop_container(
    container_id: str,
    timeout: int = 10,
    remove: bool = False,
) -> dict[str, Any]
# Detiene (y opcionalmente elimina) un contenedor.

@mcp.tool(name="images_list")
def tool_images_list(
    name: str | None = None,
    dangling: bool = False,
) -> dict[str, Any]
# Lista imágenes locales. Retorna: images[] (tags, size_mb, id), count.

@mcp.tool(name="image_pull")
def tool_image_pull(image: str, tag: str = "latest") -> dict[str, Any]
# Descarga imagen desde registry. Retorna: image, tag, id, tags[], size_mb.
```

---

## mcp-kafka

**Módulo:** `mcp_kafka.server`  
**Config:** `KafkaSettings(BaseMcpSettings)` — prefijo `MCP_KAFKA_`  
**Entrypoint:** `python -m mcp_kafka.server`  
**Puerto (HTTP):** 8008  
**Fuentes tools:** `mcp_kafka/tools/kafka_tools.py`  
**Dependencias externas:** `confluent-kafka>=2.5` (librdkafka wrapper)

### Variables de entorno específicas

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Brokers Kafka (comma-separated) |
| `MCP_KAFKA_SECURITY_PROTOCOL` | `PLAINTEXT` | `PLAINTEXT` \| `SSL` \| `SASL_PLAINTEXT` \| `SASL_SSL` |
| `MCP_KAFKA_SASL_MECHANISM` | *(none)* | `PLAIN` \| `SCRAM-SHA-256` \| `SCRAM-SHA-512` |
| `MCP_KAFKA_SASL_USERNAME` | *(none)* | Usuario SASL |
| `MCP_KAFKA_SASL_PASSWORD` | *(none)* | Contraseña SASL |
| `MCP_KAFKA_SSL_CA_LOCATION` | *(none)* | Ruta CA certificate (SSL) |
| `MCP_KAFKA_CONSUME_TIMEOUT` | `5.0` | Timeout consume en segundos |
| `MCP_KAFKA_MAX_CONSUME_MESSAGES` | `50` | Máx mensajes por llamada consume |
| `MCP_KAFKA_ADMIN_TIMEOUT` | `10.0` | Timeout operaciones admin |

### Tools registradas

```python
@mcp.tool(name="topics_list")
def tool_topics_list(
    prefix: str | None = None,
    exclude_internal: bool = True,
) -> dict[str, Any]
# Lista topics. Retorna: topics[] (name, partitions), count, cluster_id, broker_count.

@mcp.tool(name="topic_describe")
def tool_topic_describe(topic: str) -> dict[str, Any]
# Describe un topic: líder, réplicas, ISR por partición.
# Retorna: topic, partition_count, replication_factor, partitions[].

@mcp.tool(name="consumer_groups_list")
def tool_consumer_groups_list(prefix: str | None = None) -> dict[str, Any]
# Lista consumer groups. Retorna: groups[] (group_id, state, is_simple), count.

@mcp.tool(name="consumer_group_offsets")
def tool_consumer_group_offsets(
    group_id: str,
    topics: list[str] | None = None,
) -> dict[str, Any]
# Offsets de un consumer group. Retorna: group_id, offsets[] (topic, partition, offset).

@mcp.tool(name="produce_message")
def tool_produce_message(
    topic: str,
    value: str | dict[str, Any] = "",
    key: str | None = None,
    partition: int | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]
# Produce mensaje (dict → JSON automático). acks=all.
# Retorna: topic, partition, offset, timestamp_ms, key, value_size_bytes.

@mcp.tool(name="consume_messages")
def tool_consume_messages(
    topic: str,
    group_id: str = "mcp-kafka-consumer",
    max_messages: int | None = None,
    from_beginning: bool = False,
    timeout: float | None = None,
    parse_json: bool = True,
) -> dict[str, Any]
# Consume mensajes (non-blocking, retorna al agotar timeout o max_messages).
# Retorna: topic, group_id, messages[] (partition, offset, key, value, headers), count.
```

---

## Patrones de error comunes (todos los servidores)

Todos los servidores usan este patrón de manejo de errores en `server.py`:

```python
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError

@mcp.tool(name="...")
def tool_X(param: str) -> dict:
    try:
        return business_function(param)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))
    except Exception as exc:
        logger.exception("Error inesperado en tool X", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor."))
```

Códigos JSON-RPC usados:
- `-32000`: Error de negocio (archivo no encontrado, formato inválido, etc.)
- `-32603`: Error interno inesperado del servidor

---

*Última actualización: junio 2026*
