"""
Servidor FastMCP para mcp-prompt-engineer.

Expone 8 herramientas para analizar, mejorar y optimizar prompts para LLMs.
Toda la lógica es heurística local — sin llamadas a modelos externos.

Transporte: configurable mediante MCP_TRANSPORT (stdio | streamable-http).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_prompt_engineer.config import settings
from mcp_prompt_engineer.tools.analyzer import analyze_prompt, classify_prompt
from mcp_prompt_engineer.tools.improver import (
    create_system_prompt,
    decompose_task,
    estimate_tokens,
    generate_variations,
    get_prompt_template,
    improve_prompt,
)
from mcp_shared.logging import get_logger, setup_logging

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name=settings.server_name,
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Context manager de ciclo de vida del servidor MCP."""
    structlog.contextvars.bind_contextvars(server_name=settings.server_name)
    logger.info(
        "Servidor mcp-prompt-engineer iniciando",
        version=settings.server_version,
        max_prompt_length=settings.max_prompt_length,
        max_variations=settings.max_variations,
        default_model=settings.default_model,
        transport=settings.mcp_transport,
    )
    yield
    logger.info("Servidor mcp-prompt-engineer detenido", version=settings.server_version)


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name=settings.server_name,
    instructions=(
        "Servidor MCP especializado en análisis y mejora de prompts para modelos de lenguaje.\n\n"
        "Todo el procesamiento es heurístico y local — sin llamadas a APIs externas.\n\n"
        "## Herramientas disponibles\n\n"
        "### 🔍 Análisis\n"
        "- **analyze_prompt**: Análisis exhaustivo: tokens, idioma, tipo, claridad, "
        "problemas y sugerencias.\n"
        "- **classify_prompt**: Clasifica el tipo de prompt (instrucción, pregunta, "
        "few-shot, sistema, etc.).\n"
        "- **estimate_tokens**: Estima tokens para múltiples modelos (GPT-4, Claude, etc.) "
        "y verifica si cabe en el contexto.\n\n"
        "### ✨ Mejora y generación\n"
        "- **improve_prompt**: Mejora automática aplicando buenas prácticas de prompt "
        "engineering. Retorna el prompt mejorado con diff de cambios.\n"
        "- **generate_variations**: Genera N variaciones del prompt con diferentes enfoques "
        "(rol, CoT, formato estructurado, conciso, audiencia).\n"
        "- **create_system_prompt**: Crea un system prompt estructurado a partir de rol, "
        "contexto y restricciones.\n"
        "- **decompose_task**: Descompone una tarea compleja en subtareas manejables.\n"
        "- **get_prompt_template**: Retorna un template optimizado para un caso de uso "
        "(análisis, código, escritura, traducción, resumen, etc.).\n\n"
        "## Notas\n"
        f"- Longitud máxima de prompt: {settings.max_prompt_length:,} caracteres.\n"
        f"- Variaciones máximas por llamada: {settings.max_variations}.\n"
        "- La estimación de tokens usa tiktoken para modelos OpenAI y heurísticas para Claude."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Helpers de manejo de errores
# ---------------------------------------------------------------------------


def _handle_unexpected_error(tool_name: str, exc: Exception) -> None:
    """Registra un error inesperado y lo relanza como SdkMcpError."""
    logger.exception(
        "Error inesperado en tool MCP",
        tool=tool_name,
        error_type=type(exc).__name__,
        error=str(exc),
    )
    raise SdkMcpError(ErrorData(code=-32603, message=f"Error interno: {exc}"))


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="analyze_prompt",
    description=(
        "Analiza un prompt de LLM de forma exhaustiva usando heurísticas reales. "
        "Detecta: tokens estimados, conteo de palabras, idioma, tipo de prompt, "
        "puntuación de claridad (0–10), problemas (críticos/warnings/info) y fortalezas. "
        "Parámetros: prompt (texto a analizar), "
        "target_model (modelo objetivo opcional: 'gpt-4', 'claude-3-5', etc.). "
        "Retorna: token_count, word_count, language, prompt_type, clarity_score, "
        "issues, strengths, suggestions, has_role, has_examples, has_format_spec."
    ),
)
def tool_analyze_prompt(
    prompt: str,
    target_model: str | None = None,
) -> dict[str, Any]:
    """Análisis exhaustivo de un prompt."""
    try:
        if len(prompt) > settings.max_prompt_length:
            raise SdkMcpError(
                ErrorData(
                    code=-32000,
                    message=(
                        f"El prompt excede la longitud máxima de "
                        f"{settings.max_prompt_length:,} caracteres "
                        f"(actual: {len(prompt):,})."
                    ),
                )
            )
        return analyze_prompt(prompt=prompt, target_model=target_model)
    except SdkMcpError:
        raise
    except Exception as exc:
        _handle_unexpected_error("analyze_prompt", exc)
    return {}


@mcp.tool(
    name="classify_prompt",
    description=(
        "Clasifica el tipo de un prompt con una puntuación de confianza. "
        "Tipos posibles: instruction (tarea directa), question (pregunta abierta), "
        "closed_question (sí/no), few_shot (con ejemplos), system (system prompt), "
        "conversation (conversacional), creative (creativo), code (código). "
        "Parámetro: prompt (texto a clasificar). "
        "Retorna: type, confidence, indicators_found."
    ),
)
def tool_classify_prompt(prompt: str) -> dict[str, Any]:
    """Clasifica el tipo y estructura del prompt."""
    try:
        return classify_prompt(prompt=prompt)
    except Exception as exc:
        _handle_unexpected_error("classify_prompt", exc)
    return {}


@mcp.tool(
    name="estimate_tokens",
    description=(
        "Estima el número de tokens para un texto en múltiples modelos de lenguaje. "
        "Usa tiktoken para modelos OpenAI y heurísticas para Claude. "
        "También indica si el texto cabe en el contexto de cada modelo. "
        "Parámetros: text (texto a analizar), "
        "model (modelo de referencia, por defecto 'gpt-4o'). "
        "Retorna: text_length, word_count, method, tokens (por modelo), context_fit."
    ),
)
def tool_estimate_tokens(
    text: str,
    model: str = "gpt-4o",
) -> dict[str, Any]:
    """Estima tokens para múltiples modelos LLM."""
    try:
        return estimate_tokens(text=text, model=model)
    except Exception as exc:
        _handle_unexpected_error("estimate_tokens", exc)
    return {}


@mcp.tool(
    name="improve_prompt",
    description=(
        "Mejora automáticamente un prompt aplicando buenas prácticas de prompt engineering. "
        "Las mejoras son heurísticas: agrega contexto, clarifica instrucciones, "
        "añade formato si falta, elimina ambigüedades. "
        "Parámetros: prompt (prompt original), goal (objetivo del prompt, opcional), "
        "target_model (modelo objetivo, opcional), "
        "style (estilo deseado: formal | casual | technical | simple | concise, opcional). "
        "Retorna: original, improved, changes (lista de cambios aplicados), "
        "score_before, score_after, improvement_delta."
    ),
)
def tool_improve_prompt(
    prompt: str,
    goal: str | None = None,
    target_model: str | None = None,
    style: str | None = None,
) -> dict[str, Any]:
    """Mejora automática de un prompt con diff de cambios."""
    try:
        if len(prompt) > settings.max_prompt_length:
            raise SdkMcpError(
                ErrorData(
                    code=-32000,
                    message=(
                        f"El prompt excede la longitud máxima de "
                        f"{settings.max_prompt_length:,} caracteres."
                    ),
                )
            )
        return improve_prompt(
            prompt=prompt,
            goal=goal,
            target_model=target_model,
            style=style,
        )
    except SdkMcpError:
        raise
    except Exception as exc:
        _handle_unexpected_error("improve_prompt", exc)
    return {}


@mcp.tool(
    name="generate_variations",
    description=(
        "Genera N variaciones del prompt con diferentes enfoques de prompt engineering: "
        "role_injection (añade rol experto), chain_of_thought (razonamiento paso a paso), "
        "structured_output (plantilla de salida), concise (versión condensada), "
        "audience_context (adapta para audiencia específica). "
        "Parámetros: prompt (prompt base), n (número de variaciones, 1–10, por defecto 3). "
        "Retorna: lista de variaciones con variation, approach, description, clarity_score."
    ),
)
def tool_generate_variations(
    prompt: str,
    n: int = 3,
) -> list[dict[str, Any]]:
    """Genera N variaciones del prompt con diferentes enfoques."""
    try:
        clamped_n = max(1, min(n, settings.max_variations))
        return generate_variations(prompt=prompt, n=clamped_n)
    except Exception as exc:
        _handle_unexpected_error("generate_variations", exc)
    return []


@mcp.tool(
    name="create_system_prompt",
    description=(
        "Crea un system prompt estructurado y completo a partir de componentes. "
        "Parámetros: role (rol o persona del asistente, ej: 'experto en finanzas'), "
        "context (contexto de uso o empresa), "
        "constraints (restricciones o reglas a seguir, opcional). "
        "Retorna: system_prompt (texto listo para usar como system message)."
    ),
)
def tool_create_system_prompt(
    role: str,
    context: str,
    constraints: str | None = None,
) -> dict[str, Any]:
    """Crea un system prompt estructurado."""
    try:
        return create_system_prompt(
            role=role,
            context=context,
            constraints=constraints,
        )
    except Exception as exc:
        _handle_unexpected_error("create_system_prompt", exc)
    return {}


@mcp.tool(
    name="decompose_task",
    description=(
        "Descompone una tarea compleja en subtareas numeradas y manejables. "
        "Útil para tareas de múltiples pasos que abruman al modelo en un solo prompt. "
        "Parámetro: task (descripción de la tarea compleja). "
        "Retorna: lista de subtareas con step, title, description, prompt_suggestion."
    ),
)
def tool_decompose_task(task: str) -> list[dict[str, Any]]:
    """Descompone una tarea compleja en subtareas."""
    try:
        return decompose_task(task=task)
    except Exception as exc:
        _handle_unexpected_error("decompose_task", exc)
    return []


@mcp.tool(
    name="get_prompt_template",
    description=(
        "Retorna un template de prompt optimizado para un caso de uso específico. "
        "Casos de uso disponibles: analysis, code_review, code_generation, writing, "
        "translation, summarization, classification, extraction, qa, brainstorming, "
        "debugging, documentation, refactoring, testing, explanation. "
        "Parámetro: use_case (nombre del caso de uso). "
        "Retorna: use_case, template, placeholders (variables a reemplazar), "
        "description, tips."
    ),
)
def tool_get_prompt_template(use_case: str) -> dict[str, Any]:
    """Retorna un template optimizado para un caso de uso."""
    try:
        return get_prompt_template(use_case=use_case)
    except Exception as exc:
        _handle_unexpected_error("get_prompt_template", exc)
    return {}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Punto de entrada principal del servidor."""
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
