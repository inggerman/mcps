"""
Servidor FastMCP para mcp-llm-router.

Expone 9 herramientas para decidir inteligentemente si una tarea
debe procesarse con un modelo local (LM Studio) o en la nube.

Modelos locales configurados:
  - Qwen3 8B         → tareas simples/rápidas
  - Devstral Small   → código y programación
  - Deepseek R1 0528 → razonamiento y análisis
  - Qwen2.5 14B 1M   → contextos muy largos

Transporte: stdio (Claude Desktop) o streamable-http (Docker).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_llm_router import __version__
from mcp_llm_router.config import settings
from mcp_llm_router.tools.router_tools import (
    batch_route_tasks,
    call_cloud_model,
    call_local_model,
    check_lmstudio_health,
    clear_routing_history,
    compare_models,
    estimate_cost,
    estimate_task_complexity,
    export_routing_history,
    get_model_info,
    get_routing_config,
    get_routing_history,
    get_routing_history_filtered,
    get_routing_stats,
    get_routing_summary,
    list_local_models,
    record_routing_decision,
    route_task,
    set_privacy_mode,
    set_routing_threshold,
    validate_routing_config,
)
from mcp_llm_router import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-llm-router",
)

logger = get_logger(__name__)

# Ruta del historial de ruteo
_HISTORY_PATH: Path = Path(".ai-memory/routing_history.json")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Ciclo de vida: verifica disponibilidad de LM Studio al inicio."""
    structlog.contextvars.bind_contextvars(server_name="mcp-llm-router")
    _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        "mcp-llm-router iniciando",
        version=__version__,
        lmstudio_url=settings.lmstudio_base_url,
        complexity_threshold=settings.complexity_threshold,
        privacy_mode=settings.privacy_mode,
        model_fast=settings.model_fast,
        model_code=settings.model_code,
        model_reason=settings.model_reason,
        model_large_context=settings.model_large_context,
    )
    yield
    logger.info("mcp-llm-router detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-llm-router",
    instructions=(
        "Servidor MCP para ruteo inteligente de tareas entre modelos locales (LM Studio) y la nube. "
        "Llama route_task con el prompt para obtener la recomendación de modelo. "
        "Modelos locales disponibles: Qwen3 8B (rápido), Devstral Small (código), "
        "Deepseek R1 (razonamiento), Qwen2.5 14B 1M (contexto largo). "
        "Nube: Claude Sonnet (tareas complejas). "
        "Usa check_lmstudio_health para verificar que LM Studio esté corriendo."
    ),
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Wrapper estándar de manejo de errores."""
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__, error=str(exc))
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


# ---------------------------------------------------------------------------
# Tools de decisión
# ---------------------------------------------------------------------------


@mcp.tool(
    name="route_task",
    description=(
        "Analiza un prompt y decide qué modelo usar: local (LM Studio) o nube. "
        "Retorna destination, model recomendado, task_type, complexity_score (1-10), "
        "estimated_tokens y razonamiento de la decisión. "
        "Parámetros: prompt (obligatorio), context (contexto adicional), "
        "force_local (bool), force_cloud (bool)."
    ),
)
def tool_route_task(
    prompt: str,
    context: str = "",
    force_local: bool = False,
    force_cloud: bool = False,
) -> dict[str, Any]:
    logger.info(
        "route_task llamado",
        prompt_length=len(prompt),
        force_local=force_local,
        force_cloud=force_cloud,
    )
    decision = _handle(
        route_task,
        prompt,
        context,
        force_local,
        force_cloud,
        settings.complexity_threshold,
        settings.max_local_tokens,
        settings.privacy_mode,
        settings.model_fast,
        settings.model_code,
        settings.model_reason,
        settings.model_large_context,
        settings.cloud_model,
        settings.cloud_provider,
    )
    # Registrar en historial (non-blocking, ignorar errores de IO)
    try:
        record_routing_decision(_HISTORY_PATH, prompt, decision, settings.history_max)
    except Exception:
        pass
    return decision


@mcp.tool(
    name="estimate_task_complexity",
    description=(
        "Evalúa la complejidad de un prompt (score 1-10) sin tomar decisión de ruteo. "
        "Retorna complexity_score, task_type, estimated_tokens, complexity_label y factores. "
        "Parámetros: prompt, context (opcional)."
    ),
)
def tool_estimate_task_complexity(prompt: str, context: str = "") -> dict[str, Any]:
    logger.info("estimate_task_complexity llamado", prompt_length=len(prompt))
    return _handle(estimate_task_complexity, prompt, context)


@mcp.tool(
    name="get_routing_config",
    description=(
        "Retorna la configuración actual del router: modelos locales asignados por rol, "
        "modelo de nube, umbrales de complejidad y tokens, modo privacidad."
    ),
)
def tool_get_routing_config() -> dict[str, Any]:
    logger.info("get_routing_config llamado")
    return _handle(
        get_routing_config,
        settings.complexity_threshold,
        settings.max_local_tokens,
        settings.privacy_mode,
        settings.model_fast,
        settings.model_code,
        settings.model_reason,
        settings.model_large_context,
        settings.cloud_model,
        settings.cloud_provider,
        settings.lmstudio_base_url,
    )


@mcp.tool(
    name="get_routing_history",
    description=(
        "Retorna el historial de decisiones de ruteo tomadas por el servidor. "
        "Muestra destination, model, task_type y complexity_score por decisión. "
        "Parámetro limit: máximo de entradas (default 50)."
    ),
)
def tool_get_routing_history(limit: int = 50) -> list[dict[str, Any]]:
    logger.info("get_routing_history llamado", limit=limit)
    return _handle(get_routing_history, _HISTORY_PATH, limit)


# ---------------------------------------------------------------------------
# Tools de LM Studio
# ---------------------------------------------------------------------------


@mcp.tool(
    name="check_lmstudio_health",
    description=(
        "Verifica si LM Studio está corriendo y lista los modelos disponibles. "
        "Retorna status, available_models y model_count. "
        "Parámetro timeout: segundos de espera (default 5)."
    ),
)
def tool_check_lmstudio_health(timeout: int = 5) -> dict[str, Any]:
    logger.info("check_lmstudio_health llamado")
    return _handle(check_lmstudio_health, settings.lmstudio_base_url, timeout)


@mcp.tool(
    name="list_local_models",
    description=(
        "Lista todos los modelos disponibles en LM Studio con sus metadatos completos "
        "(id, object, etc.). Útil para verificar qué modelos están cargados."
    ),
)
def tool_list_local_models() -> list[dict[str, Any]]:
    logger.info("list_local_models llamado")
    return _handle(list_local_models, settings.lmstudio_base_url, settings.lmstudio_timeout_seconds)


# ---------------------------------------------------------------------------
# Tools de inferencia directa
# ---------------------------------------------------------------------------


@mcp.tool(
    name="call_local_model",
    description=(
        "Ejecuta un prompt directamente en un modelo local de LM Studio. "
        "Retorna response_text, tokens_used y elapsed_seconds. "
        "Parámetros: prompt, model (nombre en LM Studio), system (prompt de sistema), "
        "temperature (0-2, default 0.7), max_tokens (default 2048)."
    ),
)
def tool_call_local_model(
    prompt: str,
    model: str = "",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    # Si no se especifica modelo, usar el rápido por defecto
    target_model = model or settings.model_fast
    logger.info("call_local_model llamado", model=target_model, prompt_length=len(prompt))
    return _handle(
        call_local_model,
        prompt,
        target_model,
        settings.lmstudio_base_url,
        system,
        temperature,
        max_tokens,
        settings.lmstudio_timeout_seconds,
    )


@mcp.tool(
    name="call_cloud_model",
    description=(
        "Ejecuta un prompt en el modelo de nube configurado (Anthropic o OpenAI). "
        "Requiere ROUTER_CLOUD_API_KEY configurado en el .env. "
        "Retorna response_text, tokens_used y elapsed_seconds. "
        "Parámetros: prompt, system (prompt de sistema), "
        "temperature (default 0.7), max_tokens (default 4096)."
    ),
)
def tool_call_cloud_model(
    prompt: str,
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    logger.info(
        "call_cloud_model llamado",
        provider=settings.cloud_provider,
        model=settings.cloud_model,
        prompt_length=len(prompt),
    )
    return _handle(
        call_cloud_model,
        prompt,
        settings.cloud_model,
        settings.cloud_provider,
        settings.cloud_api_key,
        system,
        temperature,
        max_tokens,
        settings.cloud_timeout_seconds,
    )


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="clear_routing_history",
    description="Borra todo el historial de ruteo. Sin parametros.",
)
def tool_clear_routing_history() -> dict[str, Any]:
    logger.info("clear_routing_history llamado")
    return _handle(clear_routing_history, _HISTORY_PATH)


@mcp.tool(
    name="get_routing_stats",
    description="Retorna estadisticas agregadas del historial: total, local/cloud count, avg complexity, distribucion.",
)
def tool_get_routing_stats() -> dict[str, Any]:
    logger.info("get_routing_stats llamado")
    return _handle(get_routing_stats, _HISTORY_PATH)


@mcp.tool(
    name="compare_models",
    description="Ejecuta un prompt en local y nube y compara resultados. Parametros: prompt, local_model, system, temperature, max_tokens.",
)
def tool_compare_models(
    prompt: str,
    local_model: str = "",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    target = local_model or settings.model_fast
    logger.info("compare_models llamado", model=target)
    return _handle(
        compare_models,
        prompt,
        target,
        settings.lmstudio_base_url,
        settings.cloud_model,
        settings.cloud_provider,
        settings.cloud_api_key,
        system,
        temperature,
        max_tokens,
        settings.lmstudio_timeout_seconds,
        settings.cloud_timeout_seconds,
    )


@mcp.tool(
    name="set_routing_threshold",
    description="Valida y retorna un nuevo umbral de complejidad (1-10). Parametros: new_threshold.",
)
def tool_set_routing_threshold(new_threshold: int) -> dict[str, Any]:
    logger.info("set_routing_threshold llamado", new_threshold=new_threshold)
    return _handle(set_routing_threshold, new_threshold, settings.complexity_threshold)


@mcp.tool(
    name="set_privacy_mode",
    description="Activa o desactiva el modo privacidad. Parametros: enabled (bool).",
)
def tool_set_privacy_mode(enabled: bool) -> dict[str, Any]:
    logger.info("set_privacy_mode llamado", enabled=enabled)
    return _handle(set_privacy_mode, enabled)


@mcp.tool(
    name="get_model_info",
    description="Obtiene info de un modelo en LM Studio. Parametros: model_name (requerido), timeout (default 5).",
)
def tool_get_model_info(model_name: str, timeout: int = 5) -> dict[str, Any]:
    logger.info("get_model_info llamado", model=model_name)
    return _handle(get_model_info, model_name, settings.lmstudio_base_url, timeout)


@mcp.tool(
    name="batch_route_tasks",
    description="Ruta multiples prompts en lote. Parametros: prompts (list de strings). Retorna lista de decisiones.",
)
def tool_batch_route_tasks(prompts: list[str]) -> list[dict[str, Any]]:
    logger.info("batch_route_tasks llamado", count=len(prompts))
    return _handle(
        batch_route_tasks,
        prompts,
        settings.complexity_threshold,
        settings.max_local_tokens,
        settings.privacy_mode,
        settings.model_fast,
        settings.model_code,
        settings.model_reason,
        settings.model_large_context,
        settings.cloud_model,
        settings.cloud_provider,
    )


@mcp.tool(
    name="get_routing_history_filtered",
    description="Historial filtrado por destination o task_type. Parametros: destination, task_type, limit.",
)
def tool_get_routing_history_filtered(
    destination: str | None = None,
    task_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    logger.info("get_routing_history_filtered llamado")
    return _handle(get_routing_history_filtered, _HISTORY_PATH, destination, task_type, limit)


@mcp.tool(
    name="estimate_cost",
    description="Estima costo de procesar un prompt en local vs nube. Parametros: prompt, destination.",
)
def tool_estimate_cost(prompt: str, destination: str = "local") -> dict[str, Any]:
    logger.info("estimate_cost llamado", prompt_length=len(prompt))
    return _handle(
        estimate_cost,
        prompt,
        destination,
        settings.cloud_provider,
        settings.cloud_model,
    )


@mcp.tool(
    name="export_routing_history",
    description="Exporta el historial en JSON o CSV. Parametros: format ('json' o 'csv', default 'json').",
)
def tool_export_routing_history(format: str = "json") -> str:
    logger.info("export_routing_history llamado", format=format)
    return _handle(export_routing_history, _HISTORY_PATH, format)


@mcp.tool(
    name="validate_routing_config",
    description="Valida la configuracion del router y retorna errores/warnings.",
)
def tool_validate_routing_config() -> dict[str, Any]:
    logger.info("validate_routing_config llamado")
    return _handle(
        validate_routing_config,
        settings.complexity_threshold,
        settings.max_local_tokens,
        settings.model_fast,
        settings.model_code,
        settings.model_reason,
        settings.model_large_context,
        settings.cloud_model,
        settings.cloud_provider,
    )


@mcp.tool(
    name="get_routing_summary",
    description="Retorna un resumen rapido del historial: total, ultimo destino, ultimo modelo.",
)
def tool_get_routing_summary() -> dict[str, Any]:
    logger.info("get_routing_summary llamado")
    return _handle(get_routing_summary, _HISTORY_PATH)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("router://configuration")
def res_config() -> str:
    return res.router_configuration()


@mcp.resource("router://local-models")
def res_local() -> str:
    return res.router_local_models()


@mcp.resource("router://cloud-models")
def res_cloud() -> str:
    return res.router_cloud_models()


@mcp.resource("router://routing-logic")
def res_logic() -> str:
    return res.router_routing_logic()


@mcp.resource("router://task-types")
def res_tasks() -> str:
    return res.router_task_types()


@mcp.resource("router://best-practices")
def res_best() -> str:
    return res.router_best_practices()


@mcp.resource("router://privacy-guide")
def res_priv() -> str:
    return res.router_privacy_guide()


@mcp.resource("router://cost-optimization")
def res_cost() -> str:
    return res.router_cost_optimization()


@mcp.resource("router://error-codes")
def res_errors() -> str:
    return res.router_error_codes()


@mcp.resource("router://troubleshooting")
def res_trouble() -> str:
    return res.router_troubleshooting()


@mcp.resource("router://quick-reference")
def res_quick() -> str:
    return res.router_quick_reference()


@mcp.resource("router://performance-tips")
def res_perf() -> str:
    return res.router_performance_tips()


@mcp.resource("router://examples")
def res_examples() -> str:
    return res.router_examples()


@mcp.resource("router://model-comparison")
def res_compare() -> str:
    return res.router_model_comparison()


@mcp.resource("router://api-reference")
def res_api() -> str:
    return res.router_api_reference()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
