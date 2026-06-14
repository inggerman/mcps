"""Tests para mcp-llm-router tools."""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_llm_router.tools.router_tools import (
    estimate_task_complexity,
    get_routing_config,
    get_routing_history,
    record_routing_decision,
    route_task,
)
from mcp_shared.errors import ValidationError

# ---------------------------------------------------------------------------
# Tests de complejidad
# ---------------------------------------------------------------------------


def test_estimate_complexity_simple() -> None:
    result = estimate_task_complexity("Hola, ¿cómo estás?")
    assert result["complexity_score"] <= 3
    assert result["complexity_label"] == "simple"
    assert result["estimated_tokens"] > 0


def test_estimate_complexity_code_task() -> None:
    result = estimate_task_complexity(
        "Implementa una función Python que lea un archivo CSV y retorne un DataFrame con pandas."
    )
    assert result["task_type"] == "code"
    assert result["complexity_score"] >= 1


def test_estimate_complexity_long_prompt() -> None:
    long_prompt = "Analiza este sistema de microservicios. " * 500  # ~4000 palabras
    result = estimate_task_complexity(long_prompt)
    assert result["complexity_score"] >= 6
    assert result["estimated_tokens"] > 5000


def test_estimate_complexity_invalid() -> None:
    with pytest.raises(ValidationError):
        estimate_task_complexity("x")


def test_estimate_complexity_architecture() -> None:
    result = estimate_task_complexity(
        "Diseña la arquitectura de un sistema de microservicios con múltiples servicios "
        "y decisión estratégica sobre el plan de migración de monolito."
    )
    assert result["complexity_score"] >= 4


# ---------------------------------------------------------------------------
# Tests de ruteo
# ---------------------------------------------------------------------------


def test_route_simple_task_to_local() -> None:
    result = route_task(
        prompt="Formatea este JSON",
        complexity_threshold=6,
        max_local_tokens=6000,
        privacy_mode=False,
        model_fast="qwen3-8b",
        model_code="devstral-small-2507",
        model_reason="deepseek-r1-0528",
        model_large_context="qwen2.5-14b",
        cloud_model="claude-sonnet-4-5",
        cloud_provider="anthropic",
    )
    assert result["destination"] == "local"
    assert result["model"] == "qwen3-8b"
    assert result["local_model_role"] == "fast"


def test_route_code_task_to_devstral() -> None:
    result = route_task(
        prompt="Implementa una clase Python con métodos para leer y escribir archivos JSON.",
        complexity_threshold=6,
        max_local_tokens=6000,
        privacy_mode=False,
        model_fast="qwen3-8b",
        model_code="devstral-small-2507",
        model_reason="deepseek-r1-0528",
        model_large_context="qwen2.5-14b",
        cloud_model="claude-sonnet-4-5",
        cloud_provider="anthropic",
    )
    assert result["destination"] == "local"
    assert result["task_type"] == "code"
    assert result["model"] == "devstral-small-2507"
    assert result["local_model_role"] == "code"


def test_route_complex_architecture_to_cloud() -> None:
    complex_prompt = (
        "Diseña la arquitectura completa de un sistema de microservicios con múltiples servicios, "
        "decisión estratégica sobre trade-offs, plan de migración, análisis de seguridad "
        "y diseño de sistema distribuido con consistencia eventual. " * 3
    )
    result = route_task(
        prompt=complex_prompt,
        complexity_threshold=4,
        max_local_tokens=6000,
        privacy_mode=False,
        model_fast="qwen3-8b",
        model_code="devstral-small-2507",
        model_reason="deepseek-r1-0528",
        model_large_context="qwen2.5-14b",
        cloud_model="claude-sonnet-4-5",
        cloud_provider="anthropic",
    )
    assert result["destination"] == "cloud"
    assert result["model"] == "claude-sonnet-4-5"


def test_route_privacy_mode_forces_local() -> None:
    complex_prompt = "arquitectura microservicios sistema decisión estratégica " * 20
    result = route_task(
        prompt=complex_prompt,
        complexity_threshold=3,  # umbral bajo
        max_local_tokens=100,  # límite muy bajo
        privacy_mode=True,  # forzar local
        model_fast="qwen3-8b",
        model_code="devstral-small-2507",
        model_reason="deepseek-r1-0528",
        model_large_context="qwen2.5-14b",
        cloud_model="claude-sonnet-4-5",
        cloud_provider="anthropic",
    )
    assert result["destination"] == "local"


def test_route_force_local() -> None:
    result = route_task(
        prompt="Tarea cualquiera " * 100,
        force_local=True,
        complexity_threshold=1,  # umbral muy bajo (iría a nube)
        max_local_tokens=6000,
        privacy_mode=False,
        model_fast="qwen3-8b",
        model_code="devstral-small-2507",
        model_reason="deepseek-r1-0528",
        model_large_context="qwen2.5-14b",
        cloud_model="claude-sonnet-4-5",
        cloud_provider="anthropic",
    )
    assert result["destination"] == "local"


def test_route_force_cloud() -> None:
    result = route_task(
        prompt="Hola",
        force_cloud=True,
        complexity_threshold=10,
        max_local_tokens=1000000,
        privacy_mode=False,
        model_fast="qwen3-8b",
        model_code="devstral-small-2507",
        model_reason="deepseek-r1-0528",
        model_large_context="qwen2.5-14b",
        cloud_model="claude-sonnet-4-5",
        cloud_provider="anthropic",
    )
    assert result["destination"] == "cloud"


def test_route_force_conflict() -> None:
    with pytest.raises(ValidationError):
        route_task(
            prompt="Hola",
            force_local=True,
            force_cloud=True,
            complexity_threshold=6,
            max_local_tokens=6000,
            privacy_mode=False,
            model_fast="qwen3-8b",
            model_code="devstral-small-2507",
            model_reason="deepseek-r1-0528",
            model_large_context="qwen2.5-14b",
            cloud_model="claude-sonnet-4-5",
            cloud_provider="anthropic",
        )


def test_route_large_context_to_qwen_large() -> None:
    # Prompt que excede max_local_tokens con modelo de contexto largo
    long_prompt = "Analiza este código: " + "print('hello')\n" * 3000
    result = route_task(
        prompt=long_prompt,
        complexity_threshold=9,  # umbral muy alto para forzar local
        max_local_tokens=1_000_000,  # límite alto para permitir local
        privacy_mode=True,
        model_fast="qwen3-8b",
        model_code="devstral-small-2507",
        model_reason="deepseek-r1-0528",
        model_large_context="qwen2.5-14b",
        cloud_model="claude-sonnet-4-5",
        cloud_provider="anthropic",
    )
    assert result["destination"] == "local"
    assert result["task_type"] == "large_context"
    assert result["model"] == "qwen2.5-14b"


def test_route_invalid_prompt() -> None:
    with pytest.raises(ValidationError):
        route_task(
            prompt="",
            complexity_threshold=6,
            max_local_tokens=6000,
            privacy_mode=False,
            model_fast="qwen3-8b",
            model_code="devstral-small-2507",
            model_reason="deepseek-r1-0528",
            model_large_context="qwen2.5-14b",
            cloud_model="claude-sonnet-4-5",
            cloud_provider="anthropic",
        )


# ---------------------------------------------------------------------------
# Tests de configuración
# ---------------------------------------------------------------------------


def test_get_routing_config() -> None:
    config = get_routing_config(
        complexity_threshold=6,
        max_local_tokens=6000,
        privacy_mode=False,
        model_fast="qwen3-8b",
        model_code="devstral-small-2507",
        model_reason="deepseek-r1-0528",
        model_large_context="qwen2.5-14b",
        cloud_model="claude-sonnet-4-5",
        cloud_provider="anthropic",
        lmstudio_base_url="http://localhost:1234/v1",
    )
    assert config["rules"]["complexity_threshold"] == 6
    assert config["local_models"]["code"]["name"] == "devstral-small-2507"
    assert config["cloud"]["model"] == "claude-sonnet-4-5"


# ---------------------------------------------------------------------------
# Tests de historial
# ---------------------------------------------------------------------------


def test_routing_history(tmp_path: Path) -> None:
    history_path = tmp_path / "routing_history.json"

    decision = {
        "destination": "local",
        "model": "qwen3-8b",
        "task_type": "simple",
        "complexity_score": 2,
        "estimated_tokens": 50,
    }
    record_routing_decision(history_path, "Formatea este JSON", decision, max_entries=100)
    record_routing_decision(history_path, "Analiza este código", decision, max_entries=100)

    history = get_routing_history(history_path, limit=10)
    assert len(history) == 2
    assert history[0]["destination"] == "local"


def test_routing_history_rotation(tmp_path: Path) -> None:
    history_path = tmp_path / "routing_history.json"
    decision = {
        "destination": "local",
        "model": "qwen3-8b",
        "task_type": "simple",
        "complexity_score": 1,
        "estimated_tokens": 10,
    }
    # Insertar más entradas que el límite
    for i in range(10):
        record_routing_decision(history_path, f"Prompt {i}", decision, max_entries=5)
    history = get_routing_history(history_path, limit=100)
    assert len(history) == 5  # rotación aplicada


def test_routing_history_invalid_limit(tmp_path: Path) -> None:
    history_path = tmp_path / "routing_history.json"
    with pytest.raises(ValidationError):
        get_routing_history(history_path, limit=0)
