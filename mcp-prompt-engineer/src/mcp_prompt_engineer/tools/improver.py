"""
Módulo de mejora y optimización de prompts para LLMs.

Implementa mejoras heurísticas reales sin llamadas a modelos externos:
- Mejora automática de prompts
- Generación de variaciones
- Estimación de tokens con tiktoken
- Creación de system prompts profesionales
- Descomposición de tareas
- Enriquecimiento con ejemplos few-shot
- Templates por caso de uso
"""

from __future__ import annotations

import re
from typing import Any

from .analyzer import (
    analyze_prompt,
    classify_prompt,
    _has_examples,
    _has_format_spec,
    _has_role,
    _is_closed_question,
    _detect_vague_words,
    _compute_clarity_score,
    _detect_contradictions,
    _count_words,
    _estimate_tokens,
)

# ---------------------------------------------------------------------------
# Constantes de templates
# ---------------------------------------------------------------------------

_ROLE_TEMPLATES: dict[str, str] = {
    "summarize": "experto en síntesis y comprensión de textos",
    "translate": "traductor profesional y lingüista experto",
    "classify": "especialista en categorización y taxonomía",
    "extract": "analista de información y extracción de datos",
    "generate": "redactor creativo y experto en contenido",
    "analyze": "analista crítico y experto en evaluación",
    "code": "ingeniero de software senior con amplia experiencia",
    "qa": "experto en garantía de calidad y pruebas de software",
}

_FORMAT_TEMPLATES: dict[str, str] = {
    "summarize": "Proporciona un resumen estructurado con: 1) Puntos clave (bullets), 2) Conclusión principal.",
    "translate": "Proporciona únicamente la traducción, sin notas adicionales a menos que haya ambigüedades importantes.",
    "classify": "Responde en formato JSON con los campos: 'category', 'confidence' (0.0-1.0) y 'reasoning'.",
    "extract": "Responde en formato JSON con una lista de objetos que contengan los campos extraídos.",
    "generate": "Genera el contenido directamente, sin preámbulos ni meta-comentarios.",
    "analyze": "Estructura tu análisis con: 1) Resumen ejecutivo, 2) Análisis detallado, 3) Recomendaciones.",
    "code": "Proporciona el código con comentarios explicativos y, al final, una sección de 'Uso' con ejemplo.",
    "qa": "Lista cada caso de prueba en formato: ID | Escenario | Pasos | Resultado esperado.",
}

_TASK_TEMPLATES: dict[str, str] = {
    "summarize": (
        "Eres un {role}.\n\n"
        "## Tarea\n"
        "Resume el siguiente texto manteniendo los puntos más importantes:\n\n"
        "```\n{input_placeholder}\n```\n\n"
        "## Restricciones\n"
        "- Longitud máxima: {max_length} palabras\n"
        "- Idioma de salida: {language}\n\n"
        "## Formato de salida\n"
        "{format}"
    ),
    "translate": (
        "Eres un {role}.\n\n"
        "## Tarea\n"
        "Traduce el siguiente texto de {source_lang} a {target_lang}:\n\n"
        "```\n{input_placeholder}\n```\n\n"
        "## Formato de salida\n"
        "{format}"
    ),
    "classify": (
        "Eres un {role}.\n\n"
        "## Tarea\n"
        "Clasifica el siguiente elemento en una de las categorías disponibles:\n\n"
        "**Elemento a clasificar:**\n{input_placeholder}\n\n"
        "**Categorías disponibles:**\n{categories}\n\n"
        "## Formato de salida\n"
        "{format}"
    ),
    "extract": (
        "Eres un {role}.\n\n"
        "## Tarea\n"
        "Extrae la siguiente información del texto dado:\n\n"
        "**Campos a extraer:** {fields}\n\n"
        "**Texto fuente:**\n```\n{input_placeholder}\n```\n\n"
        "## Formato de salida\n"
        "{format}"
    ),
    "generate": (
        "Eres un {role}.\n\n"
        "## Tarea\n"
        "Genera {content_type} con las siguientes especificaciones:\n\n"
        "**Tema:** {topic}\n"
        "**Audiencia:** {audience}\n"
        "**Tono:** {tone}\n"
        "**Extensión aproximada:** {length}\n\n"
        "## Formato de salida\n"
        "{format}"
    ),
    "analyze": (
        "Eres un {role}.\n\n"
        "## Tarea\n"
        "Analiza el siguiente contenido en detalle:\n\n"
        "```\n{input_placeholder}\n```\n\n"
        "## Preguntas guía\n"
        "- ¿Cuáles son los puntos fuertes y débiles?\n"
        "- ¿Qué patrones o tendencias son evidentes?\n"
        "- ¿Qué recomendaciones se derivan del análisis?\n\n"
        "## Formato de salida\n"
        "{format}"
    ),
    "code": (
        "Eres un {role}.\n\n"
        "## Tarea\n"
        "Implementa la siguiente funcionalidad:\n\n"
        "**Descripción:** {description}\n"
        "**Lenguaje:** {language}\n"
        "**Restricciones:** {constraints}\n\n"
        "## Requisitos\n"
        "- Código limpio y bien documentado\n"
        "- Manejo adecuado de errores\n"
        "- Eficiencia y legibilidad\n\n"
        "## Formato de salida\n"
        "{format}"
    ),
    "qa": (
        "Eres un {role}.\n\n"
        "## Tarea\n"
        "Genera casos de prueba para la siguiente funcionalidad:\n\n"
        "**Funcionalidad:** {feature}\n"
        "**Tipo de pruebas:** {test_type}\n\n"
        "## Cobertura requerida\n"
        "- Casos nominales (happy path)\n"
        "- Casos de borde (edge cases)\n"
        "- Casos de error\n\n"
        "## Formato de salida\n"
        "{format}"
    ),
    "qa_answer": (
        "Eres un {role}.\n\n"
        "## Contexto\n"
        "{context}\n\n"
        "## Pregunta\n"
        "{question}\n\n"
        "## Instrucciones\n"
        "- Responde únicamente basándote en el contexto proporcionado.\n"
        "- Si la información no está en el contexto, indícalo explícitamente.\n"
        "- Cita las partes relevantes del contexto.\n\n"
        "## Formato de salida\n"
        "{format}"
    ),
}

# Vague word replacement suggestions
_VAGUE_REPLACEMENTS: dict[str, str] = {
    "algo": "especifica qué exactamente",
    "algunas": "especifica cuántas",
    "algunos": "especifica cuántos",
    "cosas": "especifica qué tipo de elementos",
    "temas": "especifica los temas exactos",
    "aspectos": "especifica qué aspectos",
    "elementos": "especifica qué elementos",
    "características": "especifica qué características",
    "something": "specify what exactly",
    "things": "specify what type of items",
    "stuff": "specify what exactly",
    "various": "enumerate the specific items",
    "several": "specify the exact number",
}


# ---------------------------------------------------------------------------
# Estimación de tokens
# ---------------------------------------------------------------------------


def estimate_tokens(text: str, model: str = "gpt-4o") -> dict[str, Any]:
    """
    Estima el número de tokens para un texto dado en múltiples modelos.

    Usa tiktoken para modelos OpenAI y heurísticas para Claude.

    Args:
        text: El texto a tokenizar.
        model: Modelo de referencia para tiktoken.

    Returns:
        dict con token_count por modelo y método usado.
    """
    char_count = len(text)
    word_count = _count_words(text)

    # Estimación heurística base
    heuristic_gpt = max(1, char_count // 4)
    heuristic_claude = max(1, char_count * 10 // 35)  # ~3.5 chars/token

    # Intentar usar tiktoken para modelos OpenAI
    tiktoken_count: int | None = None
    method = "heuristic"

    try:
        import tiktoken

        # Mapear nombres de modelos a encodings de tiktoken
        model_lower = model.lower()
        if "gpt-4" in model_lower or "gpt4" in model_lower:
            encoding_name = "cl100k_base"
        elif "gpt-3.5" in model_lower or "gpt35" in model_lower:
            encoding_name = "cl100k_base"
        elif "o1" in model_lower or "o3" in model_lower:
            encoding_name = "o200k_base"
        elif "text-embedding" in model_lower:
            encoding_name = "cl100k_base"
        else:
            encoding_name = "cl100k_base"

        enc = tiktoken.get_encoding(encoding_name)
        tiktoken_count = len(enc.encode(text))
        method = f"tiktoken:{encoding_name}"
    except Exception:
        pass

    gpt4_count = tiktoken_count if tiktoken_count is not None else heuristic_gpt

    return {
        "text_length": char_count,
        "word_count": word_count,
        "model_requested": model,
        "method": method,
        "tokens": {
            "gpt-4o": gpt4_count,
            "gpt-4-turbo": gpt4_count,
            "gpt-3.5-turbo": tiktoken_count if tiktoken_count is not None else heuristic_gpt,
            "claude-3-5-sonnet": heuristic_claude,
            "claude-3-opus": heuristic_claude,
            "claude-3-haiku": heuristic_claude,
        },
        "context_fit": {
            "gpt-4o (128k)": "fits" if gpt4_count <= 128_000 else "exceeds",
            "claude-3-5-sonnet (200k)": "fits" if heuristic_claude <= 200_000 else "exceeds",
            "gpt-3.5-turbo (16k)": (
                "fits"
                if (tiktoken_count or heuristic_gpt) <= 16_000
                else "exceeds"
            ),
        },
    }


# ---------------------------------------------------------------------------
# Mejora de prompts
# ---------------------------------------------------------------------------


def _apply_improvements(
    prompt: str,
    analysis: dict[str, Any],
    goal: str | None,
    style: str | None,
) -> tuple[str, list[str]]:
    """
    Aplica mejoras heurísticas al prompt basándose en el análisis.

    Returns:
        Tuple (improved_prompt, list_of_changes)
    """
    improved = prompt.strip()
    changes: list[str] = []

    word_count: int = analysis["word_count"]
    prompt_type: str = analysis["prompt_type"]
    has_role: bool = analysis["has_role"]
    has_format: bool = analysis["has_format_spec"]
    is_closed_q: bool = analysis.get("is_closed_question", False)
    vague_words: list[str] = analysis.get("vague_words_found", [])

    # 1. Convertir pregunta cerrada a abierta
    if is_closed_q:
        # Detectar patrón de pregunta cerrada en español
        match_es = re.match(
            r"^(¿?)((es|son|está|están|hay|puede|puedes|debería|debo)\s+)",
            improved.strip(),
            re.IGNORECASE,
        )
        if match_es:
            # Reemplazar con apertura más descriptiva
            improved = re.sub(
                r"^¿?(es|son|está|están|hay|puede|puedes|debería|debo)\s+",
                "¿Cuáles son las razones por las que ",
                improved.strip(),
                flags=re.IGNORECASE,
                count=1,
            )
            if not improved.endswith("?"):
                improved = improved.rstrip("?") + "?"
            changes.append("Pregunta cerrada convertida a pregunta abierta.")

    # 2. Añadir rol si no existe y el prompt es suficientemente largo
    if not has_role and word_count >= 15 and prompt_type in {"analytical", "instruction"}:
        role_map = {
            "analytical": "experto en análisis y evaluación",
            "instruction": "especialista en el área solicitada",
            "creative": "redactor creativo experimentado",
            "question": "experto en el tema preguntado",
            "conversational": "asistente experto",
        }
        role = role_map.get(prompt_type, "experto en el área")
        improved = f"Eres un {role}.\n\n{improved}"
        changes.append(f"Se añadió definición de rol: '{role}'.")

    # 3. Añadir chain-of-thought para prompts analíticos
    if prompt_type == "analytical" and not re.search(
        r"\b(paso a paso|step by step|razona|think)\b", improved, re.IGNORECASE
    ):
        improved = improved + "\n\nRazona paso a paso antes de dar tu respuesta final."
        changes.append("Se añadió instrucción de razonamiento paso a paso (chain-of-thought).")

    # 4. Añadir formato de salida si no existe y el prompt es largo
    if not has_format and word_count >= 30:
        default_formats: dict[str, str] = {
            "analytical": "\n\nEstructura tu respuesta con: 1) Resumen, 2) Análisis, 3) Conclusiones.",
            "instruction": "\n\nPresenta tu respuesta de forma clara y organizada.",
            "creative": "\n\nGenera el contenido solicitado directamente, sin meta-comentarios.",
            "question": "\n\nResponde de forma completa y estructurada.",
            "conversational": "",
        }
        fmt = default_formats.get(prompt_type, "")
        if fmt:
            improved = improved + fmt
            changes.append("Se añadió especificación del formato de salida.")

    # 5. Si hay objetivo específico (goal), añadirlo como contexto
    if goal and goal.strip():
        improved = f"## Objetivo\n{goal.strip()}\n\n## Prompt\n{improved}"
        changes.append("Se añadió el objetivo como contexto estructurado.")

    # 6. Si hay estilo específico (style), añadir al final
    if style and style.strip():
        style_map: dict[str, str] = {
            "formal": "Usa un tono formal y profesional.",
            "casual": "Usa un tono conversacional y amigable.",
            "technical": "Usa terminología técnica precisa.",
            "simple": "Usa lenguaje simple y accesible para cualquier audiencia.",
            "concise": "Sé conciso y directo; evita explicaciones innecesarias.",
        }
        style_instruction = style_map.get(style.lower(), f"Estilo de respuesta: {style}.")
        improved = improved + f"\n\n{style_instruction}"
        changes.append(f"Se añadió instrucción de estilo: '{style}'.")

    # 7. Limpiar espacios múltiples y saltos de línea excesivos
    improved = re.sub(r"\n{3,}", "\n\n", improved)
    improved = improved.strip()

    if not changes:
        changes.append(
            "El prompt ya tiene buena estructura; se aplicaron mejoras menores de formato."
        )

    return improved, changes


def improve_prompt(
    prompt: str,
    goal: str | None = None,
    target_model: str | None = None,
    style: str | None = None,
) -> dict[str, Any]:
    """
    Mejora un prompt aplicando heurísticas basadas en buenas prácticas de prompt engineering.

    Args:
        prompt: El prompt original a mejorar.
        goal: Objetivo o propósito del prompt (opcional).
        target_model: Modelo de lenguaje objetivo (opcional).
        style: Estilo de respuesta deseado (formal, casual, technical, simple, concise).

    Returns:
        dict con original, improved, changes, score_before y score_after.
    """
    # Analizar el prompt original
    analysis_before = analyze_prompt(prompt, target_model)
    score_before = analysis_before["clarity_score"]

    # Aplicar mejoras
    improved, changes = _apply_improvements(prompt, analysis_before, goal, target_model)

    # Analizar el prompt mejorado
    analysis_after = analyze_prompt(improved, target_model)
    score_after = analysis_after["clarity_score"]

    return {
        "original": prompt,
        "improved": improved,
        "changes": changes,
        "score_before": score_before,
        "score_after": score_after,
        "improvement_delta": round(score_after - score_before, 1),
        "analysis_before": analysis_before,
        "analysis_after": analysis_after,
    }


# ---------------------------------------------------------------------------
# Generación de variaciones
# ---------------------------------------------------------------------------


def generate_variations(prompt: str, n: int = 3) -> list[dict[str, Any]]:
    """
    Genera N variaciones del prompt con diferentes enfoques.

    Args:
        prompt: El prompt base para generar variaciones.
        n: Número de variaciones a generar (1–10).

    Returns:
        Lista de dicts con variation, approach y description.
    """
    n = max(1, min(n, 10))
    analysis = analyze_prompt(prompt)
    prompt_type = analysis["prompt_type"]
    has_role = analysis["has_role"]
    word_count = analysis["word_count"]

    variations: list[dict[str, Any]] = []

    # Variación 1: Agregar rol de experto
    if not has_role:
        v1 = f"Actúa como un experto senior en el área. {prompt}"
        variations.append({
            "variation": v1,
            "approach": "role_injection",
            "description": "Se añadió un rol de experto para orientar el estilo de respuesta.",
            "clarity_score": analyze_prompt(v1)["clarity_score"],
        })

    # Variación 2: Chain-of-thought explícito
    v2 = (
        f"{prompt}\n\n"
        "Antes de responder, razona paso a paso:\n"
        "1. ¿Qué información necesito?\n"
        "2. ¿Cuál es el enfoque correcto?\n"
        "3. ¿Cuál es mi respuesta final?"
    )
    variations.append({
        "variation": v2,
        "approach": "chain_of_thought",
        "description": "Se añadió estructura de razonamiento paso a paso.",
        "clarity_score": analyze_prompt(v2)["clarity_score"],
    })

    # Variación 3: Formato de salida estructurado
    if not analysis["has_format_spec"]:
        v3 = (
            f"{prompt}\n\n"
            "Estructura tu respuesta exactamente así:\n"
            "**Resumen:** [1-2 oraciones]\n"
            "**Desarrollo:** [detalle principal]\n"
            "**Conclusión:** [cierre y próximos pasos si aplica]"
        )
        variations.append({
            "variation": v3,
            "approach": "structured_output",
            "description": "Se añadió una plantilla de formato de salida estructurada.",
            "clarity_score": analyze_prompt(v3)["clarity_score"],
        })

    # Variación 4: Versión concisa (si el prompt es largo)
    if word_count > 50:
        # Tomar la primera oración/párrafo principal
        first_para = prompt.strip().split("\n\n")[0].strip()
        v4 = (
            f"{first_para}\n\n"
            "Sé directo y conciso. Responde en máximo 3 párrafos."
        )
        variations.append({
            "variation": v4,
            "approach": "concise",
            "description": "Versión condensada que preserva la intención principal.",
            "clarity_score": analyze_prompt(v4)["clarity_score"],
        })

    # Variación 5: Versión con contexto de audiencia
    v5 = (
        f"Contexto: Estoy preparando una respuesta para una audiencia profesional "
        f"con conocimientos intermedios en el tema.\n\n{prompt}\n\n"
        "Adapta tu respuesta para esta audiencia específica."
    )
    variations.append({
        "variation": v5,
        "approach": "audience_context",
        "description": "Se añadió contexto de audiencia para personalizar la respuesta.",
        "clarity_score": analyze_prompt(v5)["clarity_score"],
    })

    # Variación 6: Con ejemplos solicitados explícitamente
    if not analysis["has_examples"]:
        v6 = (
            f"{prompt}\n\n"
            "Incluye al menos 2 ejemplos concretos para ilustrar tu respuesta."
        )
        variations.append({
            "variation": v6,
            "approach": "examples_requested",
            "description": "Se añadió solicitud explícita de ejemplos ilustrativos.",
            "clarity_score": analyze_prompt(v6)["clarity_score"],
        })

    # Variación 7: Versión en inglés (si el prompt está en español)
    if analysis["language"] in {"es", "ca", "pt"}:
        english_prefix = "You are an expert assistant. "
        # Translate key parts — use a template since we can't call LLM
        v7 = (
            f"{english_prefix}[English version of: {prompt[:100]}{'...' if len(prompt) > 100 else ''}]\n\n"
            "Note: This is a template for the English version. Replace [English version of: ...] "
            "with the actual English translation of the original prompt."
        )
        variations.append({
            "variation": v7,
            "approach": "english_version",
            "description": "Template para versión en inglés (requiere traducción manual del contenido).",
            "clarity_score": 6.0,
        })

    # Variación 8: Prompt tipo sistema (system prompt)
    v8 = (
        "## System\n"
        f"Eres un asistente especializado. {prompt}\n\n"
        "## Instrucciones adicionales\n"
        "- Responde siempre en el idioma del usuario\n"
        "- Si tienes dudas, pide aclaración antes de proceder\n"
        "- Cita fuentes cuando sea relevante"
    )
    variations.append({
        "variation": v8,
        "approach": "system_prompt_style",
        "description": "Versión reformateada como system prompt con instrucciones adicionales.",
        "clarity_score": analyze_prompt(v8)["clarity_score"],
    })

    # Variación 9: Con criterios de éxito
    v9 = (
        f"{prompt}\n\n"
        "## Criterios de éxito\n"
        "Tu respuesta será exitosa si:\n"
        "- Es precisa y verificable\n"
        "- Está bien organizada y es fácil de leer\n"
        "- Responde completamente a lo solicitado"
    )
    variations.append({
        "variation": v9,
        "approach": "success_criteria",
        "description": "Se añadieron criterios de éxito explícitos para guiar la respuesta.",
        "clarity_score": analyze_prompt(v9)["clarity_score"],
    })

    # Variación 10: Con restricciones negativas
    v10 = (
        f"{prompt}\n\n"
        "## Restricciones\n"
        "- NO uses jerga o términos técnicos sin explicarlos\n"
        "- NO repitas información ya mencionada\n"
        "- NO respondas con información desactualizada si conoces la versión actual"
    )
    variations.append({
        "variation": v10,
        "approach": "negative_constraints",
        "description": "Se añadieron restricciones negativas para aclarar qué evitar.",
        "clarity_score": analyze_prompt(v10)["clarity_score"],
    })

    # Retornar solo las primeras N variaciones, ordenadas por clarity_score
    result = sorted(variations, key=lambda x: x["clarity_score"], reverse=True)
    return result[:n]


# ---------------------------------------------------------------------------
# System prompt generator
# ---------------------------------------------------------------------------


def create_system_prompt(
    role: str,
    context: str,
    constraints: str | None = None,
    output_format: str | None = None,
) -> str:
    """
    Genera un system prompt profesional a partir de los componentes dados.

    Args:
        role: El rol o persona del asistente (ej: "experto en seguridad informática").
        context: El contexto o dominio del sistema.
        constraints: Restricciones o reglas a seguir (opcional).
        output_format: Formato de salida esperado (opcional).

    Returns:
        System prompt completo y formateado.
    """
    sections: list[str] = []

    # Sección de identidad y rol
    sections.append(f"# Identidad\nEres {role}.")

    # Sección de contexto
    sections.append(f"# Contexto\n{context.strip()}")

    # Sección de capacidades implícitas
    capabilities = (
        "# Capacidades\n"
        "- Provides accurate, well-researched responses\n"
        "- Asks for clarification when the request is ambiguous\n"
        "- Acknowledges limitations and uncertainty when appropriate\n"
        "- Responds in the language of the user"
    )
    sections.append(capabilities)

    # Sección de restricciones
    if constraints and constraints.strip():
        sections.append(f"# Restricciones\n{constraints.strip()}")
    else:
        default_constraints = (
            "# Restricciones\n"
            "- No proporciones información falsa o no verificada\n"
            "- Si no sabes algo, indícalo claramente\n"
            "- Mantén el foco en el dominio establecido"
        )
        sections.append(default_constraints)

    # Sección de formato de salida
    if output_format and output_format.strip():
        sections.append(f"# Formato de salida\n{output_format.strip()}")

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Descomposición de tareas
# ---------------------------------------------------------------------------


def decompose_task(task: str) -> list[dict[str, Any]]:
    """
    Descompone una tarea compleja en subtareas numeradas manejables.

    Args:
        task: Descripción de la tarea compleja a descomponer.

    Returns:
        Lista de dicts con step_number, subtask, description y estimated_complexity.
    """
    analysis = analyze_prompt(task)
    prompt_type = analysis["prompt_type"]
    word_count = analysis["word_count"]

    subtasks: list[dict[str, Any]] = []

    # Estrategia genérica de descomposición por tipo
    if prompt_type == "analytical":
        subtasks = [
            {
                "step_number": 1,
                "subtask": "Recopilación de información",
                "description": f"Identificar y reunir toda la información relevante sobre: {task[:100]}",
                "prompt": f"Lista todos los datos y hechos relevantes para analizar: {task}",
                "estimated_complexity": "baja",
            },
            {
                "step_number": 2,
                "subtask": "Análisis preliminar",
                "description": "Examinar la información recopilada para identificar patrones y relaciones.",
                "prompt": f"Basándote en la información anterior, identifica los patrones clave relacionados con: {task}",
                "estimated_complexity": "media",
            },
            {
                "step_number": 3,
                "subtask": "Análisis profundo",
                "description": "Profundizar en los hallazgos más importantes.",
                "prompt": "Analiza en detalle los patrones identificados. ¿Cuáles son las causas y consecuencias?",
                "estimated_complexity": "alta",
            },
            {
                "step_number": 4,
                "subtask": "Síntesis y conclusiones",
                "description": "Consolidar el análisis en conclusiones accionables.",
                "prompt": "Sintetiza el análisis anterior en conclusiones claras y recomendaciones específicas.",
                "estimated_complexity": "media",
            },
        ]

    elif prompt_type == "creative":
        subtasks = [
            {
                "step_number": 1,
                "subtask": "Definición de parámetros creativos",
                "description": "Establecer el tono, estilo, audiencia y restricciones del contenido.",
                "prompt": f"Define los parámetros para: {task}. ¿Cuál es el tono, audiencia y objetivo?",
                "estimated_complexity": "baja",
            },
            {
                "step_number": 2,
                "subtask": "Lluvia de ideas",
                "description": "Generar múltiples ideas y enfoques creativos posibles.",
                "prompt": f"Genera 5 enfoques creativos diferentes para: {task}",
                "estimated_complexity": "media",
            },
            {
                "step_number": 3,
                "subtask": "Desarrollo del borrador",
                "description": "Crear el contenido principal basándose en el mejor enfoque.",
                "prompt": "Desarrolla un borrador completo usando el mejor enfoque identificado.",
                "estimated_complexity": "alta",
            },
            {
                "step_number": 4,
                "subtask": "Refinamiento y pulido",
                "description": "Revisar, mejorar y pulir el contenido generado.",
                "prompt": "Revisa el borrador anterior y mejora: fluidez, claridad, impacto y originalidad.",
                "estimated_complexity": "media",
            },
        ]

    elif prompt_type == "instruction":
        subtasks = [
            {
                "step_number": 1,
                "subtask": "Comprensión de requisitos",
                "description": "Clarificar todos los requisitos y condiciones de éxito.",
                "prompt": f"¿Cuáles son los requisitos específicos, restricciones y criterios de éxito para: {task}?",
                "estimated_complexity": "baja",
            },
            {
                "step_number": 2,
                "subtask": "Planificación del enfoque",
                "description": "Definir el método o estrategia a seguir.",
                "prompt": "¿Cuál es el mejor enfoque paso a paso para completar la tarea?",
                "estimated_complexity": "media",
            },
            {
                "step_number": 3,
                "subtask": "Ejecución",
                "description": "Realizar la tarea según el plan definido.",
                "prompt": f"Ejecuta la siguiente tarea siguiendo el plan establecido: {task}",
                "estimated_complexity": "alta",
            },
            {
                "step_number": 4,
                "subtask": "Verificación y entrega",
                "description": "Revisar el resultado y asegurar que cumple los requisitos.",
                "prompt": "Revisa el resultado anterior. ¿Cumple todos los requisitos? ¿Hay alguna mejora necesaria?",
                "estimated_complexity": "baja",
            },
        ]

    else:
        # Descomposición genérica para preguntas y conversacional
        subtasks = [
            {
                "step_number": 1,
                "subtask": "Contextualización",
                "description": "Establecer el contexto y alcance de la respuesta.",
                "prompt": f"¿Cuál es el contexto relevante para responder: {task}?",
                "estimated_complexity": "baja",
            },
            {
                "step_number": 2,
                "subtask": "Respuesta principal",
                "description": "Proporcionar la respuesta o solución central.",
                "prompt": f"Responde de forma completa y precisa: {task}",
                "estimated_complexity": "media",
            },
            {
                "step_number": 3,
                "subtask": "Ejemplos y evidencia",
                "description": "Ilustrar la respuesta con ejemplos concretos.",
                "prompt": "Proporciona ejemplos concretos que ilustren la respuesta anterior.",
                "estimated_complexity": "media",
            },
            {
                "step_number": 4,
                "subtask": "Conclusión y siguientes pasos",
                "description": "Resumir y proponer acciones o próximos pasos.",
                "prompt": "Resume los puntos clave y sugiere próximos pasos o recursos adicionales.",
                "estimated_complexity": "baja",
            },
        ]

    return subtasks


# ---------------------------------------------------------------------------
# Few-shot examples
# ---------------------------------------------------------------------------


def add_few_shot_examples(
    prompt: str,
    examples: list[dict[str, str]],
) -> str:
    """
    Enriquece un prompt con ejemplos few-shot input/output.

    Args:
        prompt: El prompt base.
        examples: Lista de dicts con claves 'input' y 'output'.

    Returns:
        Prompt enriquecido con los ejemplos.
    """
    if not examples:
        return prompt

    examples_block_lines: list[str] = ["## Ejemplos\n"]
    for i, ex in enumerate(examples, 1):
        inp = ex.get("input", "").strip()
        out = ex.get("output", "").strip()
        examples_block_lines.append(f"### Ejemplo {i}")
        examples_block_lines.append(f"**Entrada:** {inp}")
        examples_block_lines.append(f"**Salida:** {out}")
        examples_block_lines.append("")

    examples_block = "\n".join(examples_block_lines)
    separator = "\n\n---\n\n"

    return f"{examples_block}{separator}## Tarea\n{prompt}"


# ---------------------------------------------------------------------------
# Prompt templates por caso de uso
# ---------------------------------------------------------------------------


def get_prompt_template(use_case: str) -> dict[str, Any]:
    """
    Retorna un template de prompt optimizado para el caso de uso especificado.

    Args:
        use_case: Caso de uso. Uno de: summarize, translate, classify, extract,
                  generate, analyze, code, qa.

    Returns:
        dict con template, placeholders, description y example.
    """
    templates: dict[str, dict[str, Any]] = {
        "summarize": {
            "template": (
                "Eres un experto en síntesis y comprensión de textos.\n\n"
                "## Tarea\n"
                "Resume el siguiente texto de forma clara y concisa:\n\n"
                "```\n{{TEXT}}\n```\n\n"
                "## Parámetros\n"
                "- Extensión máxima: {{MAX_WORDS}} palabras\n"
                "- Idioma: {{LANGUAGE}}\n"
                "- Enfoque: {{FOCUS}}\n\n"
                "## Formato de salida\n"
                "**Resumen ejecutivo:** [1-2 oraciones con la idea principal]\n\n"
                "**Puntos clave:**\n"
                "- [punto 1]\n"
                "- [punto 2]\n"
                "- [punto 3]\n\n"
                "**Conclusión:** [mensaje final o llamada a la acción]"
            ),
            "placeholders": {
                "{{TEXT}}": "El texto a resumir",
                "{{MAX_WORDS}}": "Número máximo de palabras (ej: 150)",
                "{{LANGUAGE}}": "Idioma de salida (ej: español, English)",
                "{{FOCUS}}": "Aspecto a priorizar (ej: datos técnicos, narrativa, estadísticas)",
            },
            "description": "Template para resumir documentos con formato estructurado.",
            "example": "Resume este artículo científico en máximo 200 palabras, en español, enfocándote en los resultados y conclusiones.",
            "use_case": "summarize",
        },
        "translate": {
            "template": (
                "Eres un traductor profesional y lingüista experto.\n\n"
                "## Tarea\n"
                "Traduce el siguiente texto de {{SOURCE_LANG}} a {{TARGET_LANG}}:\n\n"
                "```\n{{TEXT}}\n```\n\n"
                "## Instrucciones\n"
                "- Preserva el tono y estilo del original\n"
                "- Adapta expresiones idiomáticas cuando sea necesario\n"
                "- Si hay términos técnicos ambiguos, añade una nota breve\n\n"
                "## Formato de salida\n"
                "Proporciona únicamente la traducción. Si hay términos ambiguos, "
                "añádelos al final en una sección '**Notas de traducción:**'."
            ),
            "placeholders": {
                "{{TEXT}}": "El texto a traducir",
                "{{SOURCE_LANG}}": "Idioma origen (ej: inglés, francés)",
                "{{TARGET_LANG}}": "Idioma destino (ej: español, German)",
            },
            "description": "Template para traducciones profesionales con notas opcionales.",
            "example": "Traduce este contrato del inglés al español, preservando la terminología legal.",
            "use_case": "translate",
        },
        "classify": {
            "template": (
                "Eres un especialista en categorización y taxonomía.\n\n"
                "## Tarea\n"
                "Clasifica el siguiente elemento en la categoría más apropiada:\n\n"
                "**Elemento:** {{ITEM}}\n\n"
                "**Categorías disponibles:**\n"
                "{{CATEGORIES}}\n\n"
                "## Instrucciones\n"
                "- Elige la categoría más específica y apropiada\n"
                "- Si el elemento podría clasificarse en múltiples categorías, "
                "elige la dominante\n"
                "- Explica brevemente tu razonamiento\n\n"
                "## Formato de salida (JSON)\n"
                "```json\n"
                "{\n"
                '  "category": "nombre_categoria",\n'
                '  "confidence": 0.95,\n'
                '  "reasoning": "Explicación breve",\n'
                '  "alternative_categories": ["cat2", "cat3"]\n'
                "}\n"
                "```"
            ),
            "placeholders": {
                "{{ITEM}}": "El elemento a clasificar",
                "{{CATEGORIES}}": "Lista de categorías válidas (una por línea, con descripción opcional)",
            },
            "description": "Template para clasificación con output JSON estructurado.",
            "example": "Clasifica este email como: urgente, normal, spam o informativo.",
            "use_case": "classify",
        },
        "extract": {
            "template": (
                "Eres un analista de información y extracción de datos.\n\n"
                "## Tarea\n"
                "Extrae la siguiente información del texto dado:\n\n"
                "**Campos a extraer:**\n"
                "{{FIELDS}}\n\n"
                "**Texto fuente:**\n"
                "```\n{{TEXT}}\n```\n\n"
                "## Instrucciones\n"
                "- Extrae solo información explícita en el texto\n"
                "- Si un campo no está disponible, usa null\n"
                "- No infiereas información que no esté presente\n\n"
                "## Formato de salida (JSON)\n"
                "```json\n"
                "{\n"
                '  "extracted_fields": {\n'
                '    "campo1": "valor o null",\n'
                '    "campo2": "valor o null"\n'
                "  },\n"
                '  "confidence": 0.9,\n'
                '  "notes": "Observaciones relevantes"\n'
                "}\n"
                "```"
            ),
            "placeholders": {
                "{{FIELDS}}": "Lista de campos a extraer (ej: nombre, fecha, monto, empresa)",
                "{{TEXT}}": "El texto del que extraer la información",
            },
            "description": "Template para extracción estructurada de datos con output JSON.",
            "example": "Extrae: nombre del cliente, fecha, monto total y método de pago de esta factura.",
            "use_case": "extract",
        },
        "generate": {
            "template": (
                "Eres un redactor creativo y experto en contenido.\n\n"
                "## Tarea\n"
                "Genera {{CONTENT_TYPE}} con las siguientes especificaciones:\n\n"
                "**Tema:** {{TOPIC}}\n"
                "**Audiencia objetivo:** {{AUDIENCE}}\n"
                "**Tono:** {{TONE}}\n"
                "**Extensión:** {{LENGTH}}\n"
                "**Objetivos:** {{GOALS}}\n\n"
                "## Restricciones\n"
                "{{CONSTRAINTS}}\n\n"
                "## Formato de salida\n"
                "Genera el contenido directamente, sin preámbulos ni meta-comentarios. "
                "Comienza con el contenido solicitado."
            ),
            "placeholders": {
                "{{CONTENT_TYPE}}": "Tipo de contenido (ej: artículo de blog, email, descripción de producto)",
                "{{TOPIC}}": "Tema o asunto del contenido",
                "{{AUDIENCE}}": "Audiencia objetivo (ej: profesionales de TI, consumidores generales)",
                "{{TONE}}": "Tono deseado (ej: formal, conversacional, persuasivo, técnico)",
                "{{LENGTH}}": "Extensión aproximada (ej: 500 palabras, 3 párrafos)",
                "{{GOALS}}": "Objetivos del contenido (ej: informar, persuadir, entretener)",
                "{{CONSTRAINTS}}": "Restricciones específicas (ej: no mencionar competidores, incluir CTA)",
            },
            "description": "Template flexible para generación de contenido de cualquier tipo.",
            "example": "Genera un artículo de blog de 800 palabras sobre IA generativa para directores de marketing, tono accesible.",
            "use_case": "generate",
        },
        "analyze": {
            "template": (
                "Eres un analista crítico y experto en evaluación.\n\n"
                "## Tarea\n"
                "Realiza un análisis detallado del siguiente contenido:\n\n"
                "```\n{{CONTENT}}\n```\n\n"
                "## Dimensiones de análisis\n"
                "{{DIMENSIONS}}\n\n"
                "## Instrucciones\n"
                "- Sé objetivo y basa tu análisis en evidencia del texto\n"
                "- Identifica tanto fortalezas como debilidades\n"
                "- Proporciona recomendaciones accionables\n\n"
                "## Formato de salida\n"
                "### 1. Resumen ejecutivo\n"
                "[2-3 oraciones con el hallazgo principal]\n\n"
                "### 2. Análisis detallado\n"
                "[Por cada dimensión: observación + evidencia]\n\n"
                "### 3. Fortalezas identificadas\n"
                "- [fortaleza 1]\n"
                "- [fortaleza 2]\n\n"
                "### 4. Áreas de mejora\n"
                "- [área 1]\n"
                "- [área 2]\n\n"
                "### 5. Recomendaciones\n"
                "- [recomendación 1 — prioridad: alta/media/baja]"
            ),
            "placeholders": {
                "{{CONTENT}}": "El contenido a analizar",
                "{{DIMENSIONS}}": "Dimensiones o aspectos a evaluar (ej: claridad, coherencia, evidencia, estructura)",
            },
            "description": "Template para análisis crítico estructurado con recomendaciones.",
            "example": "Analiza esta propuesta de negocio evaluando viabilidad, riesgos y oportunidades de mercado.",
            "use_case": "analyze",
        },
        "code": {
            "template": (
                "Eres un ingeniero de software senior con amplia experiencia.\n\n"
                "## Tarea\n"
                "Implementa la siguiente funcionalidad:\n\n"
                "**Descripción:** {{DESCRIPTION}}\n"
                "**Lenguaje/Framework:** {{LANGUAGE}}\n"
                "**Versión:** {{VERSION}}\n\n"
                "## Requisitos técnicos\n"
                "{{REQUIREMENTS}}\n\n"
                "## Restricciones\n"
                "{{CONSTRAINTS}}\n\n"
                "## Formato de salida\n"
                "1. **Código:** Implementación completa y funcional con comentarios\n"
                "2. **Explicación:** Descripción de las decisiones de diseño clave\n"
                "3. **Uso:** Ejemplo de cómo usar el código\n"
                "4. **Testing:** Al menos 2-3 casos de prueba sugeridos"
            ),
            "placeholders": {
                "{{DESCRIPTION}}": "Descripción detallada de la funcionalidad a implementar",
                "{{LANGUAGE}}": "Lenguaje de programación y/o framework",
                "{{VERSION}}": "Versión del lenguaje/framework (ej: Python 3.11, Node 20)",
                "{{REQUIREMENTS}}": "Requisitos técnicos (ej: rendimiento, seguridad, escalabilidad)",
                "{{CONSTRAINTS}}": "Restricciones (ej: no usar librerías externas, compatible con Python 3.8+)",
            },
            "description": "Template para solicitudes de implementación de código con contexto completo.",
            "example": "Implementa una función Python 3.11 que calcule el hash SHA-256 de archivos grandes de forma eficiente.",
            "use_case": "code",
        },
        "qa": {
            "template": (
                "Eres un experto en garantía de calidad y pruebas de software.\n\n"
                "## Contexto\n"
                "{{CONTEXT}}\n\n"
                "## Pregunta\n"
                "{{QUESTION}}\n\n"
                "## Instrucciones\n"
                "- Responde ÚNICAMENTE basándote en el contexto proporcionado\n"
                "- Si la información no está en el contexto, indica: "
                "'Esta información no está disponible en el contexto proporcionado'\n"
                "- Cita textualmente las partes del contexto que respaldan tu respuesta\n"
                "- Si hay ambigüedad, presenta las interpretaciones posibles\n\n"
                "## Formato de salida\n"
                "**Respuesta:** [respuesta directa a la pregunta]\n\n"
                "**Evidencia del contexto:**\n"
                "> [cita textual relevante]\n\n"
                "**Confianza:** [alta/media/baja] — [razón]"
            ),
            "placeholders": {
                "{{CONTEXT}}": "El documento, texto o información de referencia",
                "{{QUESTION}}": "La pregunta específica a responder",
            },
            "description": "Template para Q&A basado en contexto (RAG-ready).",
            "example": "¿Cuál es el plazo de entrega según el contrato? [contexto: texto del contrato]",
            "use_case": "qa",
        },
    }

    use_case_lower = use_case.lower().strip()
    if use_case_lower not in templates:
        available = ", ".join(sorted(templates.keys()))
        return {
            "error": f"Caso de uso '{use_case}' no encontrado.",
            "available_use_cases": available,
            "template": None,
        }

    return templates[use_case_lower]
