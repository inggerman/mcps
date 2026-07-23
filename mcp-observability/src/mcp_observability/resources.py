"""Resources de solo lectura para mcp-observability."""

from __future__ import annotations

import json


def observability_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-observability",
            "version": "1.0.0",
            "prometheus_url": None,
            "loki_url": None,
            "timeout_seconds": 30,
            "max_entries": 500,
        },
        indent=2,
        ensure_ascii=False,
    )


def observability_basics() -> str:
    return (
        "# Observability Basics\n\n"
        "## Tres pilares\n"
        "- Metrics: datos numericos temporales (Prometheus)\n"
        "- Logs: eventos discretos (Loki)\n"
        "- Traces: flujo de requests distribuidos (Jaeger/Tempo)\n\n"
        "## Prometheus\n"
        "- Time series database\n"
        "- PromQL: lenguaje de consulta\n"
        "- Pull model: scrapea endpoints\n"
        "- Alertmanager: gestiona alertas\n\n"
        "## Loki\n"
        "- Log aggregation system\n"
        "- LogQL: lenguaje de consulta\n"
        "- Indexa labels, no contenido\n"
        "- Compatible con Promtail\n\n"
        "## Grafana\n"
        "- Visualizacion de metrics y logs\n"
        "- Dashboards interactivos\n"
        "- Alerting integrado\n"
        "- Data sources plugables"
    )


def observability_best_practices() -> str:
    return (
        "# Observability Best Practices\n\n"
        "## Metrics\n"
        "- USE: Utilization, Saturation, Errors\n"
        "- RED: Rate, Errors, Duration\n"
        "- Four Golden Signals\n"
        "- Cardinality control\n\n"
        "## Logs\n"
        "- Structured logging (JSON)\n"
        "- Log levels: DEBUG, INFO, WARN, ERROR\n"
        "- Correlation IDs\n"
        "- No sensitive data in logs\n\n"
        "## Traces\n"
        "- Distributed tracing\n"
        "- Span context propagation\n"
        "- Sampling strategies\n"
        "- Service mesh integration\n\n"
        "## Alerting\n"
        "- Alert on symptoms, not causes\n"
        "- Runbooks en alertas\n"
        "- Avoid alert fatigue\n"
        "- SLO-based alerting\n\n"
        "## Dashboards\n"
        "- One dashboard per service\n"
        "- Show trends, not just current\n"
        "- Color coding consistent\n"
        "- Annotations para deployments"
    )


def observability_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- observability_prometheus_query(query)\n"
        "- observability_loki_query(query)\n"
        "- observability_health_check(url)\n"
        "- observability_prometheus_range(query, start, end, step)\n"
        "- observability_prometheus_targets()\n"
        "- observability_prometheus_alerts()\n"
        "- observability_prometheus_rules()\n"
        "- observability_prometheus_series(match)\n"
        "- observability_loki_labels()\n"
        "- observability_loki_label_values(label)\n"
        "- observability_check_endpoints(urls)\n"
        "- observability_prometheus_metadata()\n"
        "- observability_prometheus_status()\n"
        "- observability_loki_status()\n"
        "- observability_slo_report(slo_query, error_query)\n\n"
        "## Variables .env\n"
        "- OBSERVABILITY_PROMETHEUS_URL\n"
        "- OBSERVABILITY_LOKI_URL\n"
        "- OBSERVABILITY_BEARER_TOKEN\n"
        "- OBSERVABILITY_TIMEOUT_SECONDS"
    )


def observability_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "ValidationError: campo invalido"},
                {"code": -32002, "description": "URL no configurada"},
                {"code": -32003, "description": "Error de conexion con Prometheus/Loki"},
                {"code": -32004, "description": "Timeout en consulta"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def observability_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## No se puede conectar a Prometheus\n"
        "- Verificar OBSERVABILITY_PROMETHEUS_URL\n"
        "- Verificar conectividad de red\n"
        "- Verificar bearer token\n"
        "- Verificar que Prometheus este corriendo\n\n"
        "## No se puede conectar a Loki\n"
        "- Verificar OBSERVABILITY_LOKI_URL\n"
        "- Verificar conectividad de red\n"
        "- Verificar que Loki este ready\n"
        "- Verificar /ready endpoint\n\n"
        "## Query sin resultados\n"
        "- Verificar sintaxis PromQL/LogQL\n"
        "- Verificar time range\n"
        "- Verificar labels y matchers\n"
        "- Verificar que existan series\n\n"
        "## Timeout en consultas\n"
        "- Aumentar OBSERVABILITY_TIMEOUT_SECONDS\n"
        "- Optimizar query (reducir rango)\n"
        "- Verificar carga de Prometheus\n"
        "- Usar recording rules"
    )


def observability_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Query Prometheus\n"
        'observability_prometheus_query(query="up")\n\n'
        "## Query Loki\n"
        'observability_loki_query(query=\'{job="api"} |= "error"\')\n\n'
        "## Health check\n"
        'observability_health_check(url="http://api:8080/health")\n\n'
        "## Prometheus range query\n"
        'observability_prometheus_range(query="rate(http_requests_total[5m])", start=1700000000, end=1700003600, step="60s")\n\n'
        "## SLO report\n"
        'observability_slo_report(slo_query="http_requests_total", error_query="http_requests_total{status=~\"5..\"}")'
    )


def observability_promql_guide() -> str:
    return (
        "# PromQL Guide\n\n"
        "## Tipos de datos\n"
        "- Instant vector: una muestra por series\n"
        "- Range vector: multiples muestras en un rango\n"
        "- Scalar: numero simple\n"
        "- String: texto\n\n"
        "## Operadores\n"
        "- Aritmeticos: +, -, *, /\n"
        "- Comparacion: ==, !=, >, <\n"
        "- Logicos: and, or, unless\n\n"
        "## Funciones comunes\n"
        "- rate(): tasa por segundo\n"
        "- increase(): incremento total\n"
        "- sum(): suma\n"
        "- avg(): promedio\n"
        "- histogram_quantile(): percentiles\n"
        "- by(): agrupar\n"
        "- without(): excluir labels\n\n"
        "## Ejemplos\n"
        "- rate(http_requests_total[5m])\n"
        "- sum by(status) (rate(http_requests_total[5m]))\n"
        "- histogram_quantile(0.99, rate(http_duration_bucket[5m]))\n"
        "- up{job=\"api\"} == 0"
    )


def observability_logql_guide() -> str:
    return (
        "# LogQL Guide\n\n"
        "## Estructura\n"
        "- Log stream selector: {job=\"api\"}\n"
        "- Filter: |=, !=, |~, !~\n"
        "- Line filter: |= \"error\"\n"
        "- Label filter: | status=\"500\"\n\n"
        "## Metric queries\n"
        "- rate(): log entries por segundo\n"
        "- count_over_time(): conteo en ventana\n"
        "- bytes_over_time(): bytes en ventana\n\n"
        "## Ejemplos\n"
        "- {job=\"api\"} |= \"error\"\n"
        "- {job=\"api\"} | json | line_format \"{{.status}}\"\n"
        "- rate({job=\"api\"}[5m])\n"
        "- count_over_time({job=\"api\"} |= \"error\" [10m])\n\n"
        "## Parsing\n"
        "- | json: parse JSON logs\n"
        "- | logfmt: parse logfmt\n"
        "- | regexp: parse con regex\n"
        "- | pattern: parse con patron\n\n"
        "## Aggregations\n"
        "- sum by(status) (rate({job=\"api\"}[5m]))\n"
        "- topk(10, sum by(app) (count_over_time({app=\"\"}[1h])))"
    )


def observability_alerting() -> str:
    return (
        "# Alerting Guide\n\n"
        "## Alertmanager\n"
        "- Recibe alertas de Prometheus\n"
        "- Deduplica y agrupa\n"
        "- Rutea a receivers (email, slack, pagerduty)\n"
        "- Silencia y inhibe\n\n"
        "## Reglas de alerta\n"
        "```yaml\n"
        "groups:\n"
        "- name: api\n"
        "  rules:\n"
        "  - alert: HighErrorRate\n"
        "    expr: rate(http_requests_total{status=~\"5..\"}[5m]) > 0.1\n"
        "    for: 10m\n"
        "    labels:\n"
        "      severity: critical\n"
        "    annotations:\n"
        "      summary: \"High error rate\"\n"
        "      runbook: \"https://runbooks/high-error-rate\"\n"
        "```\n\n"
        "## Mejores practicas\n"
        "- Alertar en sintomas, no causas\n"
        "- Usar 'for' para evitar flapping\n"
        "- Incluir runbook URL\n"
        "- Severity: warning, critical\n"
        "- Evitar alertas duplicadas\n"
        "- SLO-based alerting preferido"
    )


def observability_grafana() -> str:
    return (
        "# Grafana Guide\n\n"
        "## Conceptos\n"
        "- Dashboard: coleccion de paneles\n"
        "- Panel: visualizacion individual\n"
        "- Data source: Prometheus, Loki, etc.\n"
        "- Variables: filtros dinamicos\n\n"
        "## Tipos de paneles\n"
        "- Time series: grafico de lineas\n"
        "- Stat: valor unico\n"
        "- Bar gauge: barras\n"
        "- Table: tabla de datos\n"
        "- Logs: visor de logs\n"
        "- Heatmap: densidad\n\n"
        "## Mejores practicas\n"
        "- Usar variables para multi-entorno\n"
        "- Templating con $namespace, $pod\n"
        "- Links entre dashboards\n"
        "- Annotations para eventos\n"
        "- Alerting desde Grafana\n"
        "- Versionar dashboards como JSON\n\n"
        "## Dashboards recomendados\n"
        "- Cluster overview\n"
        "- Namespace detail\n"
        "- Pod detail\n"
        "- API latency (p50, p90, p99)\n"
        "- Error rate\n"
        "- SLO dashboard"
    )


def observability_tracing() -> str:
    return (
        "# Distributed Tracing\n\n"
        "## Conceptos\n"
        "- Trace: request end-to-end\n"
        "- Span: unidad de trabajo\n"
        "- Context propagation: trace headers\n"
        "- Sampling: que traces capturar\n\n"
        "## Tools\n"
        "- Jaeger: tracing UI y storage\n"
        "- Tempo: Grafana tracing backend\n"
        "- OpenTelemetry: estandar de instrumentacion\n"
        "- Zipkin: alternativa compatible\n\n"
        "## OpenTelemetry\n"
        "- Auto-instrumentacion: Python, Java, Go\n"
        "- SDK: custom spans\n"
        "- Collector: procesa y exporta\n"
        "- Exporters: OTLP, Jaeger, Zipkin\n\n"
        "## Mejores practicas\n"
        "- Propagar trace context (W3C headers)\n"
        "- Sampling head-based o tail-based\n"
        "- Span attributes para contexto\n"
        "- Span events para errores\n"
        "- Correlacionar con metrics y logs\n\n"
        "## Analisis\n"
        "- Latency percentiles\n"
        "- Critical path analysis\n"
        "- Service dependency map\n"
        "- Error traces"
    )


def observability_slo() -> str:
    return (
        "# SLO (Service Level Objectives)\n\n"
        "## Conceptos\n"
        "- SLI: Service Level Indicator (metrica)\n"
        "- SLO: Service Level Objective (objetivo)\n"
        "- SLA: Service Level Agreement (contrato)\n"
        "- Error budget: 100% - SLO\n\n"
        "## SLIs comunes\n"
        "- Disponibilidad: requests exitosos / total\n"
        "- Latencia: p99 < threshold\n"
        "- Throughput: requests por segundo\n"
        "- Error rate: 5xx / total\n\n"
        "## SLOs tipicos\n"
        "- 99.9% disponibilidad (8.76h downtime/anio)\n"
        "- 99% latencia p99 < 500ms\n"
        "- 99.99% disponibilidad (52.6min downtime/anio)\n\n"
        "## Error budget\n"
        "- Define cuantos errores son tolerables\n"
        "- Si se agota, congelar features\n"
        "- Usar para priorizar work\n\n"
        "## Alerting SLO\n"
        "- Multi-window multi-burn rate\n"
        "- Fast burn: 1h window\n"
        "- Slow burn: 6h window\n"
        "- Alertar cuando burn rate > threshold"
    )


def observability_service_mesh() -> str:
    return (
        "# Service Mesh Observability\n\n"
        "## Istio\n"
        "- mTLS automatico\n"
        "- Telemetria: metrics, logs, traces\n"
        "- Kiali: visualizacion de mesh\n"
        "- Envoy proxy: data plane\n\n"
        "## Linkerd\n"
        "- Lightweight service mesh\n"
        "- Built-in observability\n"
        "- Grafana dashboards incluidos\n"
        "- Tap: inspeccion de trafico en vivo\n\n"
        "## Metrics del mesh\n"
        "- Request volume\n"
        "- Success rate\n"
        "- Latency (p50, p95, p99)\n"
        "- TCP connections\n\n"
        "## Beneficios\n"
        "- Observabilidad sin code changes\n"
        "- Distributed tracing automatico\n"
        "- Traffic splitting para canary\n"
        "- Circuit breaking visible\n\n"
        "## Dashboards\n"
        "- Service-to-service communication\n"
        "- Topology view\n"
        "- Workload health\n"
        "- Traffic flow"
    )


def observability_metrics_guide() -> str:
    return (
        "# Metrics Guide\n\n"
        "## Four Golden Signals\n"
        "- Latency: tiempo de respuesta\n"
        "- Traffic: volumen de requests\n"
        "- Errors: tasa de errores\n"
        "- Saturation: utilizacion de recursos\n\n"
        "## USE Method (Resources)\n"
        "- Utilization: % de uso\n"
        "- Saturation: cola de trabajo\n"
        "- Errors: errores internos\n\n"
        "## RED Method (Services)\n"
        "- Rate: requests por segundo\n"
        "- Errors: errores por segundo\n"
        "- Duration: latencia (p50, p90, p99)\n\n"
        "## Tipos de metricas\n"
        "- Counter: siempre incrementa (requests total)\n"
        "- Gauge: sube y baja (memory usage)\n"
        "- Histogram: distribucion (latency buckets)\n"
        "- Summary: quantiles precalculados\n\n"
        "## Cardinalidad\n"
        "- Mantener baja cardinalidad\n"
        "- No usar user_id, request_id como labels\n"
        "- Limitar labels a < 10 valores\n"
        "- Usar recording rules para aggregaciones\n\n"
        "## Naming conventions\n"
        "- unit_suffix: _seconds, _bytes, _total\n"
        "- namespace_metric_submetric\n"
        "- snake_case\n"
        "- Plural para counters acumulados"
    )
