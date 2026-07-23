# MCP Framework — Manual de Onboarding

> **Para quien nunca escuchó hablar de MCP:** Este documento explica desde cero qué es MCP, para qué sirve este proyecto, cómo usarlo hoy mismo y cómo extenderlo. Léelo de principio a fin la primera vez; después úsalo como referencia.

---

## Tabla de Contenidos

1. [¿Qué es MCP? (la idea en 5 minutos)](#1-qué-es-mcp-la-idea-en-5-minutos)
2. [¿Para qué sirve este proyecto?](#2-para-qué-sirve-este-proyecto)
3. [Arquitectura general](#3-arquitectura-general)
4. [Catálogo de servidores](#4-catálogo-de-servidores)
5. [Prerrequisitos e instalación](#5-prerrequisitos-e-instalación)
6. [Uso local con Claude Desktop / Cursor / Windsurf](#6-uso-local-con-claude-desktop--cursor--windsurf)
7. [Desarrollo y pruebas](#7-desarrollo-y-pruebas)
8. [Despliegue en producción con Docker](#8-despliegue-en-producción-con-docker)
9. [La librería compartida `mcp_shared`](#9-la-librería-compartida-mcp_shared)
10. [Cómo crear un nuevo servidor MCP](#10-cómo-crear-un-nuevo-servidor-mcp)
11. [Variables de entorno de referencia](#11-variables-de-entorno-de-referencia)
12. [Referencia de comandos Makefile](#12-referencia-de-comandos-makefile)
13. [Convenciones y estándares de código](#13-convenciones-y-estándares-de-código)
14. [Preguntas frecuentes (FAQ)](#14-preguntas-frecuentes-faq)

---

## 1. ¿Qué es MCP? (la idea en 5 minutos)

### El problema que MCP resuelve

Los modelos de lenguaje (Claude, GPT, Gemini…) son muy buenos generando texto, pero viven "encerrados" — no pueden leer tus archivos, consultar tu base de datos, ni llamar a tus APIs internas. Cada integración se construía a mano, de forma distinta en cada herramienta.

**MCP (Model Context Protocol)** es el estándar abierto creado por Anthropic en 2024 que define *cómo* un modelo de IA se comunica con herramientas externas de forma universal. Es como USB para la IA: cualquier cliente que hable MCP puede usar cualquier servidor MCP, sin código de pegamento.

### Los tres componentes del protocolo

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTE MCP                          │
│        (Claude Desktop, Cursor, Windsurf, tu app…)          │
│                                                             │
│  El modelo de IA le dice al cliente: "necesito leer        │
│  un Excel". El cliente llama al servidor correcto.          │
└───────────────────────┬─────────────────────────────────────┘
                        │  Protocolo JSON-RPC 2.0
                        │  (via stdio o HTTP)
┌───────────────────────▼─────────────────────────────────────┐
│                      SERVIDOR MCP                           │
│           (este proyecto — mcp-tabular, etc.)               │
│                                                             │
│  Proceso Python independiente que expone "tools",           │
│  "resources" y "prompts" al modelo.                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                 SISTEMA EXTERNO                              │
│     (archivos del disco, APIs web, bases de datos…)         │
└─────────────────────────────────────────────────────────────┘
```

### Los tres tipos de capacidades que expone un servidor

| Tipo | ¿Qué es? | Ejemplo |
|------|----------|---------|
| **Tool** | Función que el modelo puede llamar | `read_excel("ventas.xlsx")` |
| **Resource** | Datos que el modelo puede leer | El contenido de un archivo |
| **Prompt** | Plantilla de instrucciones reutilizable | "Eres un analista de datos…" |

Este proyecto usa principalmente **tools** — son las más versátiles.

### Los dos modos de transporte

| Modo | Cuándo usarlo | Cómo funciona |
|------|--------------|---------------|
| **stdio** | Local (Claude Desktop, Cursor, Windsurf) | El cliente lanza el servidor como subproceso; se comunican por stdin/stdout |
| **streamable-http** | Producción (servidor remoto, múltiples clientes) | El servidor escucha en un puerto HTTP; el cliente hace requests |

> **Regla de oro:** durante desarrollo usa `stdio`. En producción usa `streamable-http` con Docker.

---

## 2. ¿Para qué sirve este proyecto?

Este repositorio es un **framework propio** de servidores MCP, diseñado para:

- Correr **localmente** en la máquina del desarrollador (integrado con Claude Desktop, Cursor o Windsurf).
- Desplegarse **en producción** en un servidor remoto de forma transparente — cambiando solo una variable de entorno (`MCP_TRANSPORT`).
- Compartir código de infraestructura (logging, configuración, manejo de errores) entre todos los servidores a través de la librería `mcp_shared`.
- Seguir estándares de producción: tipado estático, tests, Docker multi-stage, usuarios no-root y healthchecks.

---

## 3. Arquitectura general

```
mcps/                              ← raíz del workspace uv
│
├── shared/                        ← librería compartida (se instala como paquete)
│   └── src/mcp_shared/
│       ├── config.py              ← BaseMcpSettings (base de configuración)
│       ├── errors.py              ← jerarquía de errores tipados
│       ├── logging.py             ← setup_logging() con structlog
│       └── models.py              ← modelos Pydantic reutilizables
│
├── mcp-tabular/                  ← Archivos tabulares
├── mcp-calendar/                  ← Días hábiles y divisas
├── mcp-markdown/                  ← Archivos Markdown
├── mcp-prompt-engineer/                  ← Ingeniería de prompts
├── mcp-structured-output/                  ← Structured Output (LLMs JSON Schema)
├── mcp-fetch/                  ← HTTP y web scraping
├── mcp-docker/                  ← Gestión Docker
├── mcp-kafka/                  ← Apache Kafka
├── mcp-project-memory/                  ← Memoria de proyecto persistente
├── mcp-llm-router/                  ← Ruteo inteligente de LLMs
├── mcp-git/                  ← Operaciones Git
├── mcp-github/                  ← Integración GitHub
├── mcp-code-quality/                  ← Calidad de código
├── mcp-architecture/                  ← Análisis de arquitectura
├── mcp-event-driven/                  ← Event-driven architecture
├── mcp-orchestrator/                  ← Orquestación de DAGs
├── mcp-best-practices/                  ← Documentación retroactiva
├── mcp-ci-cd/                  ← Simulación de pipelines
├── mcp-design-patterns/                  ← Patrones de diseño
├── mcp-security-champion/                  ← Seguridad y compliance
├── mcp-database/                  ← Consultas SQL
├── mcp-filesystem/                  ← Filesystem sandbox
├── mcp-object-storage/                  ← Object Storage S3/MinIO
├── mcp-openapi/                  ← OpenAPI client
├── mcp-documents/                  ← Documentos PDF/DOCX/PPTX
├── mcp-browser/                  ← Automatización web
├── mcp-kubernetes/                  ← Kubernetes
├── mcp-observability/                  ← Observabilidad
├── mcp-terraform/                  ← Infraestructura como código
├── mcp-snyk/                  ← Snyk SAST/SCA
├── mcp-sonar/                  ← SonarQube/SonarCloud
├── mcp-java-build/                  ← Builds Java
├── mcp-agent-runner/                  ← Orquestación de agentes
├── mcp-personal-vault/                  ← Bóveda personal cifrada
│
├── docker-compose.yml             ← orquestación (modo HTTP / producción)
├── pyproject.toml                 ← workspace root: ruff, mypy, pytest
├── Makefile                       ← comandos operacionales
├── claude_desktop_config.json     ← config para Claude Desktop (modo stdio)
└── .env.example                   ← plantilla de variables de entorno
```
server.py          ← CAPA MCP: registra tools, maneja errores MCP, logging
    │
tools/*.py         ← CAPA DE NEGOCIO: lógica pura, sin dependencias MCP
    │
mcp_shared/        ← CAPA COMPARTIDA: config, errores, logging, modelos
```

Esto significa que puedes probar la lógica de `tools/` con tests unitarios normales, sin necesidad de levantar un servidor MCP.

---

## 4. Catálogo de servidores

### `mcp-tabular` — Archivos tabulares

Lee Excel, CSV, TSV, ODS y Parquet; filtra, agrega y exporta a JSON.

| Tool | Qué hace |
|------|----------|
| `read_tabular_file` | Lee un archivo tabular (Excel, CSV, TSV, ODS, Parquet) y retorna los datos en formato JSON. Detecta automáticamente el encoding para archivos CSV/TSV. Parámetros: path (ruta al archivo), sheet (nombre de hoja para Excel/ODS, opcional), encoding ('auto' o nombre de encoding como 'utf-8', 'latin-1'). Retorna: columns (metadatos de columnas), records (filas como dicts), total_rows, returned_rows, truncated, metadata, warnings. |
| `get_sheet_names` | Retorna la lista de nombres de hojas de un archivo Excel (.xlsx, .xls) u ODS. No aplica para CSV, TSV ni Parquet. Parámetro: path (ruta al archivo). Retorna: lista de strings con los nombres de las hojas en orden. |
| `get_file_summary` | Retorna estadísticas completas de un archivo tabular: shape (filas × columnas), tipos de datos, conteo de nulos por columna, y estadísticas descriptivas (mean, std, min, max, percentiles) de columnas numéricas. Parámetros: path (ruta al archivo), sheet (hoja para Excel/ODS, opcional). Retorna: dict con shape, columns, dtypes, null_counts, null_percentages, numeric_describe, size_bytes, size_mb. |
| `read_specific_sheet` | Lee una hoja específica de un archivo Excel (.xlsx, .xls) u ODS por nombre exacto. Retorna un error descriptivo si la hoja no existe, indicando las hojas disponibles. Parámetros: path (ruta al archivo), sheet_name (nombre exacto de la hoja). Retorna: mismo formato que read_tabular_file. |
| `filter_rows` | Filtra filas de un archivo tabular según un criterio en una columna. Operadores soportados: eq (igual), ne (diferente), gt (mayor), lt (menor), gte (mayor o igual), lte (menor o igual), contains (contiene substring, case-insensitive), startswith (empieza con, case-insensitive). Parámetros: path, column (nombre de columna), operator (ver lista), value (valor a comparar como string), sheet (opcional). El valor se convierte automáticamente al tipo de la columna para comparaciones numéricas. Retorna: mismo formato que read_tabular_file pero solo con las filas que cumplen el filtro. |
| `search_in_file` | Busca un texto en todas las columnas del archivo tabular (búsqueda case-insensitive). Retorna todas las celdas que contienen el texto buscado, con el contexto completo de la fila. Parámetros: path, query (texto a buscar), sheet (opcional), max_results (máximo de resultados, por defecto 100). Retorna: lista de matches con row_index, column, value y row (fila completa). |
| `convert_to_csv` | Convierte un archivo tabular (Excel, ODS, Parquet) a formato CSV. Retorna el contenido CSV completo como string, incluyendo encabezados. Útil para exportar datos o usar en otros sistemas que solo aceptan CSV. Parámetros: path, sheet (nombre de hoja para Excel/ODS, opcional), output_encoding (encoding del CSV de salida, por defecto 'utf-8'). Retorna: string con el contenido CSV completo. |
| `get_column_stats` | Retorna estadísticas detalladas de una columna específica del archivo. Para columnas numéricas: mean, std, min, max, percentiles, skewness, kurtosis. Para columnas de texto: value_counts top-10, most_frequent, avg/min/max length. Para columnas de fecha: min_date, max_date, date_range_days. Para todas: null_count, null_percentage, unique_count, dtype, total_count. Parámetros: path, column (nombre exacto de la columna), sheet (opcional). Retorna: dict con stats adaptadas al tipo de la columna. |
| `sort_rows` | Ordena las filas del archivo por una o más columnas. Parámetros: path, by (nombre de columna o lista), ascending (bool, default true), sheet (opcional). Retorna: mismo formato que read_tabular_file con las filas ordenadas. |
| `drop_columns` | Elimina columnas específicas del archivo. Parámetros: path, columns (nombre o lista de columnas a eliminar), sheet (opcional). Retorna: mismo formato que read_tabular_file sin las columnas eliminadas. |
| `select_columns` | Selecciona solo las columnas especificadas, descartando las demás. Parámetros: path, columns (nombre o lista de columnas a conservar), sheet (opcional). Retorna: mismo formato que read_tabular_file con solo las columnas seleccionadas. |
| `rename_columns` | Renombra columnas del archivo usando un diccionario {nombre_antiguo: nombre_nuevo}. Parámetros: path, mapping (dict de renombrado), sheet (opcional). Retorna: mismo formato que read_tabular_file con las columnas renombradas. |
| `fill_nulls` | Rellena valores nulos (NaN) con un valor dado. Parámetros: path, value (valor de relleno, default 0), columns (lista opcional de columnas a rellenar; si es None, rellena todas), sheet (opcional). Retorna: mismo formato que read_tabular_file con los nulos rellenados. |
| `drop_nulls` | Elimina filas que contienen valores nulos. Parámetros: path, how ('any' = cualquier nulo, 'all' = todos nulos, default 'any'), subset (columnas específicas a considerar, opcional), sheet (opcional). Retorna: mismo formato que read_tabular_file sin las filas con nulos. |
| `drop_duplicates` | Elimina filas duplicadas del archivo. Parámetros: path, subset (columnas a considerar para duplicados, opcional), keep ('first' = mantener primero, 'last' = mantener último, 'false' = eliminar todos), sheet (opcional). Retorna: mismo formato que read_tabular_file sin duplicados. |
| `groupby_agg` | Agrupa filas por una o más columnas y aplica una función de agregación. Funciones soportadas: mean, sum, min, max, count, median, std, var, first, last, nunique. Parámetros: path, by (columna o lista de agrupación), agg_func (función de agregación), sheet (opcional). Retorna: mismo formato que read_tabular_file con el resultado agrupado. |
| `pivot_table` | Crea una tabla pivot desde el archivo tabular. Parámetros: path, index (columna de filas), columns (columna de columnas), values (columna de valores), aggfunc (función de agregación, default 'mean'), sheet (opcional). Retorna: mismo formato que read_tabular_file con la tabla pivot. |
| `melt_table` | Convierte el archivo de formato ancho a largo (unpivot/melt). Parámetros: path, id_vars (columnas que se mantienen), value_vars (columnas a despivotar, opcional), sheet (opcional). Retorna: mismo formato que read_tabular_file en formato largo. |
| `sample_rows` | Retorna una muestra aleatoria de n filas del archivo. Parámetros: path, n (número de filas, default 10), random_state (semilla, opcional), sheet (opcional). Retorna: mismo formato que read_tabular_file con la muestra. |
| `head_rows` | Retorna las primeras n filas del archivo. Parámetros: path, n (número de filas, default 10), sheet (opcional). Retorna: mismo formato que read_tabular_file. |
| `tail_rows` | Retorna las últimas n filas del archivo. Parámetros: path, n (número de filas, default 10), sheet (opcional). Retorna: mismo formato que read_tabular_file. |
| `convert_to_json` | Convierte un archivo tabular a formato JSON. Parámetros: path, sheet (opcional), orient ('records', 'index', 'columns', 'values', 'split'). Retorna: string JSON completo. |
| `convert_to_markdown` | Convierte un archivo tabular a tabla Markdown. Parámetros: path, sheet (opcional), max_rows (límite de filas, default 50). Retorna: string con tabla Markdown. |
| `get_duplicates_info` | Reporta filas duplicadas en el archivo con conteo y muestra. Parámetros: path, subset (columnas a considerar, opcional), sheet (opcional). Retorna: dict con total_rows, duplicate_rows, duplicate_percentage, sample_duplicates. |
| `get_correlation` | Calcula la matriz de correlación entre columnas numéricas. Métodos soportados: pearson, spearman, kendall. Parámetros: path, method (default 'pearson'), sheet (opcional). Retorna: dict con la matriz de correlación. |

**Caso de uso típico:** Analiza ventas_Q1.xlsx y muestra las 5 categorías con más ingresos.

---

### `mcp-calendar` — Días hábiles y divisas

Calcula días hábiles y feriados para más de 100 países y consulta tasas de cambio vía Frankfurter.

| Tool | Qué hace |
|------|----------|
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

**Caso de uso típico:** Calcula fechas de entrega entre México y Alemania y convierte montos a EUR.

---

### `mcp-markdown` — Archivos Markdown

Lee, analiza, valida y transforma archivos Markdown: headings, links, code blocks, frontmatter.

| Tool | Qué hace |
|------|----------|
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

**Caso de uso típico:** Genera un resumen de /docs o valida que no haya enlaces rotos.

---

### `mcp-prompt-engineer` — Ingeniería de prompts

Analiza, mejora, clasifica y genera variaciones de prompts para LLMs.

| Tool | Qué hace |
|------|----------|
| `analyze_prompt` | Analiza un prompt de LLM de forma exhaustiva usando heurísticas reales. Detecta: tokens estimados, conteo de palabras, idioma, tipo de prompt, puntuación de claridad (0–10), problemas (críticos/warnings/info) y fortalezas. Parámetros: prompt (texto a analizar), target_model (modelo objetivo opcional: 'gpt-4', 'claude-3-5', etc.). Retorna: token_count, word_count, language, prompt_type, clarity_score, issues, strengths, suggestions, has_role, has_examples, has_format_spec. |
| `classify_prompt` | Clasifica el tipo de un prompt con una puntuación de confianza. Tipos posibles: instruction (tarea directa), question (pregunta abierta), closed_question (sí/no), few_shot (con ejemplos), system (system prompt), conversation (conversacional), creative (creativo), code (código). Parámetro: prompt (texto a clasificar). Retorna: type, confidence, indicators_found. |
| `estimate_tokens` | Estima el número de tokens para un texto en múltiples modelos de lenguaje. Usa tiktoken para modelos OpenAI y heurísticas para Claude. También indica si el texto cabe en el contexto de cada modelo. Parámetros: text (texto a analizar), model (modelo de referencia, por defecto 'gpt-4o'). Retorna: text_length, word_count, method, tokens (por modelo), context_fit. |
| `improve_prompt` | Mejora automáticamente un prompt aplicando buenas prácticas de prompt engineering. Las mejoras son heurísticas: agrega contexto, clarifica instrucciones, añade formato si falta, elimina ambigüedades. Parámetros: prompt (prompt original), goal (objetivo del prompt, opcional), target_model (modelo objetivo, opcional), style (estilo deseado: formal | casual | technical | simple | concise, opcional). Retorna: original, improved, changes (lista de cambios aplicados), score_before, score_after, improvement_delta. |
| `generate_variations` | Genera N variaciones del prompt con diferentes enfoques de prompt engineering: role_injection (añade rol experto), chain_of_thought (razonamiento paso a paso), structured_output (plantilla de salida), concise (versión condensada), audience_context (adapta para audiencia específica). Parámetros: prompt (prompt base), n (número de variaciones, 1–10, por defecto 3). Retorna: lista de variaciones con variation, approach, description, clarity_score. |
| `create_system_prompt` | Crea un system prompt estructurado y completo a partir de componentes. Parámetros: role (rol o persona del asistente, ej: 'experto en finanzas'), context (contexto de uso o empresa), constraints (restricciones o reglas a seguir, opcional). Retorna: system_prompt (texto listo para usar como system message). |
| `decompose_task` | Descompone una tarea compleja en subtareas numeradas y manejables. Útil para tareas de múltiples pasos que abruman al modelo en un solo prompt. Parámetro: task (descripción de la tarea compleja). Retorna: lista de subtareas con step, title, description, prompt_suggestion. |
| `get_prompt_template` | Retorna un template de prompt optimizado para un caso de uso específico. Casos de uso disponibles: analysis, code_review, code_generation, writing, translation, summarization, classification, extraction, qa, brainstorming, debugging, documentation, refactoring, testing, explanation. Parámetro: use_case (nombre del caso de uso). Retorna: use_case, template, placeholders (variables a reemplazar), description, tips. |

**Caso de uso típico:** Optimiza un prompt de soporte al cliente para mayor claridad.

---

### `mcp-structured-output` — Structured Output (LLMs JSON Schema)

Invoca LLMs (Bedrock, OpenAI-compatible) con salida forzada a JSON Schema; incluye validación y generación de schemas.

| Tool | Qué hace |
|------|----------|
| `invoke_structured` | Llama a un LLM y garantiza que la respuesta cumpla un JSON Schema. Proveedores: bedrock-converse | bedrock-invoke-claude | bedrock-invoke-openweight | openai-compatible. Credenciales AWS vía entorno/perfil boto3. Parámetros: prompt, schema, schema_name (default 'response'), provider, model_id, system_prompt, max_tokens (default 2048), temperature (default 0.0), region (AWS), base_url (solo openai-compatible). |
| `validate_schema` | Valida localmente que un JSON Schema sea compatible con Bedrock structured output (Draft 2020-12). Detecta: schemas recursivos, $ref externos, additionalProperties != false, constraints numéricas/string no soportadas, minItems fuera de [0,1], enum con tipos complejos. No hace llamadas a AWS. Retorna: valid (bool), issues (lista con path, message, severity). |
| `generate_schema` | Genera un JSON Schema Bedrock-compatible a partir de un objeto JSON de ejemplo. Infiere tipos automáticamente y aplica additionalProperties: false. Parámetros: example (dict JSON), name (nombre del schema, default 'schema'), description (opcional), strict (bool, default true — marca todos los campos como required). Retorna: schema (dict), field_count (int), warnings (list). |
| `sanitize_schema` | Transforma un JSON Schema para que sea compatible con Bedrock structured output. Elimina/transforma automáticamente: constraints numéricas (minimum, maximum, multipleOf), constraints de string (minLength, maxLength), additionalProperties != false, $ref externos, minItems fuera de [0,1], valores complejos en enum. El schema original NO se modifica. Retorna: sanitized (dict), changes (lista con path, action, reason), was_valid (bool). |

**Caso de uso típico:** Extrae entidades estructuradas de texto o genera un schema compatible con Bedrock.

---

### `mcp-fetch` — HTTP y web scraping

Realiza peticiones GET/POST, extrae texto de HTML y consume JSON.

| Tool | Qué hace |
|------|----------|
| `fetch_url` | Realiza un GET HTTP y devuelve el contenido crudo + metadatos. Parámetros: url (requerido), headers (dict opcional), timeout (segundos, default 30), max_bytes (default 5MB). Retorna: url, status_code, content_type, content, truncated, headers, elapsed_ms. |
| `fetch_post` | Realiza un POST HTTP con cuerpo JSON o form-data. Parámetros: url (requerido), json_body (dict para application/json), form_data (dict para form-urlencoded), headers, timeout, max_bytes. Solo uno de json_body o form_data puede estar presente. Retorna: url, status_code, content_type, content, truncated, headers, elapsed_ms. |
| `extract_text` | Descarga una página HTML y extrae el texto limpio (sin tags HTML, scripts ni estilos). Ideal para leer documentación: Spring Boot docs, Kafka docs, Kubernetes docs, Terraform registry, Javadoc, Stack Overflow, artículos, etc. Parámetros: url (requerido), headers, timeout, include_links (bool, default false), include_title (bool, default true). Retorna: url, title, text, word_count, links (si include_links=true), status_code. |
| `fetch_json` | Descarga una URL y parsea la respuesta como JSON. Opcionalmente navega el resultado con un path tipo 'data.items[0].name'. Ideal para consultar APIs REST: GitHub API, Docker Hub API, Kubernetes API, Terraform Cloud API, Kafka REST Proxy, Spring Boot Actuator, etc. Parámetros: url (requerido), headers, timeout, jq_path (string opcional, notación punto+índice). Retorna: url, data (JSON completo o sub-valor), status_code, path_used. |

**Caso de uso típico:** Obtén el contenido de una API REST o extrae el artículo de una página de noticias.

---

### `mcp-docker` — Gestión Docker

Lista contenedores, imágenes, logs, exec y gestiona el ciclo de vida de contenedores e imágenes.

| Tool | Qué hace |
|------|----------|
| `containers_list` | Lista contenedores Docker. Parámetros: all_containers (bool, default false = solo running), filters (dict opcional, ej: {"name": "web", "status": "running"}). Retorna: containers[], count, showing. |
| `containers_stats` | Estadísticas de recursos de un contenedor: CPU %, memoria MB, red, disco. Parámetros: container_id (ID o nombre, requerido). Retorna: cpu_percent, memory_mb, memory_limit_mb, memory_percent, net_rx_mb, net_tx_mb, block_read_mb, block_write_mb. |
| `container_logs` | Obtiene los logs de un contenedor. Parámetros: container_id (requerido), lines (int, default 100), since (str opcional, ej: '1h', '30m', '2024-01-01T10:00:00'), timestamps (bool, default false). Retorna: logs (texto), container_id, container_name, lines_requested, status. |
| `container_exec` | Ejecuta un comando dentro de un contenedor en ejecución (debe estar running). Parámetros: container_id (requerido), command (string, requerido), workdir (string opcional), user (string opcional, ej: 'root'), environment (dict opcional). Retorna: exit_code, output, success, container_id, command. |
| `run_container` | Crea y arranca un contenedor Docker. Parámetros: image (requerido, ej: 'nginx:latest'), command (string opcional), name (string opcional), detach (bool, default true = background), ports (dict container→host, ej: {'80': '8080'}), environment (dict), volumes (dict host_path→container_path), remove_on_exit (bool, default false). Retorna: id, name, status, image, ports. |
| `stop_container` | Detiene un contenedor Docker en ejecución. Parámetros: container_id (ID o nombre, requerido), timeout (int segundos antes de SIGKILL, default 10), remove (bool, si True elimina tras detener, default false). Retorna: container_id, name, action, removed. |
| `images_list` | Lista imágenes Docker locales. Parámetros: name (string opcional, filtrar por nombre/tag), dangling (bool, incluir imágenes sin tag, default false). Retorna: images[], count. |
| `image_pull` | Descarga una imagen Docker desde un registry (Docker Hub, ECR, GHCR, etc.). Parámetros: image (requerido, ej: 'nginx', 'python', 'my-registry/app'), tag (string, default 'latest'). Retorna: image, tag, id, tags[], size_mb. |

**Caso de uso típico:** Consulta logs de un contenedor o ejecuta un comando ad-hoc sin abrir la terminal.

---

### `mcp-kafka` — Apache Kafka

Lista topics, describe configuraciones, produce y consume mensajes, revisa consumer groups.

| Tool | Qué hace |
|------|----------|
| `topics_list` | Lista todos los topics del cluster Kafka. Parámetros: prefix (string opcional, filtrar por prefijo), exclude_internal (bool, default true, excluye topics __). Retorna: topics[], count, cluster_id, broker_count. |
| `topic_describe` | Describe un topic Kafka: particiones, líder, réplicas e ISR. Parámetros: topic (requerido). Retorna: topic, partition_count, replication_factor, partitions[]. |
| `consumer_groups_list` | Lista todos los consumer groups del cluster Kafka. Parámetros: prefix (string opcional, filtrar por prefijo). Retorna: groups[], count, errors[]. |
| `consumer_group_offsets` | Obtiene los offsets actuales de un consumer group. Parámetros: group_id (requerido), topics (list de strings opcional). Retorna: group_id, offsets[] (topic, partition, offset), partition_count. |
| `produce_message` | Produce un mensaje en un topic Kafka. Parámetros: topic (requerido), value (string o dict → se serializa como JSON), key (string opcional), partition (int opcional), headers (dict opcional). Retorna: topic, partition, offset, timestamp_ms, key, value_size_bytes. |
| `consume_messages` | Consume mensajes de un topic Kafka. Parámetros: topic (requerido), group_id (default 'mcp-kafka-consumer'), max_messages (int, default 50), from_beginning (bool, default false), timeout (float segundos, default 5), parse_json (bool, default true). Retorna: topic, group_id, messages[] (partition, offset, key, value, timestamp_ms, headers), count. |

**Caso de uso típico:** Depura un consumer group atascado o publica un mensaje de prueba en un topic.

---

### `mcp-project-memory` — Memoria de proyecto persistente

Mantiene estado, decisiones, tareas y snapshots entre sesiones de agentes de IA.

| Tool | Qué hace |
|------|----------|
| `get_project_state` | Retorna el estado completo del proyecto: componentes, decisiones activas, tareas pendientes, invariantes y resumen de la última sesión. LLAMA ESTE TOOL AL INICIO DE CADA SESIÓN para recuperar el contexto completo. |
| `generate_project_brief` | Genera un resumen ejecutivo del proyecto en Markdown. Ideal para iniciar una nueva sesión con un agente que no tiene contexto previo. |
| `get_component_map` | Retorna el mapa de todos los componentes del proyecto con su estado, versión, número de tools y descripción. |
| `get_decisions_history` | Retorna el historial de decisiones de arquitectura y diseño. Parámetro opcional status_filter: 'active', 'superseded' o 'rejected'. |
| `get_session_history` | Retorna el historial de sesiones de trabajo registradas, ordenadas de más reciente a más antigua. Parámetro limit: máximo de sesiones a retornar (default 20). |
| `search_memory` | Búsqueda de texto en toda la memoria del proyecto: decisiones, tareas, sesiones e invariantes. Parámetro query: texto a buscar (mínimo 2 caracteres). |
| `diff_state` | Compara el estado actual del proyecto con el estado al finalizar una sesión anterior. Muestra componentes nuevos, decisiones tomadas y tareas completadas desde esa sesión. Parámetro session_id: ID de la sesión a comparar (ej: 'SES-0003'). |
| `export_memory_snapshot` | Exporta toda la memoria del proyecto como JSON estructurado. Útil para backup, migración o inspección completa del estado. |
| `snapshot_session` | Guarda un snapshot de la sesión de trabajo actual. LLAMA ESTE TOOL AL FINALIZAR CADA SESIÓN para preservar el contexto. Parámetros: summary (resumen de lo hecho), changes_made (lista de archivos/componentes modificados), decisions_taken (int), tasks_completed (int), agent (nombre del agente). |
| `update_component_status` | Actualiza o registra un componente del proyecto. Parámetros: component_name (ej: 'mcp-tabular'), status ('draft'|'ready'|'deprecated'), version (ej: '1.0.0'), description (str), tools (int), port (int). |
| `record_decision` | Registra una decisión de arquitectura o diseño con su justificación. Parámetros: title (título conciso), rationale (justificación), alternatives_rejected (lista de alternativas descartadas), tags (lista de etiquetas). |
| `add_pending_task` | Agrega una tarea pendiente al backlog del proyecto. Parámetros: title (descripción corta), context (detalles), priority ('high'|'medium'|'low'). |
| `complete_pending_task` | Marca una tarea pendiente como completada. Parámetros: task_id (ej: 'TASK-0001'), resolution (cómo se resolvió). |
| `initialize_project` | Inicializa o actualiza los datos base del proyecto en la memoria. Idempotente: no borra sesiones ni decisiones existentes. Parámetros: project_name, description, tech_stack (lista), invariants (reglas que nunca deben violarse). |
| `sync_from_filesystem` | Escanea el filesystem del proyecto y registra automáticamente los directorios 'mcp-*' detectados como componentes en la memoria. No elimina componentes existentes. Parámetro project_root: ruta raíz del proyecto (default: directorio actual). |

**Caso de uso típico:** Recupera el contexto completo al inicio de una sesión y guárdalo al finalizar.

---

### `mcp-llm-router` — Ruteo inteligente de LLMs

Rutea tareas entre modelos locales (LM Studio) y modelos en la nube según complejidad, privacidad y tokens.

| Tool | Qué hace |
|------|----------|
| `route_task` | Analiza un prompt y decide qué modelo usar: local (LM Studio) o nube. Retorna destination, model recomendado, task_type, complexity_score (1-10), estimated_tokens y razonamiento de la decisión. Parámetros: prompt (obligatorio), context (contexto adicional), force_local (bool), force_cloud (bool). |
| `estimate_task_complexity` | Evalúa la complejidad de un prompt (score 1-10) sin tomar decisión de ruteo. Retorna complexity_score, task_type, estimated_tokens, complexity_label y factores. Parámetros: prompt, context (opcional). |
| `get_routing_config` | Retorna la configuración actual del router: modelos locales asignados por rol, modelo de nube, umbrales de complejidad y tokens, modo privacidad. |
| `get_routing_history` | Retorna el historial de decisiones de ruteo tomadas por el servidor. Muestra destination, model, task_type y complexity_score por decisión. Parámetro limit: máximo de entradas (default 50). |
| `check_lmstudio_health` | Verifica si LM Studio está corriendo y lista los modelos disponibles. Retorna status, available_models y model_count. Parámetro timeout: segundos de espera (default 5). |
| `list_local_models` | Lista todos los modelos disponibles en LM Studio con sus metadatos completos (id, object, etc.). Útil para verificar qué modelos están cargados. |
| `call_local_model` | Ejecuta un prompt directamente en un modelo local de LM Studio. Retorna response_text, tokens_used y elapsed_seconds. Parámetros: prompt, model (nombre en LM Studio), system (prompt de sistema), temperature (0-2, default 0.7), max_tokens (default 2048). |
| `call_cloud_model` | Ejecuta un prompt en el modelo de nube configurado (Anthropic o OpenAI). Requiere ROUTER_CLOUD_API_KEY configurado en el .env. Retorna response_text, tokens_used y elapsed_seconds. Parámetros: prompt, system (prompt de sistema), temperature (default 0.7), max_tokens (default 4096). |

**Caso de uso típico:** Delega una pregunta simple a un modelo local y una tarea compleja a Claude.

---

### `mcp-git` — Operaciones Git

Status, diff, log, add, commit en dos pasos, pull, push y gestión de ramas.

| Tool | Qué hace |
|------|----------|
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

**Caso de uso típico:** Prepara un commit revisando el diff y confirma de forma segura.

---

### `mcp-github` — Integración GitHub

Crea issues, pull requests, comentarios y consulta diffs vía API REST de GitHub.

| Tool | Qué hace |
|------|----------|
| `github_create_issue` | Crea un issue en GitHub. Parámetros owner y repo son obligatorios si no están en .env. |
| `github_get_issue` | Obtiene información detallada de un issue por su número. |
| `github_create_pull_request` | Crea un Pull Request de la rama 'head' a 'base'. |
| `github_get_pull_request_diff` | Obtiene el diff completo de un Pull Request. |
| `github_add_issue_comment` | Agrega un comentario a un issue o Pull Request. |

**Caso de uso típico:** Abre un issue con el contexto de un error o revisa un PR desde el chat.

---

### `mcp-code-quality` — Calidad de código

Ejecuta linters, formateadores y tests sobre el proyecto.

| Tool | Qué hace |
|------|----------|
| `quality_run_lint` | Ejecuta el linter sobre el proyecto. Puedes especificar un archivo/carpeta con 'target'. |
| `quality_run_format` | Ejecuta el formateador de código. Usa check_only=True para ver qué cambiaría sin modificar. |
| `quality_run_tests` | Ejecuta los tests unitarios. Puedes pasar un archivo de tests específico con 'target'. |

**Caso de uso típico:** Verifica rápido que el código pase ruff y pytest.

---

### `mcp-architecture` — Análisis de arquitectura

Explora la estructura de un proyecto Python, analiza dependencias por AST y detecta violaciones a principios SOLID.

| Tool | Qué hace |
|------|----------|
| `arch_get_project_tree` | Retorna la estructura de carpetas y archivos del proyecto. Útil para entender la arquitectura macro. |
| `arch_analyze_dependencies` | Usa AST para extraer todas las importaciones de un archivo .py y entender su acoplamiento. |
| `arch_check_solid_principles` | Revisa un archivo buscando heurísticas como Clases Gigantes o demasiados argumentos, que violan SOLID. |

**Caso de uso típico:** Entiende el acoplamiento de un módulo nuevo o revisa si una clase cumple SOLID.

---

### `mcp-event-driven` — Event-driven architecture

Parsea esquemas de eventos, analiza coreografía y genera payloads de prueba.

| Tool | Qué hace |
|------|----------|
| `event_parse_schema` | Parsea un esquema de evento (JSON Schema o AsyncAPI) para extraer metadata y propiedades. |
| `event_analyze_choreography` | Escanea el directorio de esquemas configurado para encontrar todos los eventos registrados. |
| `event_generate_mock_payload` | Genera un payload JSON simulado para un evento, dado un arreglo de sus propiedades. |

**Caso de uso típico:** Diseña un flujo event-driven validando que los consumidores cubren todos los eventos.

---

### `mcp-orchestrator` — Orquestación de DAGs

Parsea DAGs de Airflow, valida acyclicidad y genera código boilerplate.

| Tool | Qué hace |
|------|----------|
| `orch_parse_airflow_dag` | Parsea un archivo de Python que contiene un DAG de Airflow y extrae tareas y sus dependencias (AST). |
| `orch_validate_dag` | Valida que un conjunto de aristas (dependencias) formen un grafo acíclico dirigido (DAG) válido. |
| `orch_generate_boilerplate` | Genera código Python (Airflow DAG) a partir de un dag_id y una lista de nombres de tareas. |

**Caso de uso típico:** Valida que un nuevo DAG no tenga ciclos antes de subirlo.

---

### `mcp-best-practices` — Documentación retroactiva

Mantiene actualizados docs/project-state.md y docs/servers-reference.md escaneando el repositorio.

| Tool | Qué hace |
|------|----------|
| `bp_update_project_state` | Genera o actualiza el archivo docs/project-state.md escaneando la estructura actual del proyecto. |
| `bp_update_servers_reference` | Genera o actualiza docs/servers-reference.md leyendo claude_desktop_config.json de la raíz. |

**Caso de uso típico:** Pídele que refresque la referencia de servidores tras agregar un nuevo MCP.

---

### `mcp-ci-cd` — Simulación de pipelines

Ejecuta pipelines CI/CD locales configurables sobre el repositorio.

| Tool | Qué hace |
|------|----------|
| `cicd_run_pipeline` | Ejecuta un pipeline local que incluye linting, testing y simulación de despliegue. |

**Caso de uso típico:** Corre un pipeline de validación antes de hacer commit.

---

### `mcp-design-patterns` — Patrones de diseño

Detecta anti-patrones en el código y sugiere patrones de diseño aplicables.

| Tool | Qué hace |
|------|----------|
| `dp_analyze_code_patterns` | Analiza un archivo Python (.py) para detectar posibles antipatrones como God Objects o Long Methods. |
| `dp_suggest_pattern` | Sugiere un patrón de diseño (GoF) basado en la descripción del problema de software a resolver. |

**Caso de uso típico:** Refactoriza una clase con muchas responsabilidades sugiriendo Strategy o Factory.

---

### `mcp-security-champion` — Seguridad y compliance

Audita código buscando secretos y funciones inseguras, y revisa compliance financiero básico.

| Tool | Qué hace |
|------|----------|
| `sec_audit_code` | Audita código fuente buscando hardcoded secrets o funciones inseguras (OWASP Top 10). |
| `sec_financial_compliance` | Revisa el cumplimiento de normativas financieras como PCI-DSS (enmascaramiento de datos, uso de HTTPS). |

**Caso de uso típico:** Revisa un archivo antes de commit en busca de tokens hardcodeados.

---

### `mcp-database` — Consultas SQL

Inspecciona esquemas y ejecuta queries SQL de forma controlada (read-only por defecto).

| Tool | Qué hace |
|------|----------|
| `database_info` | Sin descripción. |
| `database_list_tables` | Sin descripción. |
| `database_describe_table` | Sin descripción. |
| `database_query` | Sin descripción. |

**Caso de uso típico:** Consulta tablas de una base SQLite de analytics sin salir del chat.

---

### `mcp-filesystem` — Filesystem sandbox

Lista, lee, busca y escribe archivos dentro de una raíz configurable.

| Tool | Qué hace |
|------|----------|
| `filesystem_list` | Sin descripción. |
| `filesystem_read_text` | Sin descripción. |
| `filesystem_search` | Sin descripción. |
| `filesystem_write_text` | Sin descripción. |

**Caso de uso típico:** Lee logs o busca archivos de configuración dentro del proyecto.

---

### `mcp-object-storage` — Object Storage S3/MinIO

Lista buckets y objetos, sube/descarga texto, genera URLs presignadas y elimina objetos.

| Tool | Qué hace |
|------|----------|
| `storage_list_buckets` | Sin descripción. |
| `storage_list_objects` | Sin descripción. |
| `storage_object_metadata` | Sin descripción. |
| `storage_presign_download` | Sin descripción. |
| `storage_upload_text` | Sin descripción. |
| `storage_delete_object` | Sin descripción. |

**Caso de uso típico:** Sube un reporte JSON a S3 o genera una URL temporal de descarga.

---

### `mcp-openapi` — OpenAPI client

Descubre operaciones de una especificación OpenAPI y las invoca con un allowlist.

| Tool | Qué hace |
|------|----------|
| `openapi_list_operations` | Sin descripción. |
| `openapi_describe_operation` | Sin descripción. |
| `openapi_invoke` | Sin descripción. |

**Caso de uso típico:** Lista los endpoints de una API interna documentada en OpenAPI y llama uno permitido.

---

### `mcp-documents` — Documentos PDF/DOCX/PPTX

Extrae texto y metadatos de documentos de oficina.

| Tool | Qué hace |
|------|----------|
| `documents_extract` | Sin descripción. |
| `documents_metadata` | Sin descripción. |

**Caso de uso típico:** Resume el contenido de un contrato PDF o extrae diapositivas de una presentación.

---

### `mcp-browser` — Automatización web

Navega sitios con Playwright, extrae contenido visible y toma screenshots.

| Tool | Qué hace |
|------|----------|
| `browser_extract` | Sin descripción. |
| `browser_screenshot` | Sin descripción. |

**Caso de uso típico:** Lee el contenido de una documentación web o captura un screenshot de una UI.

---

### `mcp-kubernetes` — Kubernetes

Lista namespaces, pods y deployments, obtiene logs y escala deployments.

| Tool | Qué hace |
|------|----------|
| `kubernetes_list_namespaces` | Sin descripción. |
| `kubernetes_list_pods` | Sin descripción. |
| `kubernetes_list_deployments` | Sin descripción. |
| `kubernetes_pod_logs` | Sin descripción. |
| `kubernetes_scale_deployment` | Sin descripción. |

**Caso de uso típico:** Consulta logs de un pod en staging o escala un deployment ante pico de tráfico.

---

### `mcp-observability` — Observabilidad

Ejecuta queries PromQL y LogQL, y realiza health checks a endpoints.

| Tool | Qué hace |
|------|----------|
| `observability_prometheus_query` | Sin descripción. |
| `observability_loki_query` | Sin descripción. |
| `observability_health_check` | Sin descripción. |

**Caso de uso típico:** Consulta el error rate de las últimas horas o busca logs de un servicio.

---

### `mcp-terraform` — Infraestructura como código

Ejecuta comandos Terraform init, plan, validate y apply (deshabilitado por defecto).

| Tool | Qué hace |
|------|----------|
| `tf_run_cmd` | Ejecuta un comando Terraform en el proyecto. Provee los argumentos (ej. 'plan' o 'init'). |

**Caso de uso típico:** Valida un cambio de infraestructura con `terraform plan` antes de aplicar.

---

### `mcp-snyk` — Snyk SAST/SCA

Ejecuta `snyk test` sobre el proyecto y reporta vulnerabilidades en dependencias.

| Tool | Qué hace |
|------|----------|
| `snyk_run_test` | Ejecuta 'snyk test' en el proyecto actual y devuelve un reporte de vulnerabilidades. |

**Caso de uso típico:** Escanea vulnerabilidades de una rama antes del merge.

---

### `mcp-sonar` — SonarQube/SonarCloud

Ejecuta análisis de calidad con sonar-scanner y resume bugs, code smells y cobertura.

| Tool | Qué hace |
|------|----------|
| `sonar_run_scan` | Ejecuta 'sonar-scanner' en el proyecto actual y devuelve un resumen de calidad. |

**Caso de uso típico:** Obtén un resumen de deuda técnica del proyecto.

---

### `mcp-java-build` — Builds Java

Ejecuta comandos Maven y Gradle sobre proyectos Java.

| Tool | Qué hace |
|------|----------|
| `java_mvn` | Ejecuta un comando Maven en el proyecto. Provee los argumentos (ej. 'clean install'). |
| `java_gradle` | Ejecuta un comando Gradle en el proyecto. Provee los argumentos (ej. 'build'). |

**Caso de uso típico:** Compila un proyecto Spring Boot o ejecuta tests con Maven.

---

### `mcp-agent-runner` — Orquestación de agentes

Dispara webhooks (ej. n8n) y ejecuta scripts locales para delegar tareas a sub-agentes.

| Tool | Qué hace |
|------|----------|
| `agent_trigger_webhook` | Dispara un webhook REST HTTP (ej. n8n) enviando un payload en JSON. |
| `agent_run_local_script` | Ejecuta un sub-agente o script Python en local y espera su resultado. |

**Caso de uso típico:** Automatiza un workflow de n8n o ejecuta un script de mantenimiento desde Claude.

---

### `mcp-personal-vault` — Bóveda personal cifrada

Almacena y recupera contexto personal cifrado (preferencias, contactos, trayectoria).

| Tool | Qué hace |
|------|----------|
| `personal_vault_status` | Sin descripción. |
| `personal_upsert` | Sin descripción. |
| `personal_get` | Sin descripción. |
| `personal_list` | Sin descripción. |
| `search_personal_context` | Sin descripción. |
| `personal_delete` | Sin descripción. |

**Caso de uso típico:** Recuerda preferencias del usuario entre sesiones sin exponer datos sensibles.

---
## 5. Prerrequisitos e instalación

### Herramientas necesarias

| Herramienta | Para qué | Instalación |
|-------------|----------|-------------|
| Python 3.11+ | Ejecutar los servidores | [python.org](https://python.org) |
| **uv** | Gestor de paquetes y entornos | Ver abajo |
| Docker Desktop | Modo producción | [docker.com](https://docker.com) |
| Node.js / npx | MCP Inspector (opcional) | [nodejs.org](https://nodejs.org) |

### Instalar `uv`

`uv` es el gestor de paquetes de este proyecto. Es mucho más rápido que pip y maneja workspaces de Python.

```powershell
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verificar instalación
uv --version
```

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clonar e instalar el proyecto

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd mcps

# 2. Instalar todas las dependencias (crea el entorno virtual automáticamente)
uv sync --all-packages

# 3. Instalar con dev tools (para contribuir al código)
uv sync --all-packages --all-extras
uv run pre-commit install

# 4. Crear tu archivo .env
cp .env.example .env
```

Después de `uv sync`, verás una carpeta `.venv/` en la raíz. No necesitas activarla manualmente — `uv run` la usa automáticamente.

---

## 6. Uso local con Claude Desktop / Cursor / Windsurf

En modo local, el cliente de IA lanza cada servidor como un subproceso y se comunican por **stdio** (sin abrir puertos, sin red). Es la forma más simple y segura de usar los MCPs en tu máquina.

### Paso 1 — Verificar que los servidores funcionan

```bash
# Prueba rápida: inicia un servidor manualmente
cd mcp-calendar
uv run python -m mcp_calendar.server
# Debería iniciar sin errores (Ctrl+C para parar)
```

### Paso 2 — Configurar Claude Desktop

Copia el archivo `claude_desktop_config.json` de este repositorio a la carpeta de configuración de Claude Desktop:

| Sistema operativo | Ruta |
|-------------------|------|
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |

> **Importante:** actualiza las rutas absolutas dentro del JSON. Busca `C:/Users/germa/Documents/IA/mcps` y reemplázalas con tu ruta real.

```json
{
  "mcpServers": {
    "mcp-calendar": {
      "command": "uv",
      "args": [
        "--directory", "C:/TU_RUTA/mcps/mcp-calendar",
        "run", "python", "-m", "mcp_calendar.server"
      ],
      "env": {
        "LOG_LEVEL": "INFO",
        "LOG_FORMAT": "console",
        "DEFAULT_COUNTRY": "MX"
      }
    }
  }
}
```

### Paso 3 — Reiniciar Claude Desktop

Cierra y vuelve a abrir Claude Desktop. En la barra inferior verás el icono de herramientas — al hacer click verás los MCPs disponibles y sus tools.

### Configurar Cursor o Windsurf

Estos editores tienen una sección "MCP Servers" en su configuración. El formato es idéntico al de Claude Desktop.

---

## 7. Desarrollo y pruebas

### Iniciar un servidor en modo desarrollo

```bash
# Opción A: modo dev con hot-reload (recomienda para desarrollo activo)
make dev-mcp-tabular

# Opción B: ejecución directa
cd mcp-tabular
uv run python -m mcp_tabular.server

# Opción C: MCP Inspector (interfaz web visual para probar tools)
make inspect SERVER=mcp-tabular
# Abre http://localhost:5173 en el navegador
```

### Ejecutar tests

```bash
# Todos los tests del workspace
make test

# Tests de un servidor específico
make test-mcp-calendar

# Tests rápidos (sin coverage, para verificar rápido)
make test-fast

# Con coverage detallado
uv run pytest --cov=. --cov-report=html
# Abre htmlcov/index.html en el navegador
```

### Linting y formateo

```bash
# Verificar calidad del código (ruff + mypy)
make lint

# Formatear código automáticamente
make format

# Verificar que todo está en orden antes de un commit
make check
```

Pre-commit está configurado para ejecutar estas verificaciones automáticamente antes de cada `git commit`.

### Estructura de un servidor (para leer el código)

Cuando abres cualquier servidor, encontrarás esta estructura:

```
mcp-tabular/
└── src/mcp_tabular/
    ├── __init__.py        ← versión del paquete, exports públicos
    ├── config.py          ← Settings: todas las variables de entorno del servidor
    ├── server.py          ← PUNTO DE ENTRADA: instancia FastMCP, registra tools
    └── tools/
        ├── __init__.py    ← exports públicos de las tools
        └── tabular_tools.py  ← implementación real (sin dependencias MCP)
```

**Flujo de una llamada MCP:**

```
Cliente llama tool "read_excel"
        │
        ▼
server.py: @mcp.tool("read_excel")  ← recibe parámetros validados
        │
        ▼
tools/tabular_tools.py: read_excel()  ← lógica pura, testeable
        │
        ▼
Resultado → serializado a JSON → devuelto al cliente
```

---

## 8. Despliegue en producción con Docker

Los servidores corren como contenedores HTTP y Compose publica sus puertos solo
en `127.0.0.1`. Para acceso remoto se requiere un reverse proxy con TLS y
autenticación; no expongas estos puertos directamente a Internet.

### Configurar el entorno de producción

```bash
# 1. Crear .env de producción
cp .env.example .env

# 2. Ajustar las variables clave en .env:
#    LOG_FORMAT=json          (logs JSON para ELK/Datadog)
#    LOG_LEVEL=INFO
#    MCP_TRANSPORT=streamable-http   (ya lo fija docker-compose)
#    MCP_DATA_DIR=/ruta/a/tus/datos
```

### Build y arranque

```bash
# Build de todas las imágenes (primera vez o tras cambios)
make build

# Levantar todos los servicios en background
make up

# mcp-docker requiere acceso privilegiado al socket del daemon
docker compose --profile privileged-tools up -d mcp-docker

# Kubernetes, observabilidad y Terraform
make up-platform

# Todos los perfiles opcionales, incluido S3 y Playwright
make up-extended

# Ver estado
make ps

# Ver logs en tiempo real
make logs

# Logs de un servidor específico
make logs-mcp-calendar

# Parar todo
make down
```

### Puertos expuestos

| Servidor | Puerto | URL |
|----------|--------|-----|
| `mcp-tabular` | 8001 | `http://127.0.0.1:8001/` |
| `mcp-calendar` | 8002 | `http://127.0.0.1:8002/` |
| `mcp-markdown` | 8003 | `http://127.0.0.1:8003/` |
| `mcp-prompt-engineer` | 8004 | `http://127.0.0.1:8004/` |
| `mcp-structured-output` | 8005 | `http://127.0.0.1:8005/` |
| `mcp-fetch` | 8006 | `http://127.0.0.1:8006/` |
| `mcp-docker` | 8007 | `http://127.0.0.1:8007/` |
| `mcp-kafka` | 8008 | `http://127.0.0.1:8008/` |
| `mcp-project-memory` | 8009 | `http://127.0.0.1:8009/` |
| `mcp-llm-router` | 8010 | `http://127.0.0.1:8010/` |
| `mcp-git` | 8011 | `http://127.0.0.1:8011/` |
| `mcp-github` | 8012 | `http://127.0.0.1:8012/` |
| `mcp-code-quality` | 8013 | `http://127.0.0.1:8013/` |
| `mcp-architecture` | 8014 | `http://127.0.0.1:8014/` |
| `mcp-event-driven` | 8015 | `http://127.0.0.1:8015/` |
| `mcp-orchestrator` | 8016 | `http://127.0.0.1:8016/` |
| `mcp-best-practices` | 8017 | `http://127.0.0.1:8017/` |
| `mcp-ci-cd` | 8018 | `http://127.0.0.1:8018/` |
| `mcp-design-patterns` | 8019 | `http://127.0.0.1:8019/` |
| `mcp-security-champion` | 8020 | `http://127.0.0.1:8020/` |
| `mcp-database` | 8021 | `http://127.0.0.1:8021/` |
| `mcp-filesystem` | 8022 | `http://127.0.0.1:8022/` |
| `mcp-object-storage` | 8023 | `http://127.0.0.1:8023/` |
| `mcp-openapi` | 8024 | `http://127.0.0.1:8024/` |
| `mcp-documents` | 8025 | `http://127.0.0.1:8025/` |
| `mcp-browser` | 8026 | `http://127.0.0.1:8026/` |
| `mcp-kubernetes` | 8027 | `http://127.0.0.1:8027/` |
| `mcp-observability` | 8028 | `http://127.0.0.1:8028/` |
| `mcp-terraform` | 8029 | `http://127.0.0.1:8029/` |
| `mcp-snyk` | 8030 | `http://127.0.0.1:8030/` |
| `mcp-sonar` | 8031 | `http://127.0.0.1:8031/` |
| `mcp-java-build` | 8032 | `http://127.0.0.1:8032/` |
| `mcp-agent-runner` | 8033 | `http://127.0.0.1:8033/` |
| `mcp-personal-vault` | 8034 | `http://127.0.0.1:8034/` |

### Healthcheck

Cada contenedor verifica su propia disponibilidad:

```bash
# Ver estado de salud de todos los contenedores
docker compose ps

# Verificar manualmente un servidor HTTP
python -c "import socket; socket.create_connection(('localhost', 8002), timeout=5); print('OK')"
```

### Acceso mediante reverse proxy

El endpoint público del ejemplo debe terminar TLS y exigir autenticación antes
de reenviar tráfico al puerto local:

```json
{
  "mcpServers": {
    "mcp-calendar": {
      "transport": "streamable-http",
      "url": "http://tu-servidor.com:8002/"
    }
  }
}
```

---

## 9. La librería compartida `mcp_shared`

Todos los servidores importan de `mcp_shared`. No dupliques lo que ya está ahí.

### `BaseMcpSettings` — Configuración base

La mayoría de los servidores heredan de esta clase. Markdown y Prompt Engineer
mantienen settings propios compatibles con las mismas variables globales.

```python
from mcp_shared.config import BaseMcpSettings
from pydantic import Field

class MiSettings(BaseMcpSettings):
    mi_api_key: str = Field(default="", description="API key del servicio.")
    max_items: int = Field(default=100, ge=1)

settings = MiSettings()
# Lee MCP_HOST, MCP_PORT, MCP_TRANSPORT, LOG_LEVEL, LOG_FORMAT, etc.
# + MCP_MI_API_KEY, MCP_MAX_ITEMS (si defines env_prefix="MCP_")
```

Variables que hereda **todo servidor** de `BaseMcpSettings`:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Nivel de logging |
| `LOG_FORMAT` | `json` | `json` (prod) o `console` (dev) |
| `MCP_HOST` | `0.0.0.0` | Host del servidor HTTP |
| `MCP_PORT` | `8000` | Puerto del servidor HTTP |
| `MCP_SERVER_NAME` | `mcp-server` | Nombre en logs |
| `MCP_TRANSPORT` | `stdio` | `stdio` o `streamable-http` |
| `MCP_DEBUG` | `false` | Modo debug |
| `MCP_WORKERS` | `1` | Workers del servidor |

### `setup_logging` — Logging estructurado

```python
from mcp_shared.logging import setup_logging, get_logger

# Llamar UNA vez al inicio del servidor (antes de crear FastMCP)
setup_logging(
    log_level=settings.log_level,   # "INFO", "DEBUG", etc.
    log_format=settings.log_format,  # "json" o "console"
    server_name="mi-servidor",
)

# En cualquier módulo:
logger = get_logger(__name__)
logger.info("Procesando archivo", path="/data/ventas.xlsx", rows=1500)
```

En `LOG_FORMAT=console` (desarrollo) los logs son coloridos y legibles. En `LOG_FORMAT=json` (producción) son JSON de una línea, listos para ingestar en ELK o Datadog.

### `McpError` y subclases — Errores tipados

```python
from mcp_shared.errors import (
    ValidationError,    # Parámetro inválido
    NotFoundError,      # Recurso no encontrado
    InvalidValueError,  # Valor fuera de rango
    ApiError,           # Error de API externa
    NetworkError,       # Error de red
    NetworkTimeoutError,# Timeout de red
)

# Uso en tools:
def mi_tool(path: str) -> dict:
    if not Path(path).exists():
        raise NotFoundError(resource="archivo", identifier=path)

    if len(path) > 1000:
        raise ValidationError(field="path", message="Ruta demasiado larga")
```

En `server.py` se capturan y convierten a `SdkMcpError` para que el cliente MCP reciba un error estructurado:

```python
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError

@mcp.tool("mi_tool")
def tool_mi_tool(path: str) -> dict:
    try:
        return mi_tool(path)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))
    except Exception as exc:
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor."))
```

---

## 10. Cómo crear un nuevo servidor MCP

Sigue estos pasos para agregar `mcp-database` (ejemplo):

### Paso 1 — Crear la estructura de carpetas

```
mcp-database/
├── src/
│   └── mcp_database/
│       ├── __init__.py
│       ├── config.py
│       ├── server.py
│       └── tools/
│           ├── __init__.py
│           └── database_tools.py
├── tests/
│   └── test_server.py
├── Dockerfile
└── pyproject.toml
```

### Paso 2 — `pyproject.toml`

```toml
[project]
name = "mcp-database"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.3",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "structlog>=24.1",
    "mcp-shared",        # librería compartida del workspace
    "sqlalchemy>=2.0",   # dependencia específica de este servidor
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mcp_database"]
```

### Paso 3 — `config.py`

```python
from pydantic import Field
from pydantic_settings import SettingsConfigDict
from mcp_shared.config import BaseMcpSettings

class DatabaseSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_DB_",   # lee MCP_DB_DATABASE_URL, etc.
        env_file=".env",
        extra="ignore",
    )

    database_url: str = Field(
        default="sqlite:///./data.db",
        description="URL de conexión a la base de datos.",
    )

settings = DatabaseSettings()
```

### Paso 4 — `tools/database_tools.py`

```python
# Lógica pura — sin imports de MCP ni FastMCP
from mcp_shared.errors import NotFoundError, ValidationError

def query_table(table: str, limit: int = 100) -> list[dict]:
    """Ejecuta una query SELECT sobre una tabla."""
    if not table.isidentifier():
        raise ValidationError(field="table", message="Nombre de tabla inválido.")
    # ... implementación real
    return []
```

### Paso 5 — `server.py`

```python
from __future__ import annotations
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData

from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging
from mcp_database.config import settings
from mcp_database.tools.database_tools import query_table

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-database",
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-database")
    logger.info("Servidor mcp-database iniciando", db_url=settings.database_url)
    yield
    logger.info("Servidor mcp-database detenido")


mcp = FastMCP(
    name="mcp-database",
    instructions="Servidor MCP para consultar bases de datos.",
    lifespan=lifespan,
)


@mcp.tool(
    name="query_table",
    description="Ejecuta SELECT sobre una tabla. Parámetros: table (str), limit (int, default 100).",
)
def tool_query_table(table: str, limit: int = 100) -> list[dict[str, Any]]:
    try:
        return query_table(table=table, limit=limit)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))
    except Exception as exc:
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor."))


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
```

### Paso 6 — Registrar en el workspace

**`pyproject.toml` (raíz):**
```toml
[tool.uv.workspace]
members = [
    "shared",
    "mcp-tabular",
    "mcp-calendar",
    "mcp-markdown",
    "mcp-prompt-engineer",
    "mcp-database",     # ← agregar aquí
]
```

**`docker-compose.yml`:**
```yaml
mcp-database:
  build:
    context: .
    dockerfile: mcp-database/Dockerfile
    target: runtime
  image: mcp-database:latest
  container_name: mcp-database
  restart: unless-stopped
  env_file: .env
  environment:
    MCP_TRANSPORT: streamable-http
    MCP_HOST: "0.0.0.0"
    MCP_PORT: "8005"
  ports:
    - "127.0.0.1:8009:8005"
  healthcheck:
    test: ["CMD", "python", "-c", "import socket; socket.create_connection(('localhost', 8005), timeout=5)"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 15s
```

**`claude_desktop_config.json`:**
```json
"mcp-database": {
  "command": "uv",
  "args": [
    "--directory", "C:/TU_RUTA/mcps/mcp-database",
    "run", "python", "-m", "mcp_database.server"
  ],
  "env": { "LOG_LEVEL": "INFO", "LOG_FORMAT": "console" }
}
```

### Paso 7 — Sincronizar e instalar

```bash
uv sync --all-packages
make test-mcp-database
```

---

## 11. Variables de entorno de referencia

Copia `.env.example` a `.env` y ajusta según tu entorno.

### Variables globales (todos los servidores)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | `stdio` (local) o `streamable-http` (producción) |
| `MCP_HOST` | `0.0.0.0` | Host del servidor HTTP |
| `MCP_PORT` | `8000` | Puerto base (docker-compose asigna uno por servidor) |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FORMAT` | `json` | `json` (producción) o `console` (desarrollo) |
| `MCP_DATA_DIR` | `./data` | Directorio de datos montado en Docker |

### Variables específicas por servidor

| Variable | Servidor | Descripción |
|----------|----------|-------------|
| `TABULAR_MAX_ROWS_PREVIEW` | `mcp-tabular` | Máximo de filas retornadas en una respuesta sin paginación. Si el archivo tiene más filas, se trunca y se indica en 'truncated'. Variable de entorno: TABULAR_MAX_ROWS_PREVIEW. |
| `TABULAR_MAX_FILE_SIZE_MB` | `mcp-tabular` | Tamaño máximo permitido de archivo en MB. Archivos más grandes serán rechazados con un error descriptivo. Variable de entorno: TABULAR_MAX_FILE_SIZE_MB. |
| `TABULAR_DEFAULT_ENCODING` | `mcp-tabular` | Encoding por defecto para archivos CSV y TSV cuando no se puede detectar automáticamente con chardet. Ejemplos: 'utf-8', 'latin-1', 'cp1252'. Variable de entorno: TABULAR_DEFAULT_ENCODING. |
| `TABULAR_SAMPLE_VALUES_COUNT` | `mcp-tabular` | Número de valores de muestra a incluir por columna en la respuesta. Variable de entorno: TABULAR_SAMPLE_VALUES_COUNT. |
| `TABULAR_CHARDET_CONFIDENCE_THRESHOLD` | `mcp-tabular` | Umbral mínimo de confianza para aceptar la detección de encoding con chardet. Si la confianza es menor, se usa default_encoding. Variable de entorno: TABULAR_CHARDET_CONFIDENCE_THRESHOLD. |
| `TABULAR_ALLOWED_ROOT` | `mcp-tabular` | Directorio raíz opcional al que se restringe el acceso a archivos. Variable de entorno: TABULAR_ALLOWED_ROOT. |
| `DEFAULT_COUNTRY` | `mcp-calendar` | Código de país ISO 3166-1 alpha-2 usado por defecto en todas las operaciones de calendario cuando no se especifica explícitamente. Variable de entorno: DEFAULT_COUNTRY. |
| `EXCHANGE_CACHE_TTL_SECONDS` | `mcp-calendar` | Tiempo de vida del caché de tasas de cambio en segundos. Rango válido: 60–86400 (1 minuto a 24 horas). Variable de entorno: EXCHANGE_CACHE_TTL_SECONDS. |
| `MCP_MARKDOWN_SERVER_NAME` | `mcp-markdown` | Nombre del servidor MCP. |
| `MCP_MARKDOWN_SERVER_VERSION` | `mcp-markdown` | Versión del servidor. |
| `MCP_MARKDOWN_MAX_FILE_SIZE_MB` | `mcp-markdown` | Tamaño máximo permitido de archivo Markdown en MB. |
| `MCP_MARKDOWN_ALLOWED_EXTENSIONS` | `mcp-markdown` | Extensiones de archivo reconocidas como Markdown. |
| `MCP_MARKDOWN_DEFAULT_MAX_TOC_DEPTH` | `mcp-markdown` | Profundidad máxima por defecto para la tabla de contenidos. |
| `MCP_MARKDOWN_VALIDATE_EXTERNAL_LINKS` | `mcp-markdown` | Si True, valida que los enlaces externos respondan (requiere red). |
| `MCP_MARKDOWN_ALLOWED_ROOT` | `mcp-markdown` | Directorio raíz opcional al que se restringe el acceso a archivos. Variable: MCP_MARKDOWN_ALLOWED_ROOT. |
| `MCP_PE_MAX_PROMPT_LENGTH` | `mcp-prompt-engineer` | Longitud máxima del prompt en caracteres. |
| `MCP_PE_MAX_VARIATIONS` | `mcp-prompt-engineer` | Número máximo de variaciones a generar. |
| `MCP_PE_DEFAULT_VARIATIONS` | `mcp-prompt-engineer` | Número por defecto de variaciones a generar. |
| `MCP_PE_DEFAULT_MODEL` | `mcp-prompt-engineer` | Modelo por defecto para estimación de tokens. |
| `MCP_PE_TIKTOKEN_CACHE_DIR` | `mcp-prompt-engineer` | Directorio de caché para modelos tiktoken (opcional). |
| `MCP_PE_SERVER_NAME` | `mcp-prompt-engineer` | Nombre del servidor MCP. |
| `MCP_PE_SERVER_VERSION` | `mcp-prompt-engineer` | Versión del servidor MCP. |
| `MCP_SO_AWS_REGION` | `mcp-structured-output` | Región AWS por defecto para Bedrock. Variable: MCP_SO_AWS_REGION. |
| `MCP_SO_AWS_PROFILE` | `mcp-structured-output` | Perfil AWS opcional (boto3 credential chain). Variable: MCP_SO_AWS_PROFILE. |
| `MCP_SO_DEFAULT_PROVIDER` | `mcp-structured-output` | Proveedor por defecto: bedrock-converse | bedrock-invoke-claude | bedrock-invoke-openweight | openai-compatible. Variable: MCP_SO_DEFAULT_PROVIDER. |
| `MCP_SO_DEFAULT_MODEL_ID` | `mcp-structured-output` | ID del modelo por defecto. Variable: MCP_SO_DEFAULT_MODEL_ID. |
| `MCP_SO_DEFAULT_MAX_TOKENS` | `mcp-structured-output` | Max tokens por defecto. Variable: MCP_SO_DEFAULT_MAX_TOKENS. |
| `MCP_SO_DEFAULT_TEMPERATURE` | `mcp-structured-output` | Temperature por defecto (0.0 recomendado para structured output). Variable: MCP_SO_DEFAULT_TEMPERATURE. |
| `MCP_SO_OPENAI_BASE_URL` | `mcp-structured-output` | URL base para endpoints OpenAI-compatible. Variable: MCP_SO_OPENAI_BASE_URL. |
| `MCP_SO_OPENAI_API_KEY` | `mcp-structured-output` | API key para endpoints OpenAI-compatible. Variable: MCP_SO_OPENAI_API_KEY. |
| `MCP_FETCH_DEFAULT_TIMEOUT` | `mcp-fetch` | Timeout en segundos para peticiones HTTP. Variable: MCP_FETCH_DEFAULT_TIMEOUT. |
| `MCP_FETCH_MAX_CONTENT_LENGTH` | `mcp-fetch` | Tamaño máximo de respuesta en bytes (default 5 MB). Variable: MCP_FETCH_MAX_CONTENT_LENGTH. |
| `MCP_FETCH_USER_AGENT` | `mcp-fetch` | User-Agent enviado en peticiones. Variable: MCP_FETCH_USER_AGENT. |
| `MCP_FETCH_FOLLOW_REDIRECTS` | `mcp-fetch` | Seguir redirecciones HTTP. Desactivado por defecto para reducir riesgo SSRF. Variable: MCP_FETCH_FOLLOW_REDIRECTS. |
| `MCP_FETCH_ALLOW_PRIVATE_NETWORKS` | `mcp-fetch` | Permitir destinos loopback, privados, link-local o reservados. Variable: MCP_FETCH_ALLOW_PRIVATE_NETWORKS. |
| `MCP_FETCH_VERIFY_SSL` | `mcp-fetch` | Verificar certificados SSL. Variable: MCP_FETCH_VERIFY_SSL. |
| `MCP_DOCKER_DOCKER_HOST` | `mcp-docker` | URL del daemon Docker. None = usa DOCKER_HOST del entorno o socket por defecto. Variable: MCP_DOCKER_DOCKER_HOST. Ej: unix:///var/run/docker.sock o tcp://host:2376 |
| `MCP_DOCKER_LOG_LINES` | `mcp-docker` | Número de líneas de logs a retornar por defecto. Variable: MCP_DOCKER_LOG_LINES. |
| `MCP_DOCKER_EXEC_TIMEOUT` | `mcp-docker` | Timeout en segundos para exec en contenedor. Variable: MCP_DOCKER_EXEC_TIMEOUT. |
| `MCP_KAFKA_BOOTSTRAP_SERVERS` | `mcp-kafka` | Brokers Kafka (comma-separated). Variable: MCP_KAFKA_BOOTSTRAP_SERVERS. Ej: localhost:9092 o broker1:9092,broker2:9092 |
| `MCP_KAFKA_SECURITY_PROTOCOL` | `mcp-kafka` | Protocolo de seguridad: PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL. Variable: MCP_KAFKA_SECURITY_PROTOCOL. |
| `MCP_KAFKA_SASL_MECHANISM` | `mcp-kafka` | Mecanismo SASL: PLAIN, SCRAM-SHA-256, SCRAM-SHA-512. Variable: MCP_KAFKA_SASL_MECHANISM. |
| `MCP_KAFKA_SASL_USERNAME` | `mcp-kafka` | Usuario SASL. Variable: MCP_KAFKA_SASL_USERNAME. |
| `MCP_KAFKA_SASL_PASSWORD` | `mcp-kafka` | Contraseña SASL. Variable: MCP_KAFKA_SASL_PASSWORD. |
| `MCP_KAFKA_SSL_CA_LOCATION` | `mcp-kafka` | Ruta al CA certificate para SSL. Variable: MCP_KAFKA_SSL_CA_LOCATION. |
| `MCP_KAFKA_CONSUME_TIMEOUT` | `mcp-kafka` | Timeout en segundos para consumir mensajes. Variable: MCP_KAFKA_CONSUME_TIMEOUT. |
| `MCP_KAFKA_MAX_CONSUME_MESSAGES` | `mcp-kafka` | Número máximo de mensajes a consumir por llamada. Variable: MCP_KAFKA_MAX_CONSUME_MESSAGES. |
| `MCP_KAFKA_ADMIN_TIMEOUT` | `mcp-kafka` | Timeout en segundos para operaciones admin (list topics, etc.). Variable: MCP_KAFKA_ADMIN_TIMEOUT. |
| `MEMORY_MEMORY_DIR` | `mcp-project-memory` | Directorio donde se almacena el archivo JSON de memoria del proyecto. Puede ser relativo al directorio de trabajo o absoluto. Variable de entorno: MEMORY_DIR. |
| `MEMORY_MEMORY_FILE` | `mcp-project-memory` | Nombre del archivo JSON que almacena la memoria del proyecto. Variable de entorno: MEMORY_FILE. |
| `MEMORY_PROJECT_NAME` | `mcp-project-memory` | Nombre del proyecto para identificación en los metadatos. Variable de entorno: MEMORY_PROJECT_NAME. |
| `MEMORY_AUTO_SYNC` | `mcp-project-memory` | Si es true, sincroniza automáticamente el estado de componentes con el filesystem al leer el estado del proyecto. Variable de entorno: MEMORY_AUTO_SYNC. |
| `MEMORY_PROJECT_ROOT` | `mcp-project-memory` | Ruta raíz del proyecto para sincronización con el filesystem. Variable de entorno: MEMORY_PROJECT_ROOT. |
| `MEMORY_MAX_SESSIONS` | `mcp-project-memory` | Número máximo de sesiones a conservar en el historial. Las más antiguas se eliminan al superar el límite. Variable de entorno: MEMORY_MAX_SESSIONS. |
| `ROUTER_LMSTUDIO_BASE_URL` | `mcp-llm-router` | URL base de la API de LM Studio (compatible con OpenAI). Variable de entorno: ROUTER_LMSTUDIO_BASE_URL. |
| `ROUTER_COMPLEXITY_THRESHOLD` | `mcp-llm-router` | Umbral de complejidad (1-10) por encima del cual se usa la nube. Tareas con score >= threshold van a la nube. Variable de entorno: ROUTER_COMPLEXITY_THRESHOLD. |
| `ROUTER_MAX_LOCAL_TOKENS` | `mcp-llm-router` | Número máximo de tokens estimados para usar modelo local. Si la tarea requiere más tokens, se ruta a la nube. Variable de entorno: ROUTER_MAX_LOCAL_TOKENS. |
| `ROUTER_PRIVACY_MODE` | `mcp-llm-router` | Si es true, fuerza el uso de modelos locales siempre. Nunca envía datos a la nube, independientemente de la complejidad. Variable de entorno: ROUTER_PRIVACY_MODE. |
| `ROUTER_HISTORY_MAX` | `mcp-llm-router` | Número máximo de entradas a conservar en el historial de ruteo. Variable de entorno: ROUTER_HISTORY_MAX. |
| `ROUTER_MODEL_FAST` | `mcp-llm-router` | Modelo local rápido para tareas simples (< complexity 3, < 2K tokens). Ejemplo: qwen3-8b. Variable de entorno: ROUTER_MODEL_FAST. |
| `ROUTER_MODEL_CODE` | `mcp-llm-router` | Modelo local especializado en código. Usado para generación, review y refactoring de código. Variable de entorno: ROUTER_MODEL_CODE. |
| `ROUTER_MODEL_REASON` | `mcp-llm-router` | Modelo local con capacidades de razonamiento (chain-of-thought). Usado para análisis complejos que no requieren la nube. Variable de entorno: ROUTER_MODEL_REASON. |
| `ROUTER_MODEL_LARGE_CONTEXT` | `mcp-llm-router` | Modelo local con ventana de contexto grande (1M tokens). Usado para tareas con mucho contexto que pueden hacerse localmente. Variable de entorno: ROUTER_MODEL_LARGE. |
| `ROUTER_CLOUD_PROVIDER` | `mcp-llm-router` | Proveedor de modelos en la nube: 'anthropic' o 'openai'. Variable de entorno: ROUTER_CLOUD_PROVIDER. |
| `ROUTER_CLOUD_MODEL` | `mcp-llm-router` | Nombre del modelo de nube a usar para tareas complejas. Variable de entorno: ROUTER_CLOUD_MODEL. |
| `ROUTER_CLOUD_API_KEY` | `mcp-llm-router` | API key del proveedor de nube. Dejar vacío si solo se usa local. Variable de entorno: ROUTER_CLOUD_API_KEY. |
| `ROUTER_LMSTUDIO_TIMEOUT_SECONDS` | `mcp-llm-router` | Timeout en segundos para llamadas a LM Studio. Variable: ROUTER_LMSTUDIO_TIMEOUT_SECONDS. |
| `ROUTER_CLOUD_TIMEOUT_SECONDS` | `mcp-llm-router` | Timeout en segundos para llamadas a la nube. Variable: ROUTER_CLOUD_TIMEOUT_SECONDS. |
| `GIT_REPO_PATH` | `mcp-git` | Ruta al repositorio Git sobre el que operará el servidor. Variable de entorno: GIT_REPO_PATH. |
| `GIT_DEFAULT_BRANCH` | `mcp-git` | Nombre de la rama principal por defecto. Variable de entorno: GIT_DEFAULT_BRANCH. |
| `GIT_ALLOW_FORCE_PUSH` | `mcp-git` | Si es true, permite al agente usar push --force (peligroso). Variable de entorno: GIT_ALLOW_FORCE_PUSH. |
| `GITHUB_TOKEN` | `mcp-github` | Personal Access Token (PAT) de GitHub para autenticación. Requerido para la mayoría de operaciones. Variable de entorno: GITHUB_TOKEN. |
| `GITHUB_OWNER` | `mcp-github` | Usuario u organización propietaria del repositorio. Variable de entorno: GITHUB_OWNER. |
| `GITHUB_REPO` | `mcp-github` | Nombre del repositorio objetivo principal. Variable de entorno: GITHUB_REPO. |
| `GITHUB_API_URL` | `mcp-github` | URL base de la API de GitHub. Útil para GitHub Enterprise Server. Variable de entorno: GITHUB_API_URL. |
| `GITHUB_TIMEOUT_SECONDS` | `mcp-github` | Timeout para peticiones a la API en segundos. |
| `CQ_PROJECT_PATH` | `mcp-code-quality` | Ruta base del proyecto a analizar. |
| `CQ_LINTER_CMD` | `mcp-code-quality` | Comando usado para linting de código. |
| `CQ_FORMATTER_CMD` | `mcp-code-quality` | Comando usado para formateo de código. |
| `CQ_TEST_CMD` | `mcp-code-quality` | Comando usado para correr tests unitarios. |
| `ARCH_PROJECT_PATH` | `mcp-architecture` | Ruta base del proyecto a analizar. |
| `EVENT_SCHEMAS_PATH` | `mcp-event-driven` | Ruta donde se almacenan los esquemas de eventos. |
| `ORCH_DAGS_PATH` | `mcp-orchestrator` | Ruta donde se almacenan los archivos de DAGs. |
| `BP_PROJECT_PATH` | `mcp-best-practices` | Ruta base del proyecto. |
| `BP_DOCS_PATH` | `mcp-best-practices` | Ruta donde se almacenará la documentación retroactiva. |
| `CICD_PROJECT_PATH` | `mcp-ci-cd` | Ruta base del proyecto. |
| `CICD_TEST_CMD` | `mcp-ci-cd` | Comando de test. |
| `CICD_LINT_CMD` | `mcp-ci-cd` | Comando de lint. |
| `CICD_DEPLOY_CMD` | `mcp-ci-cd` | Comando de despliegue. |
| `DP_PROJECT_PATH` | `mcp-design-patterns` | Ruta base del proyecto. |
| `SEC_PROJECT_PATH` | `mcp-security-champion` | Ruta base del proyecto. |
| `DATABASE_URL` | `mcp-database` | — |
| `DATABASE_READ_ONLY` | `mcp-database` | — |
| `DATABASE_MAX_ROWS` | `mcp-database` | — |
| `DATABASE_STATEMENT_TIMEOUT_SECONDS` | `mcp-database` | — |
| `FILESYSTEM_ROOT` | `mcp-filesystem` | — |
| `FILESYSTEM_ALLOW_WRITE` | `mcp-filesystem` | — |
| `FILESYSTEM_MAX_READ_BYTES` | `mcp-filesystem` | — |
| `FILESYSTEM_MAX_RESULTS` | `mcp-filesystem` | — |
| `OBJECT_STORAGE_ENDPOINT_URL` | `mcp-object-storage` | — |
| `OBJECT_STORAGE_REGION` | `mcp-object-storage` | — |
| `OBJECT_STORAGE_PROFILE` | `mcp-object-storage` | — |
| `OBJECT_STORAGE_ALLOW_WRITE` | `mcp-object-storage` | — |
| `OBJECT_STORAGE_MAX_KEYS` | `mcp-object-storage` | — |
| `OPENAPI_SPEC` | `mcp-openapi` | — |
| `OPENAPI_ALLOWED_ROOT` | `mcp-openapi` | — |
| `OPENAPI_TIMEOUT_SECONDS` | `mcp-openapi` | — |
| `OPENAPI_ALLOW_INVOKE` | `mcp-openapi` | — |
| `OPENAPI_ALLOWED_HOSTS` | `mcp-openapi` | — |
| `DOCUMENTS_ROOT` | `mcp-documents` | — |
| `DOCUMENTS_MAX_FILE_SIZE_MB` | `mcp-documents` | — |
| `DOCUMENTS_MAX_PAGES` | `mcp-documents` | — |
| `BROWSER_HEADLESS` | `mcp-browser` | — |
| `BROWSER_TIMEOUT_MS` | `mcp-browser` | — |
| `BROWSER_ALLOWED_HOSTS` | `mcp-browser` | — |
| `BROWSER_OUTPUT_DIR` | `mcp-browser` | — |
| `KUBERNETES_CONTEXT` | `mcp-kubernetes` | — |
| `KUBERNETES_NAMESPACE` | `mcp-kubernetes` | — |
| `KUBERNETES_IN_CLUSTER` | `mcp-kubernetes` | — |
| `KUBERNETES_ALLOW_WRITE` | `mcp-kubernetes` | — |
| `KUBERNETES_LOG_TAIL_LINES` | `mcp-kubernetes` | — |
| `OBSERVABILITY_PROMETHEUS_URL` | `mcp-observability` | — |
| `OBSERVABILITY_LOKI_URL` | `mcp-observability` | — |
| `OBSERVABILITY_TIMEOUT_SECONDS` | `mcp-observability` | — |
| `OBSERVABILITY_BEARER_TOKEN` | `mcp-observability` | — |
| `OBSERVABILITY_MAX_ENTRIES` | `mcp-observability` | — |
| `TF_PROJECT_PATH` | `mcp-terraform` | Ruta base donde están los archivos .tf. |
| `SNYK_PROJECT_PATH` | `mcp-snyk` | Ruta base del proyecto. |
| `SNYK_API_TOKEN` | `mcp-snyk` | Token de API de Snyk (opcional para CLI auth global). |
| `SONAR_PROJECT_PATH` | `mcp-sonar` | Ruta base del proyecto. |
| `SONAR_HOST_URL` | `mcp-sonar` | URL del servidor SonarQube. |
| `SONAR_API_TOKEN` | `mcp-sonar` | Token de API de SonarQube. |
| `JAVA_PROJECT_PATH` | `mcp-java-build` | Ruta base del proyecto Java. |
| `AGENT_PROJECT_PATH` | `mcp-agent-runner` | Ruta base del proyecto. |
| `AGENT_N8N_WEBHOOK_BASE_URL` | `mcp-agent-runner` | URL base para webhooks de n8n. |
| `AGENT_N8N_AUTH_TOKEN` | `mcp-agent-runner` | Token opcional para autenticar webhooks de n8n. |
| `PERSONAL_VAULT_DATABASE_PATH` | `mcp-personal-vault` | — |
| `PERSONAL_VAULT_KEY_FILE` | `mcp-personal-vault` | — |
| `PERSONAL_VAULT_ENCRYPTION_KEY` | `mcp-personal-vault` | — |
| `PERSONAL_VAULT_ALLOW_WRITE` | `mcp-personal-vault` | — |
| `PERSONAL_VAULT_ALLOW_HIGHLY_SENSITIVE` | `mcp-personal-vault` | — |
| `PERSONAL_VAULT_ALLOW_SECRETS` | `mcp-personal-vault` | — |
| `PERSONAL_VAULT_MAX_RESULTS` | `mcp-personal-vault` | — |

---

## 12. Referencia de comandos Makefile

```bash
# Setup
make install              # Instala todas las dependencias (uv sync)
make install-dev          # Instala con dev tools + pre-commit
make setup-env            # Crea .env desde .env.example
make status               # Verifica herramientas instaladas

# Desarrollo
make dev-mcp-tabular      # Inicia servidor con hot-reload
make run-mcp-calendar     # Ejecuta directamente un servidor
make inspect SERVER=mcp-tabular  # Abre MCP Inspector visual

# Testing
make test                 # Todos los tests con coverage
make test-mcp-calendar    # Tests de un servidor específico
make test-fast            # Tests rápidos sin coverage

# Calidad de código
make lint                 # ruff check + mypy
make format               # ruff format + ruff check --fix

# Docker (producción)
make build                # Build todas las imágenes
make build-mcp-tabular    # Build una imagen específica
make up                   # Levantar servicios sin acceso al socket Docker
docker compose --profile privileged-tools up -d mcp-docker
make down                 # Parar todos los servicios
make logs                 # Ver logs en tiempo real
make logs-mcp-calendar    # Logs de un servidor
make ps                   # Estado de los contenedores
make restart              # down + up

# Utilidades
make claude-config        # Muestra cómo configurar Claude Desktop
make clean                # Limpia __pycache__, .pytest_cache, etc.
make help                 # Lista todos los comandos disponibles
```

---

## 13. Convenciones y estándares de código

### Python
- **Versión mínima:** Python 3.11 (se usan `match`, `str | None`, `TypeAlias`, etc.)
- **Tipos:** tipo hints en todas las funciones públicas (`ANN` activado en ruff)
- **Strings:** dobles `"` siempre
- **Longitud de línea:** 100 caracteres
- **Imports:** agrupados y ordenados por isort (`I` en ruff)

### Naming
- Funciones de tool (en `server.py`): prefijo `tool_` → `tool_read_excel`
- Funciones de lógica pura (en `tools/*.py`): sin prefijo → `read_excel`
- Clases de configuración: `Settings` o `XSettings` (ej: `CalendarSettings`)
- Variables de entorno: `UPPER_SNAKE_CASE`

### Errores
- Usa **siempre** las clases de `mcp_shared.errors` en la capa de tools
- Convierte a `SdkMcpError` **solo** en `server.py`
- Nunca hagas `raise Exception("mensaje vago")` — usa la clase específica

### Logging
- Llama `setup_logging()` **una sola vez** al inicio de `server.py`
- Obtén loggers con `get_logger(__name__)` — no uses `print()`
- Incluye contexto estructurado: `logger.info("msg", key=value, otro=valor)`
- En la capa de tools, no hagas logging — solo en `server.py`

### Tests
- Cada servidor tiene su carpeta `tests/`
- Tests unitarios de `tools/*.py`: no requieren servidor MCP
- Cobertura mínima: 55% (configurado en `pyproject.toml`)

---

## 14. Preguntas frecuentes (FAQ)

**¿Por qué `uv` y no `pip` o `poetry`?**
`uv` es entre 10x y 100x más rápido que pip, maneja workspaces de Python nativamente (un solo `uv sync` instala todos los paquetes de todos los servidores) y genera lock files reproducibles. En Docker usamos la imagen oficial de `ghcr.io/astral-sh/uv` para el stage de build.

**¿Qué es un "workspace" de uv?**
Un workspace permite tener múltiples paquetes Python en un repositorio y que se referencien entre sí. El `pyproject.toml` raíz declara los miembros. `mcp_shared` se instala como un paquete real disponible para todos los servidores, sin necesidad de `sys.path` hacks.

**¿Puedo usar los MCPs desde código Python propio (sin Claude Desktop)?**
Sí. Con `MCP_TRANSPORT=streamable-http` cada servidor expone un endpoint HTTP estándar. Puedes conectarte con el cliente oficial:
```python
from fastmcp import Client

async with Client("http://localhost:8002/") as client:
    result = await client.call_tool("calculate_business_days", {
        "start_date": "2025-01-01",
        "end_date": "2025-03-31",
    })
```

**¿Por qué los Dockerfiles usan usuarios no-root?**
Buena práctica de seguridad. Si un atacante logra ejecutar código dentro del contenedor, no tiene privilegios de root en el host. Todos los Dockerfiles crean un usuario con UID 1001.

**¿Cómo depuro si una tool falla en producción?**
```bash
# 1. Ver logs del contenedor
make logs-mcp-calendar

# 2. Los logs JSON tienen: tool, error_code, error_type, mensaje
# 3. Para debug más detallado, agrega MCP_DEBUG=true y LOG_LEVEL=DEBUG en .env
# 4. Reiniciar con: make restart
```

**¿FastMCP v1 o v2?**
Este proyecto usa **FastMCP v2** (`fastmcp>=2.3`, paquete standalone). La v1 venía incluida en `mcp[cli]` de Anthropic. La v2 tiene mejor soporte para transporte HTTP, mejor manejo del lifespan y una API más limpia.

**¿Qué pasa si `MCP_TRANSPORT` no está definido?**
El default es `stdio`. El servidor arranca en modo local. Nunca fallará por falta de esta variable.

**¿Puedo agregar autenticación al transporte HTTP?**
Sí. FastMCP v2 soporta middleware ASGI. Para producción se recomienda poner un reverse proxy (nginx, Caddy) con autenticación delante de los servidores MCP, en lugar de manejar auth dentro del servidor.

---

*Última actualización: junio 2026 — FastMCP v2, Python 3.11+, uv workspaces*
