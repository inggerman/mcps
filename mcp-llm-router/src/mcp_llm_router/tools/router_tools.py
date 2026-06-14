"""
Lógica de negocio de mcp-llm-router.

Implementa la selección inteligente entre modelos locales (LM Studio)
y modelos en la nube. Sin dependencias de MCP ni FastMCP.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from mcp_shared.errors import ApiError, NetworkError, NetworkTimeoutError, ValidationError

# ---------------------------------------------------------------------------
# Constantes de clasificación de tareas
# ---------------------------------------------------------------------------

# Palabras clave que elevan la complejidad (-> nube)
_HIGH_COMPLEXITY_KEYWORDS = frozenset(
    [
        "arquitectura",
        "architecture",
        "diseño de sistema",
        "system design",
        "decisión estratégica",
        "trade-off",
        "microservicios",
        "microservices",
        "refactoring completo",
        "full refactor",
        "plan de migración",
        "migration plan",
        "análisis de seguridad",
        "security analysis",
        "código de autenticación",
        "múltiples servicios",
        "multiple services",
    ]
)

# Palabras clave de tareas de código (-> devstral)
_CODE_KEYWORDS = frozenset(
    [
        "código",
        "code",
        "función",
        "function",
        "clase",
        "class",
        "método",
        "method",
        "implementa",
        "implement",
        "genera",
        "generate",
        "escribe",
        "write",
        "test",
        "prueba",
        "bug",
        "error",
        "fix",
        "corrige",
        "refactor",
        "debugging",
        "depura",
        "parser",
        "api",
        "endpoint",
        "query",
        "sql",
    ]
)

# Palabras clave de razonamiento (-> deepseek-r1)
_REASONING_KEYWORDS = frozenset(
    [
        "por qué",
        "why",
        "analiza",
        "analyze",
        "evalúa",
        "evaluate",
        "compara",
        "compare",
        "explica",
        "explain",
        "razona",
        "reason",
        "pros y contras",
        "trade-offs",
        "mejor opción",
        "best option",
        "diagrama",
        "diagram",
        "flujo",
        "flow",
        "patrón",
        "pattern",
    ]
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _estimate_tokens(text: str) -> int:
    """Estimación rápida de tokens (~4 chars por token, conservadora)."""
    return max(1, len(text) // 3)


def _score_complexity(prompt: str) -> int:
    """
    Calcula un score de complejidad del prompt entre 1 y 10.

    Criterios:
    - Longitud (tokens)
    - Presencia de keywords de alta complejidad
    - Número de instrucciones distintas (conteo de verbos de acción)
    - Menciones a múltiples sistemas/servicios
    """
    lower = prompt.lower()
    token_count = _estimate_tokens(prompt)

    # Score base por longitud
    if token_count < 100:
        score = 1
    elif token_count < 500:
        score = 2
    elif token_count < 1500:
        score = 3
    elif token_count < 3000:
        score = 4
    elif token_count < 6000:
        score = 5
    elif token_count < 12000:
        score = 6
    elif token_count < 25000:
        score = 7
    elif token_count < 50000:
        score = 8
    else:
        score = 9

    # Bonus por keywords de alta complejidad
    high_kw_matches = sum(1 for kw in _HIGH_COMPLEXITY_KEYWORDS if kw in lower)
    score = min(10, score + min(3, high_kw_matches))

    # Bonus por múltiples instrucciones (conteo de puntos/comandos)
    instruction_count = prompt.count(".") + prompt.count(";") + prompt.count("\n")
    if instruction_count > 15:
        score = min(10, score + 1)
    if instruction_count > 40:
        score = min(10, score + 1)

    return max(1, min(10, score))


def _detect_task_type(prompt: str) -> str:
    """
    Detecta el tipo de tarea del prompt para seleccionar el mejor modelo local.

    Retorna: 'code', 'reasoning', 'large_context', 'simple'
    """
    lower = prompt.lower()
    token_count = _estimate_tokens(prompt)

    # Contexto muy largo -> modelo de ventana grande
    if token_count > 8000:
        return "large_context"

    # Conteo de keywords
    code_score = sum(1 for kw in _CODE_KEYWORDS if kw in lower)
    reasoning_score = sum(1 for kw in _REASONING_KEYWORDS if kw in lower)

    if code_score > reasoning_score and code_score >= 2:
        return "code"
    if reasoning_score >= 2:
        return "reasoning"
    return "simple"


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def route_task(
    prompt: str,
    context: str = "",
    force_local: bool = False,
    force_cloud: bool = False,
    complexity_threshold: int = 6,
    max_local_tokens: int = 6000,
    privacy_mode: bool = False,
    model_fast: str = "qwen3-8b",
    model_code: str = "devstral-small-2507",
    model_reason: str = "deepseek-r1-0528-qwen3-8b",
    model_large_context: str = "qwen2.5-14b-instruct-1m",
    cloud_model: str = "claude-sonnet-4-5",
    cloud_provider: str = "anthropic",
) -> dict[str, Any]:
    """
    Analiza un prompt y decide qué modelo usar.

    Retorna una decisión estructurada con:
    - destination: 'local' o 'cloud'
    - model: nombre exacto del modelo recomendado
    - task_type: tipo de tarea detectado
    - complexity_score: score 1-10
    - estimated_tokens: tokens estimados del prompt
    - reasoning: explicación de la decisión
    - local_model_role: rol del modelo local seleccionado
    """
    if not prompt or len(prompt.strip()) < 3:
        raise ValidationError(field="prompt", message="El prompt debe tener al menos 3 caracteres.")
    if force_local and force_cloud:
        raise ValidationError(
            field="force_local/force_cloud",
            message="No puedes forzar local y nube al mismo tiempo.",
        )

    full_text = prompt + " " + context
    complexity = _score_complexity(full_text)
    task_type = _detect_task_type(full_text)
    estimated_tokens = _estimate_tokens(full_text)

    # Lógica de decisión
    reasons: list[str] = []
    destination = "local"
    model = model_fast
    local_model_role: str | None = "fast"

    # Forzado por el usuario
    if force_local or privacy_mode:
        destination = "local"
        if privacy_mode:
            reasons.append("Modo privacidad activo: nunca se envía a la nube.")
        if force_local:
            reasons.append("Forzado a modelo local por el usuario.")
    elif force_cloud:
        destination = "cloud"
        model = cloud_model
        reasons.append("Forzado a modelo en la nube por el usuario.")
        return {
            "destination": destination,
            "model": model,
            "provider": cloud_provider,
            "task_type": task_type,
            "complexity_score": complexity,
            "estimated_tokens": estimated_tokens,
            "reasoning": reasons,
            "local_model_role": None,
        }
    else:
        # Decisión automática
        if complexity >= complexity_threshold:
            destination = "cloud"
            model = cloud_model
            reasons.append(
                f"Complejidad {complexity}/10 supera el umbral configurado ({complexity_threshold}). "
                "Se requiere el modelo de nube para mayor capacidad de razonamiento."
            )
        elif estimated_tokens > max_local_tokens:
            destination = "cloud"
            model = cloud_model
            reasons.append(
                f"El prompt excede {max_local_tokens} tokens estimados ({estimated_tokens}). "
                "Se usa la nube para manejar el contexto largo sin pérdida de calidad."
            )
        else:
            destination = "local"
            reasons.append(
                f"Complejidad {complexity}/10 dentro del umbral ({complexity_threshold}) "
                f"y {estimated_tokens} tokens dentro del límite local ({max_local_tokens})."
            )

    # Si es local, elegir el modelo específico más adecuado
    if destination == "local":
        if task_type == "code":
            model = model_code
            local_model_role = "code"
            reasons.append(
                "Tarea de tipo código detectada → Devstral Small es el mejor modelo local "
                "para generación/análisis de código."
            )
        elif task_type == "reasoning":
            model = model_reason
            local_model_role = "reasoning"
            reasons.append(
                "Tarea de razonamiento multi-paso detectada → Deepseek R1 con "
                "chain-of-thought nativo."
            )
        elif task_type == "large_context":
            model = model_large_context
            local_model_role = "large_context"
            reasons.append(
                f"Contexto amplio ({estimated_tokens} tokens) → Qwen2.5 14B con "
                f"ventana de 1M tokens."
            )
        else:
            model = model_fast
            local_model_role = "fast"
            reasons.append("Tarea simple/clasificación → Qwen3 8B: rápido y eficiente.")
    else:
        local_model_role = None

    return {
        "destination": destination,
        "model": model,
        "provider": cloud_provider if destination == "cloud" else "lmstudio",
        "task_type": task_type,
        "complexity_score": complexity,
        "estimated_tokens": estimated_tokens,
        "reasoning": reasons,
        "local_model_role": local_model_role,
    }


def estimate_task_complexity(prompt: str, context: str = "") -> dict[str, Any]:
    """
    Evalúa la complejidad de un prompt sin tomar decisión de ruteo.

    Retorna:
        Dict con score 1-10, task_type, estimated_tokens y factores determinantes.
    """
    if not prompt or len(prompt.strip()) < 3:
        raise ValidationError(field="prompt", message="El prompt debe tener al menos 3 caracteres.")

    full_text = prompt + " " + context
    score = _score_complexity(full_text)
    task_type = _detect_task_type(full_text)
    tokens = _estimate_tokens(full_text)

    lower = full_text.lower()
    matched_high_kw = [kw for kw in _HIGH_COMPLEXITY_KEYWORDS if kw in lower]
    matched_code_kw = [kw for kw in _CODE_KEYWORDS if kw in lower][:5]

    return {
        "complexity_score": score,
        "task_type": task_type,
        "estimated_tokens": tokens,
        "complexity_label": (
            "simple"
            if score <= 3
            else "moderate"
            if score <= 5
            else "complex"
            if score <= 7
            else "very_complex"
        ),
        "factors": {
            "token_count": tokens,
            "high_complexity_keywords_matched": matched_high_kw,
            "code_keywords_matched": matched_code_kw,
        },
    }


# ---------------------------------------------------------------------------
# LM Studio health & modelos
# ---------------------------------------------------------------------------


def check_lmstudio_health(base_url: str, timeout: int = 5) -> dict[str, Any]:
    """
    Verifica si LM Studio está corriendo y lista los modelos disponibles.

    Args:
        base_url: URL base de la API de LM Studio.
        timeout: Timeout en segundos para la conexión.

    Retorna:
        Dict con status, modelos disponibles y modelo actualmente cargado.
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(f"{base_url}/models")
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(
            url=base_url,
            timeout_seconds=timeout,
        ) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=base_url, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise ApiError(service="lmstudio", detail=str(exc)) from exc

    models = [m.get("id", "") for m in data.get("data", [])]
    return {
        "status": "online",
        "base_url": base_url,
        "available_models": models,
        "model_count": len(models),
    }


def list_local_models(base_url: str, timeout: int = 5) -> list[dict[str, Any]]:
    """
    Lista todos los modelos disponibles en LM Studio con sus metadatos.

    Args:
        base_url: URL base de la API de LM Studio.
        timeout: Timeout en segundos.

    Retorna:
        Lista de modelos con id, object y otros metadatos disponibles.
    """
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(f"{base_url}/models")
            resp.raise_for_status()
            return resp.json().get("data", [])
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(url=base_url, timeout_seconds=timeout) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=base_url, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise ApiError(service="lmstudio", detail=str(exc)) from exc


def get_routing_config(
    complexity_threshold: int,
    max_local_tokens: int,
    privacy_mode: bool,
    model_fast: str,
    model_code: str,
    model_reason: str,
    model_large_context: str,
    cloud_model: str,
    cloud_provider: str,
    lmstudio_base_url: str,
) -> dict[str, Any]:
    """
    Retorna la configuración actual de ruteo del servidor.

    Retorna:
        Dict con todos los parámetros de configuración activos.
    """
    return {
        "rules": {
            "complexity_threshold": complexity_threshold,
            "max_local_tokens": max_local_tokens,
            "privacy_mode": privacy_mode,
        },
        "local_models": {
            "fast": {"name": model_fast, "role": "Tareas simples < complexity 3, < 2K tokens"},
            "code": {"name": model_code, "role": "Generación y análisis de código"},
            "reasoning": {"name": model_reason, "role": "Razonamiento multi-paso (R1 CoT)"},
            "large_context": {
                "name": model_large_context,
                "role": "Contextos > 8K tokens (1M window)",
            },
        },
        "cloud": {
            "provider": cloud_provider,
            "model": cloud_model,
            "role": "Tareas complejas o que superan límites locales",
        },
        "lmstudio_url": lmstudio_base_url,
    }


# ---------------------------------------------------------------------------
# Llamadas a modelos
# ---------------------------------------------------------------------------


def call_local_model(
    prompt: str,
    model: str,
    base_url: str,
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 120,
) -> dict[str, Any]:
    """
    Ejecuta un prompt en un modelo local de LM Studio.

    Args:
        prompt: Prompt del usuario.
        model: Nombre del modelo en LM Studio.
        base_url: URL base de LM Studio.
        system: System prompt opcional.
        temperature: Temperatura de generación (0-2).
        max_tokens: Máximo de tokens a generar.
        timeout: Timeout en segundos.

    Retorna:
        Dict con response_text, model, tokens_used y tiempo de respuesta.
    """
    if not prompt or len(prompt.strip()) < 3:
        raise ValidationError(field="prompt", message="El prompt debe tener al menos 3 caracteres.")
    if not model:
        raise ValidationError(field="model", message="Debes especificar un modelo.")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    start_time = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(f"{base_url}/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException as exc:
        raise NetworkTimeoutError(url=base_url, timeout_seconds=timeout) from exc
    except httpx.RequestError as exc:
        raise NetworkError(url=base_url, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise ApiError(
            service="lmstudio", detail=f"{exc.response.status_code}: {exc.response.text}"
        ) from exc

    elapsed = round(time.time() - start_time, 2)
    choice = data.get("choices", [{}])[0]
    response_text = choice.get("message", {}).get("content", "")
    usage = data.get("usage", {})

    return {
        "response_text": response_text,
        "model": model,
        "provider": "lmstudio",
        "tokens_prompt": usage.get("prompt_tokens", 0),
        "tokens_completion": usage.get("completion_tokens", 0),
        "tokens_total": usage.get("total_tokens", 0),
        "elapsed_seconds": elapsed,
        "finish_reason": choice.get("finish_reason", "unknown"),
    }


def call_cloud_model(
    prompt: str,
    model: str,
    provider: str,
    api_key: str,
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    timeout: int = 60,
) -> dict[str, Any]:
    """
    Ejecuta un prompt en un modelo de nube (Anthropic o OpenAI-compatible).

    Args:
        prompt: Prompt del usuario.
        model: Nombre del modelo (ej: 'claude-sonnet-4-5').
        provider: Proveedor ('anthropic' o 'openai').
        api_key: API key del proveedor.
        system: System prompt opcional.
        temperature: Temperatura (0-2).
        max_tokens: Máximo de tokens a generar.
        timeout: Timeout en segundos.

    Retorna:
        Dict con response_text, model, tokens_used y tiempo de respuesta.
    """
    if not prompt or len(prompt.strip()) < 3:
        raise ValidationError(field="prompt", message="El prompt debe tener al menos 3 caracteres.")
    if not api_key:
        raise ValidationError(
            field="api_key",
            message="Se requiere una API key para llamar al modelo de nube. "
            "Configura ROUTER_CLOUD_API_KEY en el .env.",
        )
    if provider not in ("anthropic", "openai"):
        raise ValidationError(
            field="provider", message="Proveedores válidos: 'anthropic', 'openai'."
        )

    start_time = time.time()

    if provider == "anthropic":
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(
                    "https://api.anthropic.com/v1/messages", headers=headers, json=payload
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise NetworkTimeoutError(
                url="https://api.anthropic.com", timeout_seconds=timeout
            ) from exc
        except httpx.RequestError as exc:
            raise NetworkError(url="https://api.anthropic.com", detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            raise ApiError(
                service="anthropic", detail=f"{exc.response.status_code}: {exc.response.text}"
            ) from exc

        elapsed = round(time.time() - start_time, 2)
        content = data.get("content", [{}])[0].get("text", "")
        usage = data.get("usage", {})
        return {
            "response_text": content,
            "model": model,
            "provider": "anthropic",
            "tokens_prompt": usage.get("input_tokens", 0),
            "tokens_completion": usage.get("output_tokens", 0),
            "tokens_total": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            "elapsed_seconds": elapsed,
            "finish_reason": data.get("stop_reason", "unknown"),
        }

    else:  # openai-compatible
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(
                    "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise NetworkTimeoutError(
                url="https://api.openai.com", timeout_seconds=timeout
            ) from exc
        except httpx.RequestError as exc:
            raise NetworkError(url="https://api.openai.com", detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            raise ApiError(
                service="openai", detail=f"{exc.response.status_code}: {exc.response.text}"
            ) from exc

        elapsed = round(time.time() - start_time, 2)
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})
        return {
            "response_text": content,
            "model": model,
            "provider": "openai",
            "tokens_prompt": usage.get("prompt_tokens", 0),
            "tokens_completion": usage.get("completion_tokens", 0),
            "tokens_total": usage.get("total_tokens", 0),
            "elapsed_seconds": elapsed,
            "finish_reason": choice.get("finish_reason", "unknown"),
        }


# ---------------------------------------------------------------------------
# Historial de ruteo
# ---------------------------------------------------------------------------


def _load_history(history_path: Path) -> list[dict[str, Any]]:
    if not history_path.exists():
        return []
    try:
        with history_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(history_path: Path, history: list[dict[str, Any]], max_entries: int) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    # Rotar si supera el máximo
    if len(history) > max_entries:
        history = history[-max_entries:]
    with history_path.open("w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def record_routing_decision(
    history_path: Path,
    prompt_preview: str,
    decision: dict[str, Any],
    max_entries: int = 500,
) -> None:
    """Guarda una decisión de ruteo en el historial."""
    history = _load_history(history_path)
    entry = {
        "timestamp": _now_iso(),
        "prompt_preview": prompt_preview[:200],
        "destination": decision.get("destination"),
        "model": decision.get("model"),
        "task_type": decision.get("task_type"),
        "complexity_score": decision.get("complexity_score"),
        "estimated_tokens": decision.get("estimated_tokens"),
    }
    history.append(entry)
    _save_history(history_path, history, max_entries)


def get_routing_history(history_path: Path, limit: int = 50) -> list[dict[str, Any]]:
    """
    Retorna el historial de decisiones de ruteo.

    Args:
        history_path: Ruta al archivo de historial JSON.
        limit: Máximo de entradas a retornar.

    Retorna:
        Lista de decisiones ordenadas de más reciente a más antigua.
    """
    if limit < 1 or limit > 1000:
        raise ValidationError(field="limit", message="El límite debe estar entre 1 y 1000.")
    history = _load_history(history_path)
    return list(reversed(history[-limit:]))
