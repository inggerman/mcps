"""Resources de solo lectura para mcp-agent-runner."""

from __future__ import annotations

import json


def agent_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-agent-runner",
            "version": "1.0.0",
            "webhook_base_url": "http://localhost:5678/webhook",
            "has_auth_token": False,
        },
        indent=2,
        ensure_ascii=False,
    )


def agent_basics() -> str:
    return (
        "# Agent Runner Basics\n\n"
        "## Que es Agent Runner\n"
        "- Orquestador de sub-agentes\n"
        "- Ejecuta scripts locales y remotos\n"
        "- Integracion con n8n webhooks\n"
        "- Gestiona jobs y tareas\n\n"
        "## Conceptos\n"
        "- Agent: entidad que ejecuta una tarea\n"
        "- Job: ejecucion de un agente\n"
        "- Task: definicion de trabajo recurrente\n"
        "- Webhook: trigger HTTP para n8n\n"
        "- Script: codigo Python ejecutable\n\n"
        "## Modos de ejecucion\n"
        "- Local: subprocess en misma maquina\n"
        "- Webhook: HTTP POST a n8n\n"
        "- Batch: multiples scripts en secuencia\n"
        "- Timeout: ejecucion con limite de tiempo\n\n"
        "## n8n Integration\n"
        "- Webhook trigger: inicia workflow\n"
        "- Payload: JSON con datos de entrada\n"
        "- Auth: Bearer token opcional\n"
        "- Response: JSON del workflow\n\n"
        "## Arquitectura\n"
        "- MCP server expone tools\n"
        "- LLM llama tools para delegar\n"
        "- Sub-agentes ejecutan trabajo\n"
        "- Resultados retornan al LLM"
    )


def agent_best_practices() -> str:
    return (
        "# Agent Runner Best Practices\n\n"
        "## Diseno de agentes\n"
        "- Un agente = una responsabilidad\n"
        "- Inputs y outputs bien definidos\n"
        "- Idempotente cuando sea posible\n"
        "- Manejo de errores robusto\n\n"
        "## Ejecucion\n"
        "- Usar timeout para scripts largos\n"
        "- Capturar stdout y stderr\n"
        "- Loggear progreso y resultados\n"
        "- Validar inputs antes de ejecutar\n\n"
        "## Webhooks\n"
        "- Usar HTTPS en produccion\n"
        "- Autenticar con Bearer token\n"
        "- Validar payload schema\n"
        "- Timeout en HTTP requests\n"
        "- Retry con backoff\n\n"
        "## Batch execution\n"
        "- Ordenar por dependencias\n"
        "- Parar en primer error (opcional)\n"
        "- Recopilar todos los resultados\n"
        "- Loggear cada paso\n\n"
        "## Monitoring\n"
        "- Track job status\n"
        "- Alertar en failures\n"
        "- Metrics: duracion, exito/fallo\n"
        "- Logs centralizados\n\n"
        "## Security\n"
        "- Sandboxing de scripts\n"
        "- Limitar recursos (CPU, memoria)\n"
        "- No exponer secrets en payload\n"
        "- Validar paths de scripts"
    )


def agent_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- agent_trigger_webhook(payload_json)\n"
        "- agent_run_local_script(script_path, args)\n"
        "- agent_list_scripts()\n"
        "- agent_status(job_id)\n"
        "- agent_cancel(job_id)\n"
        "- agent_logs(job_id, lines)\n"
        "- agent_results(job_id)\n"
        "- agent_create_task(name, description, script_path)\n"
        "- agent_list_tasks()\n"
        "- agent_delete_task(task_id)\n"
        "- agent_trigger_n8n_workflow(workflow_id, payload)\n"
        "- agent_run_batch(scripts, args)\n"
        "- agent_health_check()\n"
        "- agent_get_config()\n"
        "- agent_run_with_timeout(script_path, args, timeout)\n\n"
        "## Variables .env\n"
        "- AGENT_PROJECT_PATH\n"
        "- AGENT_N8N_WEBHOOK_BASE_URL\n"
        "- AGENT_N8N_AUTH_TOKEN"
    )


def agent_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "Script no encontrado"},
                {"code": -32002, "description": "Timeout en ejecucion"},
                {"code": -32003, "description": "Error en webhook HTTP"},
                {"code": -32004, "description": "Job no encontrado"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def agent_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## Script no encontrado\n"
        "- Verificar ruta del script\n"
        "- Verificar que el archivo exista\n"
        "- Usar agent_list_scripts para ver disponibles\n\n"
        "## Timeout en ejecucion\n"
        "- Aumentar timeout con agent_run_with_timeout\n"
        "- Optimizar el script\n"
        "- Verificar recursos disponibles\n\n"
        "## Error en webhook\n"
        "- Verificar URL del webhook\n"
        "- Verificar conectividad de red\n"
        "- Verificar auth token\n"
        "- Verificar payload JSON\n\n"
        "## Job no encontrado\n"
        "- Verificar job_id\n"
        "- Usar agent_list_tasks para ver tareas\n"
        "- Verificar que el job no haya expirado\n\n"
        "## n8n no responde\n"
        "- Verificar que n8n este corriendo\n"
        "- Usar agent_health_check\n"
        "- Verificar URL base\n"
        "- Verificar firewall/network\n\n"
        "## Script falla\n"
        "- Revisar stderr en resultado\n"
        "- Ejecutar script manualmente\n"
        "- Verificar dependencias del script\n"
        "- Verificar Python version"
    )


def agent_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Webhook basico\n"
        'agent_trigger_webhook(payload_json=\'{"task": "process_data"}\')\n\n'
        "## Script local\n"
        'agent_run_local_script(script_path="scripts/agent.py", args="--verbose")\n\n'
        "## Script con timeout\n"
        'agent_run_with_timeout(script_path="scripts/long.py", args="", timeout=120)\n\n'
        "## Batch execution\n"
        'agent_run_batch(scripts=["a.py", "b.py"], args="--mode=fast")\n\n'
        "## n8n workflow\n"
        'agent_trigger_n8n_workflow(workflow_id="wf-123", payload={"data": 42})\n\n'
        "## Status y logs\n"
        'agent_status(job_id="abc-123")\n'
        'agent_logs(job_id="abc-123", lines=100)\n\n'
        "## Health check\n"
        "agent_health_check()"
    )


def agent_n8n_guide() -> str:
    return (
        "# n8n Integration Guide\n\n"
        "## Que es n8n\n"
        "- Workflow automation platform\n"
        "- Node-based visual editor\n"
        "- 400+ integraciones\n"
        "- Self-hosted o cloud\n\n"
        "## Webhook trigger\n"
        "- Crear workflow con Webhook node\n"
        "- Configurar URL path\n"
        "- Method: POST\n"
        "- Response mode: Respond Immediately o Last Node\n\n"
        "## Autenticacion\n"
        "- Header: Authorization: Bearer <token>\n"
        "- Configurar en n8n Webhook node\n"
        "- O usar custom header\n\n"
        "## Payload\n"
        "- JSON body\n"
        "- n8n parsea automaticamente\n"
        "- Acceso via $json en expressions\n\n"
        "## Ejemplo workflow\n"
        "1. Webhook node (POST /agent-trigger)\n"
        "2. Function node (parse payload)\n"
        "3. HTTP Request node (call API)\n"
        "4. Respond to Webhook node\n\n"
        "## Mejores practicas\n"
        "- Usar production URL\n"
        "- Versionar workflows\n"
        "- Test con mock data\n"
        "- Error handling en workflow\n"
        "- Loggear ejecuciones\n\n"
        "## API endpoints\n"
        "- POST /webhook/<path>: trigger\n"
        "- POST /webhook-wait/<path>: async con response\n"
        "- GET /healthz: health check\n"
        "- GET /rest/workflows: listar workflows"
    )


def agent_patterns() -> str:
    return (
        "# Agent Orchestration Patterns\n\n"
        "## Sequential Pipeline\n"
        "- Agent A -> Agent B -> Agent C\n"
        "- Output de uno es input del siguiente\n"
        "- Usar agent_run_batch\n"
        "- Parar en primer error\n\n"
        "## Parallel Fan-out\n"
        "- Un trigger -> N agentes en paralelo\n"
        "- Recopilar resultados\n"
        "- Usar webhooks async\n"
        "- Aggregator al final\n\n"
        "## Router Pattern\n"
        "- Un agente decide que hacer\n"
        "- Delega a sub-agente especializado\n"
        "- LLM actua como router\n"
        "- Sub-agentes exponen tools\n\n"
        "## Map-Reduce\n"
        "- Dividir tarea en chunks\n"
        "- Cada agente procesa un chunk\n"
        "- Combinar resultados\n"
        "- Usar batch execution\n\n"
        "## Supervisor\n"
        "- Agente supervisor monitorea\n"
        "- Asigna tareas a workers\n"
        "- Recopila y valida resultados\n"
        "- Reintenta en caso de fallo\n\n"
        "## Event-driven\n"
        "- Webhook trigger inicia workflow\n"
        "- Agentes reaccionan a eventos\n"
        "- Async processing\n"
        "- Notificacion al completar\n\n"
        "## Retry Pattern\n"
        "- Reintentar en fallo\n"
        "- Backoff exponencial\n"
        "- Max retries configurable\n"
        "- Circuit breaker para proteger"
    )


def agent_security() -> str:
    return (
        "# Agent Runner Security\n\n"
        "## Sandboxing\n"
        "- Ejecutar scripts en contenedor aislado\n"
        "- Limitar CPU y memoria\n"
        "- Limitar acceso a filesystem\n"
        "- No ejecutar como root\n\n"
        "## Input validation\n"
        "- Validar script paths\n"
        "- No permitir path traversal\n"
        "- Sanitizar argumentos\n"
        "- Validar payload schema\n\n"
        "## Secrets\n"
        "- No hardcodear secrets\n"
        "- Usar variables de entorno\n"
        "- Usar secrets manager\n"
        "- No loggear secrets\n\n"
        "## Webhook security\n"
        "- HTTPS obligatorio en produccion\n"
        "- Bearer token auth\n"
        "- Rate limiting\n"
        "- IP whitelist\n"
        "- HMAC signature verification\n\n"
        "## Network\n"
        "- Limitar outbound connections\n"
        "- Firewall rules\n"
        "- VPN para agentes remotos\n"
        "- No exponer puertos innecesarios\n\n"
        "## Auditing\n"
        "- Loggear todas las ejecuciones\n"
        "- Track quien ejecuta que\n"
        "- Retention policy para logs\n"
        "- Alertas en actividad sospechosa"
    )


def agent_monitoring() -> str:
    return (
        "# Agent Monitoring\n\n"
        "## Metrics\n"
        "- job_count: total de jobs\n"
        "- job_duration: tiempo de ejecucion\n"
        "- job_success_rate: porcentaje de exito\n"
        "- job_timeout_count: timeouts\n"
        "- webhook_response_time: latencia\n\n"
        "## Health checks\n"
        "- agent_health_check: verifica n8n\n"
        "- Verificar espacio en disco\n"
        "- Verificar memoria disponible\n"
        "- Verificar procesos activos\n\n"
        "## Logging\n"
        "- Structured logging con JSON\n"
        "- Correlacion ID por job\n"
        "- Log level configurable\n"
        "- Centralized logging (ELK, Loki)\n\n"
        "## Alerting\n"
        "- Alertar en job failures\n"
        "- Alertar en timeouts\n"
        "- Alertar en webhook errors\n"
        "- Alertar en resource exhaustion\n\n"
        "## Dashboards\n"
        "- Jobs por estado (running, completed, failed)\n"
        "- Duracion promedio por agente\n"
        "- Throughput: jobs por minuto\n"
        "- Error rate por agente\n\n"
        "## Tracing\n"
        "- Distributed tracing (Jaeger, Zipkin)\n"
        "- Trace por job execution\n"
        "- Spans por sub-agent\n"
        "- Correlacion entre MCP y agentes"
    )


def agent_scripting() -> str:
    return (
        "# Agent Scripting Guide\n\n"
        "## Estructura de un script\n"
        "```python\n"
        "import sys\n"
        "import json\n"
        "\n"
        "def main():\n"
        "    args = sys.argv[1:]\n"
        "    result = process(args)\n"
        "    print(json.dumps(result))\n"
        "\n"
        "def process(args):\n"
        "    return {'status': 'ok', 'data': 'processed'}\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    main()\n"
        "```\n\n"
        "## Argumentos\n"
        "- sys.argv: lista de argumentos\n"
        "- argparse para CLI robusto\n"
        "- JSON stdin para datos complejos\n"
        "- Environment variables para config\n\n"
        "## Output\n"
        "- stdout: resultado principal\n"
        "- stderr: logs y errores\n"
        "- Exit code: 0 = success, !=0 = error\n"
        "- JSON output para parsing automatico\n\n"
        "## Error handling\n"
        "- try/except en main\n"
        "- Exit code significativo\n"
        "- Mensaje de error en stderr\n"
        "- No crash sin mensaje\n\n"
        "## Logging\n"
        "- structlog o logging module\n"
        "- JSON logs para parsing\n"
        "- Log level apropiado\n"
        "- Flush stdout/stderr\n\n"
        "## Testing\n"
        "- Unit tests con pytest\n"
        "- Mock subprocess para CI\n"
        "- Test con argumentos vacios\n"
        "- Test error cases"
    )


def agent_ci_cd() -> str:
    return (
        "# Agent CI/CD Integration\n\n"
        "## GitHub Actions\n"
        "```yaml\n"
        "- name: Run Agent\n"
        "  run: |\n"
        "    python scripts/agent.py --ci\n"
        "```\n\n"
        "## Trigger from CI\n"
        "- agent_trigger_webhook en pipeline\n"
        "- Payload con git info\n"
        "- Async processing post-merge\n\n"
        "## n8n CI integration\n"
        "- Webhook trigger en pipeline\n"
        "- n8n procesa notificaciones\n"
        "- Deploy automation\n"
        "- Test result processing\n\n"
        "## Mejores practicas\n"
        "- Versionar scripts de agentes\n"
        "- Test scripts en CI\n"
        "- Secrets en CI, no en codigo\n"
        "- Health check antes de deploy\n"
        "- Rollback en caso de fallo\n\n"
        "## Deployment\n"
        "- MCP server en contenedor\n"
        "- Scripts en volumen montado\n"
        "- n8n en contenedor separado\n"
        "- Network isolation\n\n"
        "## Monitoring en CI\n"
        "- Verificar job completion\n"
        "- Alertar en CI failures\n"
        "- Artifact: logs y resultados\n"
        "- Retry en flaky tests"
    )


def agent_architecture() -> str:
    return (
        "# Agent Runner Architecture\n\n"
        "## Componentes\n"
        "- MCP Server: expone tools via FastMCP\n"
        "- Tool functions: logica de ejecucion\n"
        "- n8n: workflow automation externo\n"
        "- Scripts: sub-agentes Python\n\n"
        "## Flujo de ejecucion\n"
        "1. LLM decide delegar tarea\n"
        "2. LLM llama MCP tool (agent_run_local_script)\n"
        "3. MCP server ejecuta script via subprocess\n"
        "4. Script retorna resultado en stdout\n"
        "5. MCP server retorna resultado al LLM\n"
        "6. LLM usa resultado para responder\n\n"
        "## Flujo webhook\n"
        "1. LLM llama agent_trigger_webhook\n"
        "2. MCP server hace HTTP POST a n8n\n"
        "3. n8n ejecuta workflow\n"
        "4. n8n retorna response\n"
        "5. MCP server retorna response al LLM\n\n"
        "## Escalabilidad\n"
        "- Horizontal: multiples MCP instances\n"
        "- Load balancer para webhooks\n"
        "- Queue para jobs async (Redis, RabbitMQ)\n"
        "- Workers para ejecucion paralela\n\n"
        "## Alta disponibilidad\n"
        "- MCP server en HA mode\n"
        "- n8n en cluster mode\n"
        "- Scripts en storage compartido\n"
        "- Health checks y auto-restart\n\n"
        "## Integracion con MCP ecosystem\n"
        "- mcp-orchestrator: coordina multiples MCPs\n"
        "- mcp-llm-router: enruta a LLMs\n"
        "- mcp-observability: monitoreo\n"
        "- mcp-ci-cd: pipeline automation"
    )


def agent_scaling() -> str:
    return (
        "# Agent Scaling Guide\n\n"
        "## Horizontal scaling\n"
        "- Multiples MCP server instances\n"
        "- Load balancer (nginx, HAProxy)\n"
        "- Stateless design para HA\n"
        "- Session affinity si es necesario\n\n"
        "## Queue-based scaling\n"
        "- Redis/RabbitMQ para job queue\n"
        "- Workers procesan jobs async\n"
        "- Backpressure handling\n"
        "- Dead letter queue para fallos\n\n"
        "## n8n scaling\n"
        "- n8n en mode queue (Redis)\n"
        "- Multiples n8n workers\n"
        "- Scaling horizontal en K8s\n"
        "- DB externa (PostgreSQL)\n\n"
        "## Resource limits\n"
        "- CPU: limitar por script\n"
        "- Memory: limitar por job\n"
        "- Disk: limitar workspace\n"
        "- Network: limitar bandwidth\n"
        "- Concurrent jobs: max configurable\n\n"
        "## Auto-scaling\n"
        "- Scale on CPU > 70%\n"
        "- Scale on queue depth > N\n"
        "- Scale on response time > Xms\n"
        "- K8s HPA o custom metrics\n\n"
        "## Performance\n"
        "- Connection pooling\n"
        "- Caching de resultados\n"
        "- Async I/O para webhooks\n"
        "- Batch processing para throughput\n"
        "- Profile scripts con cProfile"
    )
