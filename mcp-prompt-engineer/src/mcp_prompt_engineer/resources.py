"""Resources de solo lectura para mcp-prompt-engineer.

Expone metadatos, guias, consejos y referencias sobre prompt engineering
como URIs accesibles para el modelo a traves de `@mcp.resource`.
"""

from __future__ import annotations

import json

from mcp_prompt_engineer.config import settings


def prompt_engineer_configuration() -> str:
    """Configuracion actual del servidor prompt-engineer."""
    return json.dumps(
        {
            "server_name": settings.server_name,
            "server_version": settings.server_version,
            "max_prompt_length": settings.max_prompt_length,
            "max_variations": settings.max_variations,
            "default_model": settings.default_model,
        },
        indent=2,
        ensure_ascii=False,
    )


def prompt_types_reference() -> str:
    """Tipos de prompts detectados por el analizador."""
    return (
        "# Tipos de prompts\n\n"
        "| Tipo | Descripcion |\n"
        "|------|-------------|\n"
        "| instruction | Tarea directa o comando |\n"
        "| question | Pregunta abierta |\n"
        "| closed_question | Pregunta de si/no |\n"
        "| few_shot | Prompt con ejemplos |\n"
        "| system | System prompt |\n"
        "| conversation | Conversacional |\n"
        "| creative | Creativo (escritura, ideas) |\n"
        "| code | Codigo o implementacion tecnica |\n"
        "| analytical | Analisis, evaluacion, razonamiento |"
    )


def clarity_scoring_guide() -> str:
    """Guia de puntuacion de claridad (0-10)."""
    return (
        "# Puntuacion de claridad (0-10)\n\n"
        "## Criterios positivos\n"
        "- Longitud adecuada (20-500 palabras): +1.5 / +0.5\n"
        "- Define rol o persona: +0.8\n"
        "- Incluye ejemplos few-shot: +1.2\n"
        "- Especifica formato de salida: +0.8\n"
        "- Incluye datos cuantitativos: +0.3\n"
        "- Usa estructura de lista: +0.5\n\n"
        "## Criterios negativos\n"
        "- Menos de 10 palabras: -2.5\n"
        "- Menos de 20 palabras: -1.0\n"
        "- Palabras vagas (hasta -2.0)\n"
        "- Instrucciones contradictorias: -1.0 c/u\n"
        "- Mas de 1000 palabras: -0.5"
    )


def prompt_engineering_best_practices() -> str:
    """Mejores practicas de prompt engineering."""
    return (
        "# Mejores practicas de prompt engineering\n\n"
        "1. **Define un rol**: 'Eres un experto en...'\n"
        "2. **Sé especifico**: Evita palabras vagas como 'algo', 'cosas'\n"
        "3. **Especifica el formato**: JSON, lista, tabla, parrafo\n"
        "4. **Usa ejemplos**: Few-shot prompting con input/output\n"
        "5. **Anade chain-of-thought**: 'Razona paso a paso'\n"
        "6. **Define restricciones**: Que hacer y que NO hacer\n"
        "7. **Contexto suficiente**: Audiencia, objetivo, tono\n"
        "8. **Longitud adecuada**: 20-500 palabras ideal\n"
        "9. **Estructura**: Usa secciones, listas, numeracion\n"
        "10. **Criterios de exito**: Define cuando la respuesta es buena"
    )


def prompt_issues_reference() -> str:
    """Codigos de problemas detectados por el analizador."""
    return json.dumps(
        {
            "issues": [
                {"code": "TOO_SHORT", "severity": "critical", "description": "Prompt con menos de 10 palabras"},
                {"code": "SHORT_PROMPT", "severity": "warning", "description": "Prompt con menos de 20 palabras"},
                {"code": "VAGUE_LANGUAGE", "severity": "warning", "description": "Lenguaje vago detectado"},
                {"code": "CLOSED_QUESTION", "severity": "info", "description": "Pregunta cerrada si/no"},
                {"code": "CONTRADICTION", "severity": "warning", "description": "Instrucciones contradictorias"},
                {"code": "NO_ROLE", "severity": "info", "description": "Sin definicion de rol"},
                {"code": "NO_FORMAT", "severity": "info", "description": "Sin formato de salida especificado"},
                {"code": "TOO_LONG", "severity": "warning", "description": "Mas de 2000 palabras"},
                {"code": "MULTIPLE_TASKS", "severity": "info", "description": "Multiples tareas encadenadas"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def token_estimation_guide() -> str:
    """Guia de estimacion de tokens."""
    return (
        "# Estimacion de tokens\n\n"
        "## Modelos soportados\n"
        "- GPT-4o / GPT-4-turbo (tiktoken cl100k_base)\n"
        "- GPT-3.5-turbo (tiktoken cl100k_base)\n"
        "- Claude-3.5-sonnet / Claude-3-opus / Claude-3-haiku (heuristica 3.5 chars/token)\n\n"
        "## Ventanas de contexto\n"
        "| Modelo | Contexto |\n"
        "|--------|----------|\n"
        "| GPT-4o | 128k tokens |\n"
        "| GPT-3.5-turbo | 16k tokens |\n"
        "| Claude-3.5-sonnet | 200k tokens |"
    )


def prompt_variation_approaches() -> str:
    """Enfoques de variacion de prompts."""
    return (
        "# Enfoques de variacion\n\n"
        "| Enfoque | Descripcion |\n"
        "|----------|-------------|\n"
        "| role_injection | Anade rol de experto |\n"
        "| chain_of_thought | Razonamiento paso a paso |\n"
        "| structured_output | Plantilla de salida estructurada |\n"
        "| concise | Version condensada |\n"
        "| audience_context | Adapta para audiencia especifica |\n"
        "| examples_requested | Solicita ejemplos concretos |\n"
        "| english_version | Template para version en ingles |\n"
        "| system_prompt_style | Reformateado como system prompt |\n"
        "| success_criteria | Anade criterios de exito |\n"
        "| negative_constraints | Anade restricciones negativas |"
    )


def prompt_templates_catalog() -> str:
    """Catalogo de templates disponibles."""
    return (
        "# Templates disponibles\n\n"
        "| Caso de uso | Descripcion |\n"
        "|-------------|-------------|\n"
        "| summarize | Resumen de textos con formato estructurado |\n"
        "| translate | Traduccion profesional con notas |\n"
        "| classify | Clasificacion con output JSON |\n"
        "| extract | Extraccion de datos con JSON |\n"
        "| generate | Generacion de contenido flexible |\n"
        "| analyze | Analisis critico con recomendaciones |\n"
        "| code | Implementacion de codigo con contexto |\n"
        "| qa | Q&A basado en contexto (RAG-ready) |"
    )


def prompt_engineering_workflow() -> str:
    """Flujo de trabajo de prompt engineering."""
    return (
        "# Flujo de trabajo de prompt engineering\n\n"
        "## 1. Analizar\n"
        "```\n"
        "analyze_prompt(prompt='tu prompt aqui')\n"
        "```\n"
        "Revisa clarity_score, issues y suggestions.\n\n"
        "## 2. Mejorar\n"
        "```\n"
        "improve_prompt(prompt='tu prompt', goal='objetivo')\n"
        "```\n"
        "Revisa los cambios aplicados y el improvement_delta.\n\n"
        "## 3. Generar variaciones\n"
        "```\n"
        "generate_variations(prompt='tu prompt', n=3)\n"
        "```\n"
        "Compara enfoques y elige el mejor.\n\n"
        "## 4. Usar template\n"
        "```\n"
        "get_prompt_template(use_case='analyze')\n"
        "```\n"
        "Reemplaza los placeholders con tus valores."
    )


def prompt_engineering_tips() -> str:
    """Consejos rapidos de prompt engineering."""
    return (
        "# Consejos rapidos\n\n"
        "- Usa `classify_prompt` para entender el tipo antes de mejorar\n"
        "- Usa `estimate_tokens` antes de enviar a un modelo con contexto limitado\n"
        "- Usa `decompose_task` para tareas complejas de multiples pasos\n"
        "- Usa `create_system_prompt` para conversaciones recurrentes\n"
        "- Usa `add_few_shot_examples` para mejorar precision con ejemplos\n"
        "- Combina `improve_prompt` + `generate_variations` para optimizar\n"
        "- Revisa siempre el `clarity_score` antes y despues de mejorar"
    )


def prompt_engineering_error_codes() -> str:
    """Codigos de error del servidor prompt-engineer."""
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion (prompt muy largo, etc.)"},
                {"code": -32603, "description": "Error interno del servidor"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def few_shot_examples_guide() -> str:
    """Guia de few-shot prompting."""
    return (
        "# Few-shot prompting\n\n"
        "El few-shot prompting consiste en incluir ejemplos input/output\n"
        "en el prompt para guiar al modelo hacia el formato y estilo deseados.\n\n"
        "## Estructura\n"
        "```\n"
        "## Ejemplos\n\n"
        "### Ejemplo 1\n"
        "**Entrada:** [input ejemplo]\n"
        "**Salida:** [output esperado]\n\n"
        "### Ejemplo 2\n"
        "**Entrada:** [input ejemplo]\n"
        "**Salida:** [output esperado]\n\n"
        "---\n\n"
        "## Tarea\n"
        "[prompt actual]\n"
        "```\n\n"
        "Usa `add_few_shot_examples` para enriquecer un prompt automaticamente."
    )


def chain_of_thought_guide() -> str:
    """Guia de chain-of-thought prompting."""
    return (
        "# Chain-of-thought prompting\n\n"
        "El chain-of-thought (CoT) consiste en pedir al modelo que razone\n"
        "paso a paso antes de dar la respuesta final.\n\n"
        "## Ejemplos de instrucciones CoT\n"
        "- 'Razona paso a paso antes de responder'\n"
        "- 'Think step by step'\n"
        "- 'Antes de responder, considera: 1) Que informacion necesito, 2) Cual es el enfoque, 3) Cual es la respuesta'\n\n"
        "## Cuando usarlo\n"
        "- Tareas analiticas o de razonamiento\n"
        "- Problemas complejos de multiples pasos\n"
        "- Cuando la precision es mas importante que la velocidad"
    )


def example_analyze_prompt() -> str:
    """Ejemplo de analisis de prompt."""
    return (
        "# Ejemplo: analyze_prompt\n\n"
        "```\n"
        "analyze_prompt(\n"
        "    prompt='Eres un experto en marketing. Escribe un email de ventas.',\n"
        "    target_model='gpt-4o'\n"
        ")\n"
        "```\n"
        "Retorna: token_count, word_count, language, prompt_type, clarity_score, "
        "issues, strengths, suggestions, has_role, has_examples, has_format_spec."
    )


def example_improve_prompt() -> str:
    """Ejemplo de mejora de prompt."""
    return (
        "# Ejemplo: improve_prompt\n\n"
        "```\n"
        "improve_prompt(\n"
        "    prompt='escribe un resumen del articulo',\n"
        "    goal='Resumen ejecutivo para directores',\n"
        "    style='concise'\n"
        ")\n"
        "```\n"
        "Retorna: original, improved, changes, score_before, score_after, improvement_delta."
    )
