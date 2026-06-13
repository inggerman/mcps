"""
Módulo de análisis de prompts para LLMs.

Implementa análisis heurístico real sin llamadas a modelos externos:
- Conteo de tokens y palabras
- Detección de idioma
- Clasificación del tipo de prompt
- Puntuación de claridad
- Detección de problemas y fortalezas
- Sugerencias de mejora
"""

from __future__ import annotations

import re
from typing import Any

# langdetect puede fallar con textos muy cortos; lo manejamos con try/except
try:
    from langdetect import LangDetectException
    from langdetect import detect as _detect_lang

    def _safe_detect(text: str) -> str:
        try:
            return _detect_lang(text[:500])
        except LangDetectException:
            return "unknown"

except ImportError:
    LangDetectException = Exception  # type: ignore[assignment,misc]

    def _safe_detect(text: str) -> str:  # type: ignore[misc]
        return "unknown"


# ---------------------------------------------------------------------------
# Constantes de análisis
# ---------------------------------------------------------------------------

# Palabras de vaguedad en español e inglés
_VAGUE_WORDS_ES: frozenset[str] = frozenset(
    {
        "algo",
        "algunas",
        "algunos",
        "tal vez",
        "quizás",
        "quizas",
        "posiblemente",
        "probablemente",
        "más o menos",
        "aproximadamente",
        "etc",
        "etcétera",
        "entre otras",
        "entre otros",
        "cosas",
        "temas",
        "aspectos",
        "elementos",
        "características",
    }
)

_VAGUE_WORDS_EN: frozenset[str] = frozenset(
    {
        "something",
        "somehow",
        "maybe",
        "perhaps",
        "possibly",
        "probably",
        "around",
        "approximately",
        "etc",
        "etcetera",
        "things",
        "stuff",
        "aspects",
        "elements",
        "features",
        "various",
        "several",
        "some kind of",
        "sort of",
        "kind of",
    }
)

# Indicadores de rol/persona
_ROLE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(eres|actúa como|actua como|eres un|eres una)\b", re.IGNORECASE),
    re.compile(r"\b(you are|act as|you are a|you are an|behave as)\b", re.IGNORECASE),
    re.compile(r"\b(como (experto|especialista|profesional|consultor))\b", re.IGNORECASE),
    re.compile(r"\b(as (an? )?(expert|specialist|professional|consultant))\b", re.IGNORECASE),
]

# Indicadores de ejemplos few-shot
_EXAMPLE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(por ejemplo|ejemplo:|p\.ej\.|p\.e\.)\b", re.IGNORECASE),
    re.compile(r"\b(for example|e\.g\.|e\.g|for instance|such as)\b", re.IGNORECASE),
    re.compile(r"(input:|output:|entrada:|salida:)", re.IGNORECASE),
    re.compile(r"```[\s\S]*?```"),  # Bloque de código como ejemplo
]

# Indicadores de formato de salida
_FORMAT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(formato|format|responde en|respond in|output format)\b", re.IGNORECASE),
    re.compile(r"\b(JSON|XML|CSV|markdown|tabla|table|lista|list|bullet)\b", re.IGNORECASE),
    re.compile(r"\b(en (formato|forma de)|as a (list|table|json|markdown))\b", re.IGNORECASE),
]

# Palabras que indican análisis/razonamiento
_ANALYTICAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(analiza|analizar|analizar|analyze|analysis)\b", re.IGNORECASE),
    re.compile(r"\b(compara|comparar|compare|comparison)\b", re.IGNORECASE),
    re.compile(r"\b(evalúa|evaluar|evaluate|evaluation)\b", re.IGNORECASE),
    re.compile(r"\b(calcula|calcular|calculate|computation)\b", re.IGNORECASE),
    re.compile(r"\b(explica|explicar|explain|explanation)\b", re.IGNORECASE),
    re.compile(r"\b(razona|razonar|reason|reasoning)\b", re.IGNORECASE),
    re.compile(r"\b(deduce|deducir|deduce|infer|inference)\b", re.IGNORECASE),
]

# Palabras creativas
_CREATIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(escribe|escribir|redacta|redactar|crea|crear)\b", re.IGNORECASE),
    re.compile(r"\b(write|create|compose|generate|draft|craft)\b", re.IGNORECASE),
    re.compile(r"\b(historia|cuento|poema|canción|guion|novela)\b", re.IGNORECASE),
    re.compile(r"\b(story|poem|song|script|novel|fiction)\b", re.IGNORECASE),
    re.compile(r"\b(imagina|imagine|inventa|invent)\b", re.IGNORECASE),
]

# Palabras de instrucción directa
_INSTRUCTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(haz|hacer|realiza|realizar|ejecuta|ejecutar)\b", re.IGNORECASE),
    re.compile(r"\b(do|make|perform|execute|implement|build)\b", re.IGNORECASE),
    re.compile(r"\b(resume|resumir|traduce|traducir|clasifica|clasificar)\b", re.IGNORECASE),
    re.compile(r"\b(summarize|translate|classify|convert|transform)\b", re.IGNORECASE),
    re.compile(r"\b(extrae|extraer|extract|parse|find|list)\b", re.IGNORECASE),
]

# Patrones de pregunta
_QUESTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(qué|cuál|cómo|cuándo|dónde|por qué|quién|cuántos?)\b", re.IGNORECASE),
    re.compile(r"^(what|which|how|when|where|why|who|whom|whose|how many)\b", re.IGNORECASE),
    re.compile(r"\?$"),
]

# Palabras de contradicción
_CONTRADICTION_PAIRS: list[tuple[str, str]] = [
    ("corto", "largo"),
    ("breve", "detallado"),
    ("simple", "complejo"),
    ("formal", "informal"),
    ("técnico", "sencillo"),
    ("short", "long"),
    ("brief", "detailed"),
    ("simple", "complex"),
    ("formal", "informal"),
    ("technical", "simple"),
]


# ---------------------------------------------------------------------------
# Funciones principales
# ---------------------------------------------------------------------------


def _count_words(text: str) -> int:
    """Cuenta las palabras de un texto."""
    return len(text.split())


def _estimate_tokens(text: str) -> int:
    """Estima tokens basado en la heurística de 4 chars/token."""
    return max(1, len(text) // 4)


def _has_role(text: str) -> bool:
    """Detecta si el prompt define un rol o persona."""
    return any(p.search(text) for p in _ROLE_PATTERNS)


def _has_examples(text: str) -> bool:
    """Detecta si el prompt incluye ejemplos few-shot."""
    return any(p.search(text) for p in _EXAMPLE_PATTERNS)


def _has_format_spec(text: str) -> bool:
    """Detecta si el prompt especifica el formato de salida."""
    return any(p.search(text) for p in _FORMAT_PATTERNS)


def _is_question(text: str) -> bool:
    """Detecta si el prompt es principalmente una pregunta."""
    first_line = text.strip().split("\n")[0].strip()
    return any(p.search(first_line) for p in _QUESTION_PATTERNS)


def _is_closed_question(text: str) -> bool:
    """Detecta si la pregunta es cerrada (respuesta sí/no)."""
    if not _is_question(text):
        return False
    closed_starters_es = re.compile(
        r"^(¿?)(es|son|está|están|hay|tiene|tienen|puedes|puede|debería|debo)\b",
        re.IGNORECASE,
    )
    closed_starters_en = re.compile(
        r"^(is|are|was|were|can|could|should|would|do|does|did|has|have|had)\b",
        re.IGNORECASE,
    )
    first_word = text.strip().lstrip("¿").split()[0] if text.strip() else ""
    return bool(closed_starters_es.match(text.strip()) or closed_starters_en.match(first_word))


def _detect_vague_words(text: str) -> list[str]:
    """Detecta palabras o frases vagas en el texto."""
    text_lower = text.lower()
    found: list[str] = []
    for word in _VAGUE_WORDS_ES | _VAGUE_WORDS_EN:
        if word in text_lower:
            found.append(word)
    return found


def _detect_contradictions(text: str) -> list[tuple[str, str]]:
    """Detecta pares de palabras contradictorias en el texto."""
    text_lower = text.lower()
    found: list[tuple[str, str]] = []
    for w1, w2 in _CONTRADICTION_PAIRS:
        if w1 in text_lower and w2 in text_lower:
            found.append((w1, w2))
    return found


def classify_prompt(prompt: str) -> dict[str, Any]:
    """
    Clasifica el tipo de prompt con una puntuación de confianza.

    Returns:
        dict con:
            - type: "instruction" | "question" | "creative" | "analytical" | "conversational"
            - confidence: float 0.0–1.0
            - scores: dict con puntuación por categoría
    """
    scores: dict[str, float] = {
        "instruction": 0.0,
        "question": 0.0,
        "creative": 0.0,
        "analytical": 0.0,
        "conversational": 0.0,
    }

    # Question detection
    if _is_question(prompt):
        scores["question"] += 0.6
    if prompt.count("?") >= 2:
        scores["question"] += 0.2

    # Analytical detection
    analytical_hits = sum(1 for p in _ANALYTICAL_PATTERNS if p.search(prompt))
    scores["analytical"] += min(analytical_hits * 0.25, 0.8)

    # Creative detection
    creative_hits = sum(1 for p in _CREATIVE_PATTERNS if p.search(prompt))
    scores["creative"] += min(creative_hits * 0.3, 0.8)

    # Instruction detection
    instruction_hits = sum(1 for p in _INSTRUCTION_PATTERNS if p.search(prompt))
    scores["instruction"] += min(instruction_hits * 0.25, 0.8)
    # Imperative mood heuristic: starts with a verb
    first_word = prompt.strip().split()[0].lower() if prompt.strip() else ""
    imperative_words = {
        "resume",
        "traduce",
        "clasifica",
        "extrae",
        "escribe",
        "crea",
        "genera",
        "summarize",
        "translate",
        "classify",
        "extract",
        "write",
        "create",
        "generate",
        "list",
        "describe",
        "explain",
        "analyze",
        "compare",
        "find",
        "fix",
        "debug",
    }
    if first_word in imperative_words:
        scores["instruction"] += 0.3

    # Conversational: short, personal, informal
    word_count = _count_words(prompt)
    if word_count < 15 and not _is_question(prompt) and scores["instruction"] < 0.3:
        scores["conversational"] += 0.4
    informal_markers = re.compile(
        r"\b(oye|hey|hola|hello|hi|gracias|thanks|por favor|please)\b", re.IGNORECASE
    )
    if informal_markers.search(prompt):
        scores["conversational"] += 0.3

    # Boost analytical if "step by step" or similar
    if re.search(r"\b(step by step|paso a paso|think|razona)\b", prompt, re.IGNORECASE):
        scores["analytical"] += 0.2

    # Determine winner
    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]

    # Fallback: if no strong signal, it's an instruction
    if best_score < 0.2:
        best_type = "instruction"
        best_score = 0.5

    # Normalize confidence to [0, 1]
    confidence = min(best_score, 1.0)

    return {
        "type": best_type,
        "confidence": round(confidence, 2),
        "scores": {k: round(v, 2) for k, v in scores.items()},
    }


def _compute_clarity_score(
    prompt: str,
    word_count: int,
    vague_words: list[str],
    has_role: bool,
    has_examples: bool,
    has_format: bool,
    contradictions: list[tuple[str, str]],
    prompt_type: str,
) -> float:
    """
    Calcula la puntuación de claridad del prompt en escala 0–10.

    Criterios positivos:
    - Longitud adecuada (20–500 palabras)
    - Tiene rol/persona definido
    - Tiene ejemplos few-shot
    - Tiene formato de salida especificado
    - Vocabulario específico y técnico

    Criterios negativos:
    - Palabras vagas
    - Muy corto (<10 palabras) o muy largo (>1000 palabras)
    - Instrucciones contradictorias
    """
    score = 5.0  # Base score

    # Longitud
    if word_count < 10:
        score -= 2.5
    elif word_count < 20:
        score -= 1.0
    elif 20 <= word_count <= 200:
        score += 1.5
    elif 200 < word_count <= 500:
        score += 0.5
    elif word_count > 1000:
        score -= 0.5

    # Penalización por palabras vagas
    score -= min(len(vague_words) * 0.4, 2.0)

    # Bonificaciones por buenas prácticas
    if has_role:
        score += 0.8
    if has_examples:
        score += 1.2
    if has_format:
        score += 0.8

    # Penalización por contradicciones
    score -= len(contradictions) * 1.0

    # Bonus por especificidad: presencia de números o cantidades
    if re.search(r"\b\d+\b", prompt):
        score += 0.3

    # Bonus por estructura (listas, numeración)
    if re.search(r"(\d+\.|[-*•])\s", prompt):
        score += 0.5

    return round(max(0.0, min(10.0, score)), 1)


def analyze_prompt(
    prompt: str,
    target_model: str | None = None,
) -> dict[str, Any]:
    """
    Analiza un prompt de LLM de forma exhaustiva usando heurísticas reales.

    Args:
        prompt: El texto del prompt a analizar.
        target_model: Modelo objetivo opcional (gpt-4, claude-3-5, etc.).

    Returns:
        dict con token_count, word_count, language, prompt_type, clarity_score,
        issues, strengths y suggestions.
    """
    if not prompt or not prompt.strip():
        return {
            "token_count": 0,
            "word_count": 0,
            "language": "unknown",
            "prompt_type": "unknown",
            "clarity_score": 0.0,
            "issues": [{"severity": "error", "message": "El prompt está vacío."}],
            "strengths": [],
            "suggestions": ["Escribe el contenido del prompt."],
            "has_role": False,
            "has_examples": False,
            "has_format_spec": False,
            "target_model": target_model,
        }

    # --- Métricas básicas ---
    word_count = _count_words(prompt)
    token_count = _estimate_tokens(prompt)
    language = _safe_detect(prompt)

    # --- Propiedades estructurales ---
    has_role = _has_role(prompt)
    has_examples = _has_examples(prompt)
    has_format = _has_format_spec(prompt)
    is_closed_q = _is_closed_question(prompt)
    vague_words = _detect_vague_words(prompt)
    contradictions = _detect_contradictions(prompt)

    # --- Clasificación ---
    classification = classify_prompt(prompt)
    prompt_type: str = classification["type"]

    # --- Problemas detectados ---
    issues: list[dict[str, Any]] = []

    if word_count < 10:
        issues.append(
            {
                "severity": "critical",
                "code": "TOO_SHORT",
                "message": (
                    f"El prompt es muy corto ({word_count} palabras). "
                    "Los prompts con menos de 10 palabras suelen ser ambiguos."
                ),
            }
        )
    elif word_count < 20:
        issues.append(
            {
                "severity": "warning",
                "code": "SHORT_PROMPT",
                "message": (
                    f"El prompt es corto ({word_count} palabras). Considera añadir más contexto."
                ),
            }
        )

    if vague_words:
        issues.append(
            {
                "severity": "warning",
                "code": "VAGUE_LANGUAGE",
                "message": (
                    f"Lenguaje vago detectado: {', '.join(repr(w) for w in vague_words[:5])}. "
                    "Estos términos pueden llevar a respuestas ambiguas."
                ),
                "affected_words": vague_words,
            }
        )

    if is_closed_q:
        issues.append(
            {
                "severity": "info",
                "code": "CLOSED_QUESTION",
                "message": (
                    "La pregunta parece ser cerrada (respuesta sí/no). "
                    "Reformula como pregunta abierta para obtener respuestas más detalladas."
                ),
            }
        )

    if contradictions:
        for w1, w2 in contradictions:
            issues.append(
                {
                    "severity": "warning",
                    "code": "CONTRADICTION",
                    "message": (
                        f"Posible contradicción: '{w1}' y '{w2}' aparecen juntos. "
                        "Verifica que las instrucciones sean coherentes."
                    ),
                }
            )

    if not has_role and prompt_type in {"analytical", "instruction"} and word_count > 30:
        issues.append(
            {
                "severity": "info",
                "code": "NO_ROLE",
                "message": (
                    "No se detectó definición de rol o persona. "
                    "Añadir contexto de rol mejora la precisión de las respuestas."
                ),
            }
        )

    if not has_format and word_count > 50:
        issues.append(
            {
                "severity": "info",
                "code": "NO_FORMAT",
                "message": (
                    "No se especificó el formato de salida. "
                    "Define el formato esperado (JSON, lista, párrafo, etc.)."
                ),
            }
        )

    if word_count > 2000:
        issues.append(
            {
                "severity": "warning",
                "code": "TOO_LONG",
                "message": (
                    f"El prompt es muy largo ({word_count} palabras ≈ {token_count} tokens). "
                    "Prompts excesivamente largos pueden reducir la calidad de la respuesta."
                ),
            }
        )

    # Detectar si hay múltiples tareas sin separación clara
    task_connectors = re.findall(
        r"\b(y también|además|también|and also|also|furthermore|moreover)\b",
        prompt,
        re.IGNORECASE,
    )
    if len(task_connectors) >= 3:
        issues.append(
            {
                "severity": "info",
                "code": "MULTIPLE_TASKS",
                "message": (
                    "El prompt parece contener múltiples tareas encadenadas. "
                    "Considera descomponerlo en prompts separados o numerados."
                ),
            }
        )

    # --- Fortalezas detectadas ---
    strengths: list[str] = []

    if has_role:
        strengths.append("✓ Define un rol o persona específica.")
    if has_examples:
        strengths.append("✓ Incluye ejemplos (few-shot prompting).")
    if has_format:
        strengths.append("✓ Especifica el formato de salida esperado.")
    if 20 <= word_count <= 500:
        strengths.append(f"✓ Longitud adecuada ({word_count} palabras).")
    if not vague_words:
        strengths.append("✓ Lenguaje específico y preciso.")
    if re.search(r"\b\d+\b", prompt):
        strengths.append("✓ Incluye datos cuantitativos o referencias numéricas.")
    if re.search(r"(\d+\.|[-*•])\s", prompt):
        strengths.append("✓ Usa estructura de lista o pasos numerados.")
    if re.search(r"\b(paso a paso|step by step)\b", prompt, re.IGNORECASE):
        strengths.append("✓ Solicita razonamiento paso a paso (chain-of-thought).")
    if not contradictions:
        strengths.append("✓ Las instrucciones son coherentes y consistentes.")

    if not strengths:
        strengths.append("El prompt tiene estructura básica reconocible.")

    # --- Sugerencias de mejora ---
    suggestions: list[str] = []

    if word_count < 20:
        suggestions.append(
            "Añade más contexto: describe el objetivo, la audiencia o las restricciones."
        )
    if vague_words:
        suggestions.append(
            "Reemplaza términos vagos por especificaciones concretas. "
            "En lugar de 'algo', especifica exactamente qué necesitas."
        )
    if is_closed_q:
        suggestions.append(
            "Convierte la pregunta cerrada en abierta. "
            "Ej: '¿Es bueno X?' → '¿Cuáles son las ventajas y desventajas de X?'"
        )
    if not has_role and word_count > 30:
        suggestions.append("Agrega un rol: 'Eres un experto en [dominio]. Tu tarea es...'")
    if not has_format and word_count > 50:
        suggestions.append(
            "Especifica el formato de salida: 'Responde en formato JSON', "
            "'Lista los puntos clave como bullets', etc."
        )
    if not has_examples and prompt_type in {"analytical", "instruction"} and word_count > 100:
        suggestions.append(
            "Añade 1-3 ejemplos input/output para guiar al modelo (few-shot prompting)."
        )
    if prompt_type == "analytical" and not re.search(
        r"\b(paso a paso|step by step)\b", prompt, re.IGNORECASE
    ):
        suggestions.append(
            "Para tareas analíticas, añade 'Razona paso a paso' o 'Think step by step'."
        )
    if contradictions:
        suggestions.append(
            "Revisa y elimina instrucciones contradictorias para evitar respuestas confusas."
        )

    # --- Puntuación de claridad ---
    clarity_score = _compute_clarity_score(
        prompt=prompt,
        word_count=word_count,
        vague_words=vague_words,
        has_role=has_role,
        has_examples=has_examples,
        has_format=has_format,
        contradictions=contradictions,
        prompt_type=prompt_type,
    )

    return {
        "token_count": token_count,
        "word_count": word_count,
        "language": language,
        "prompt_type": prompt_type,
        "type_confidence": classification["confidence"],
        "clarity_score": clarity_score,
        "issues": issues,
        "strengths": strengths,
        "suggestions": suggestions,
        "has_role": has_role,
        "has_examples": has_examples,
        "has_format_spec": has_format,
        "is_closed_question": is_closed_q,
        "vague_words_found": vague_words,
        "target_model": target_model,
    }
