"""Resources de solo lectura para mcp-llm-router."""

from __future__ import annotations

import json


def router_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-llm-router",
            "version": "1.0.0",
            "lmstudio_base_url": "http://localhost:1234/v1",
            "complexity_threshold": 6,
            "max_local_tokens": 6000,
            "privacy_mode": False,
            "history_max": 500,
        },
        indent=2,
        ensure_ascii=False,
    )


def router_local_models() -> str:
    return (
        "# Modelos locales (LM Studio)\n\n"
        "## Qwen3 8B (fast)\n"
        "- Rol: Tareas simples y rapidas\n"
        "- Umbral: complexity < 3, tokens < 2K\n\n"
        "## Devstral Small (code)\n"
        "- Rol: Generacion y analisis de codigo\n"
        "- Umbral: task_type == 'code'\n\n"
        "## Deepseek R1 0528 (reasoning)\n"
        "- Rol: Razonamiento multi-paso (chain-of-thought)\n"
        "- Umbral: task_type == 'reasoning'\n\n"
        "## Qwen2.5 14B 1M (large_context)\n"
        "- Rol: Contextos muy largos\n"
        "- Umbral: tokens > 8K"
    )


def router_cloud_models() -> str:
    return (
        "# Modelos de nube\n\n"
        "## Anthropic Claude\n"
        "- Modelo default: claude-sonnet-4-5\n"
        "- API: https://api.anthropic.com/v1/messages\n"
        "- Auth: x-api-key header\n\n"
        "## OpenAI\n"
        "- Modelo default: gpt-4o\n"
        "- API: https://api.openai.com/v1/chat/completions\n"
        "- Auth: Bearer token\n\n"
        "## Configuracion\n"
        "- ROUTER_CLOUD_PROVIDER: anthropic | openai\n"
        "- ROUTER_CLOUD_MODEL: nombre del modelo\n"
        "- ROUTER_CLOUD_API_KEY: API key"
    )


def router_routing_logic() -> str:
    return (
        "# Logica de ruteo\n\n"
        "## Flujo de decision\n"
        "1. Si force_local o privacy_mode -> local\n"
        "2. Si force_cloud -> cloud\n"
        "3. Si complexity >= threshold -> cloud\n"
        "4. Si estimated_tokens > max_local_tokens -> cloud\n"
        "5. Otherwise -> local\n\n"
        "## Seleccion de modelo local\n"
        "- task_type == 'code' -> Devstral Small\n"
        "- task_type == 'reasoning' -> Deepseek R1\n"
        "- task_type == 'large_context' -> Qwen2.5 14B\n"
        "- task_type == 'simple' -> Qwen3 8B\n\n"
        "## Scoring de complejidad (1-10)\n"
        "- Base: longitud del prompt (tokens)\n"
        "- Bonus: keywords de alta complejidad\n"
        "- Bonus: multiples instrucciones"
    )


def router_task_types() -> str:
    return json.dumps(
        {
            "task_types": {
                "simple": {"description": "Tareas rapidas", "model": "qwen3-8b"},
                "code": {"description": "Generacion de codigo", "model": "devstral-small-2507"},
                "reasoning": {"description": "Razonamiento multi-paso", "model": "deepseek-r1-0528"},
                "large_context": {"description": "Contextos largos >8K", "model": "qwen2.5-14b-instruct-1m"},
            }
        },
        indent=2,
        ensure_ascii=False,
    )


def router_best_practices() -> str:
    return (
        "# Mejores practicas de ruteo\n\n"
        "1. Usa privacy_mode para datos sensibles\n"
        "2. Ajusta complexity_threshold segun tu caso\n"
        "3. Monitoriza el historial para optimizar\n"
        "4. Usa force_local para tareas que no necesitan nube\n"
        "5. Verifica LM Studio con check_lmstudio_health\n"
        "6. Estima tokens antes de rutar\n"
        "7. Usa context para dar informacion adicional\n"
        "8. Configura timeouts adecuados\n"
        "9. Usa modelos especializados para cada tipo\n"
        "10. Revisa el historial para patrones de uso"
    )


def router_privacy_guide() -> str:
    return (
        "# Guia de privacidad\n\n"
        "## Modo privacidad (privacy_mode)\n"
        "Cuando esta activo, el router NUNCA envia datos a la nube.\n\n"
        "## Activar\n"
        "ROUTER_PRIVACY_MODE=true\n\n"
        "## Consideraciones\n"
        "- Las tareas complejas pueden tomar mas tiempo localmente\n"
        "- La calidad puede ser menor para tareas muy complejas\n"
        "- Los datos nunca salen de tu maquina\n"
        "- Ideal para PII, codigo propietario"
    )


def router_cost_optimization() -> str:
    return (
        "# Optimizacion de costos\n\n"
        "## Estrategias\n"
        "1. Bajar complexity_threshold para usar mas local\n"
        "2. Subir max_local_tokens para contextos largos locales\n"
        "3. Usar Qwen2.5 14B para contextos largos en lugar de nube\n"
        "4. Usar Devstral para codigo en lugar de nube\n"
        "5. Usar Deepseek R1 para razonamiento en lugar de nube\n\n"
        "## Ahorro estimado\n"
        "Rutear ~80% de tareas a local puede ahorrar 60-80% en costos de API."
    )


def router_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "Network error (LM Studio no disponible)"},
                {"code": -32002, "description": "Timeout error"},
                {"code": -32003, "description": "API error (proveedor de nube)"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def router_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## LM Studio no responde\n"
        "- Verifica que LM Studio este corriendo en localhost:1234\n"
        "- Usa check_lmstudio_health para diagnosticar\n"
        "- Revisa firewall y puertos\n\n"
        "## Cloud API falla\n"
        "- Verifica ROUTER_CLOUD_API_KEY en .env\n"
        "- Revisa cuota del proveedor\n"
        "- Verifica nombre del modelo (ROUTER_CLOUD_MODEL)\n\n"
        "## Ruteo incorrecto\n"
        "- Ajusta complexity_threshold\n"
        "- Revisa estimated_tokens vs max_local_tokens\n"
        "- Usa estimate_task_complexity para diagnosticar\n\n"
        "## Historial vacio\n"
        "- Verifica permisos de escritura en .ai-memory/\n"
        "- El historial se crea tras llamar route_task"
    )


def router_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- route_task(prompt, context, force_local, force_cloud)\n"
        "- estimate_task_complexity(prompt, context)\n"
        "- get_routing_config()\n"
        "- get_routing_history(limit)\n"
        "- check_lmstudio_health(timeout)\n"
        "- list_local_models()\n"
        "- call_local_model(prompt, model, system, temperature, max_tokens)\n"
        "- call_cloud_model(prompt, system, temperature, max_tokens)\n\n"
        "## Variables .env\n"
        "- ROUTER_LMSTUDIO_BASE_URL\n"
        "- ROUTER_COMPLEXITY_THRESHOLD\n"
        "- ROUTER_MAX_LOCAL_TOKENS\n"
        "- ROUTER_PRIVACY_MODE\n"
        "- ROUTER_MODEL_FAST / CODE / REASON / LARGE\n"
        "- ROUTER_CLOUD_PROVIDER / MODEL / API_KEY"
    )


def router_performance_tips() -> str:
    return (
        "# Tips de rendimiento\n\n"
        "## Latencia\n"
        "- Qwen3 8B: ~0.5-2s para respuestas cortas\n"
        "- Devstral: ~1-3s para codigo\n"
        "- Deepseek R1: ~3-10s (CoT)\n"
        "- Qwen2.5 14B: ~2-5s\n"
        "- Cloud: ~1-5s + latencia de red\n\n"
        "## Optimizacion\n"
        "- Usa temperature=0 para respuestas deterministicas\n"
        "- Ajusta max_tokens al minimo necesario\n"
        "- Usa system prompts para guiar al modelo\n"
        "- Batch prompts similares para reducir llamadas"
    )


def router_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Ejemplo 1: Rutar una tarea simple\n"
        "route_task(prompt='Formatea este JSON')\n"
        "-> destination: local, model: qwen3-8b\n\n"
        "## Ejemplo 2: Rutar codigo\n"
        "route_task(prompt='Implementa una funcion Python para leer CSV')\n"
        "-> destination: local, model: devstral-small-2507\n\n"
        "## Ejemplo 3: Forzar nube\n"
        "route_task(prompt='Analiza esto', force_cloud=True)\n"
        "-> destination: cloud, model: claude-sonnet-4-5\n\n"
        "## Ejemplo 4: Estimar complejidad\n"
        "estimate_task_complexity(prompt='Diseña una arquitectura de microservicios')\n"
        "-> complexity_score: 7, task_type: reasoning"
    )


def router_model_comparison() -> str:
    return (
        "# Comparacion de modelos\n\n"
        "| Modelo | Tipo | Contexto | Fortaleza | Debilidad |\n"
        "|--------|------|----------|-----------|-----------|\n"
        "| Qwen3 8B | Local | 32K | Rapido | Limitado |\n"
        "| Devstral | Local | 128K | Codigo | No razonamiento |\n"
        "| Deepseek R1 | Local | 64K | CoT | Lento |\n"
        "| Qwen2.5 14B | Local | 1M | Contexto | Pesado |\n"
        "| Claude Sonnet | Cloud | 200K | General | Costoso |\n"
        "| GPT-4o | Cloud | 128K | General | Costoso |"
    )


def router_api_reference() -> str:
    return (
        "# Referencia de API\n\n"
        "## LM Studio (OpenAI-compatible)\n"
        "GET /v1/models — listar modelos\n"
        "POST /v1/chat/completions — chat completion\n\n"
        "## Anthropic\n"
        "POST /v1/messages — message completion\n"
        "Headers: x-api-key, anthropic-version: 2023-06-01\n\n"
        "## OpenAI\n"
        "POST /v1/chat/completions — chat completion\n"
        "Headers: Authorization: Bearer <key>"
    )
