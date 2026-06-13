from __future__ import annotations

from mcp_prompt_engineer.tools.analyzer import analyze_prompt, classify_prompt
from mcp_prompt_engineer.tools.improver import (
    create_system_prompt,
    estimate_tokens,
    generate_variations,
    get_prompt_template,
)


def test_analyze_prompt_reports_structure() -> None:
    result = analyze_prompt("Actua como experto. Resume el texto en formato JSON.")
    assert result["has_role"] is True
    assert result["has_format_spec"] is True
    assert result["clarity_score"] >= 0


def test_classify_question() -> None:
    result = classify_prompt("What is the capital of Mexico?")
    assert result["type"] in {"question", "closed_question"}


def test_estimate_tokens() -> None:
    result = estimate_tokens("hello world", "gpt-4o")
    assert result["text_length"] == 11
    assert result["tokens"]["gpt-4o"] > 0


def test_generate_variations() -> None:
    result = generate_variations("Resume este texto", 3)
    assert len(result) == 3


def test_create_system_prompt() -> None:
    result = create_system_prompt("analista", "equipo financiero")
    assert "analista" in result


def test_get_prompt_template() -> None:
    result = get_prompt_template("summarize")
    assert result["template"]
