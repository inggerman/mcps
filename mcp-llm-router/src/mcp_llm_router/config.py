"""
Configuración de mcp-llm-router.

Controla las reglas de ruteo entre modelos locales (LM Studio)
y modelos en la nube. Variables de entorno con prefijo ROUTER_
(ej: ROUTER_COMPLEXITY_THRESHOLD=5).
"""

from __future__ import annotations

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class RouterSettings(BaseMcpSettings):
    """
    Configuración del servidor MCP LLM Router.

    Variables de entorno soportadas (prefijo ROUTER_):
        ROUTER_LMSTUDIO_BASE_URL: URL base de la API de LM Studio.
        ROUTER_COMPLEXITY_THRESHOLD: Score 1-10 para decidir local vs nube.
        ROUTER_MAX_LOCAL_TOKENS: Límite de tokens para ruteo local.
        ROUTER_PRIVACY_MODE: Si true, nunca envía datos a la nube.
        ROUTER_HISTORY_MAX: Máximo de entradas en el historial de ruteo.

    Modelos locales disponibles (configuración de tus modelos LM Studio):
        ROUTER_MODEL_FAST: Modelo rápido para tareas simples (Qwen3 8B).
        ROUTER_MODEL_CODE: Modelo especialista en código (Devstral Small).
        ROUTER_MODEL_REASON: Modelo de razonamiento (Deepseek R1).
        ROUTER_MODEL_LARGE: Modelo de contexto largo (Qwen2.5 14B).

    Nube:
        ROUTER_CLOUD_PROVIDER: Proveedor de nube (anthropic / openai).
        ROUTER_CLOUD_MODEL: Modelo de nube a usar.
        ROUTER_CLOUD_API_KEY: API key del proveedor de nube.

    Variables heredadas (sin prefijo):
        LOG_LEVEL, LOG_FORMAT, MCP_HOST, MCP_PORT, MCP_TRANSPORT
    """

    model_config = SettingsConfigDict(
        env_prefix="ROUTER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # LM Studio
    lmstudio_base_url: str = Field(
        default="http://localhost:1234/v1",
        description=(
            "URL base de la API de LM Studio (compatible con OpenAI). "
            "Variable de entorno: ROUTER_LMSTUDIO_BASE_URL."
        ),
    )

    # Reglas de ruteo
    complexity_threshold: int = Field(
        default=6,
        ge=1,
        le=10,
        description=(
            "Umbral de complejidad (1-10) por encima del cual se usa la nube. "
            "Tareas con score >= threshold van a la nube. "
            "Variable de entorno: ROUTER_COMPLEXITY_THRESHOLD."
        ),
    )

    max_local_tokens: int = Field(
        default=6000,
        ge=512,
        le=1_000_000,
        description=(
            "Número máximo de tokens estimados para usar modelo local. "
            "Si la tarea requiere más tokens, se ruta a la nube. "
            "Variable de entorno: ROUTER_MAX_LOCAL_TOKENS."
        ),
    )

    privacy_mode: bool = Field(
        default=False,
        description=(
            "Si es true, fuerza el uso de modelos locales siempre. "
            "Nunca envía datos a la nube, independientemente de la complejidad. "
            "Variable de entorno: ROUTER_PRIVACY_MODE."
        ),
    )

    history_max: int = Field(
        default=500,
        ge=10,
        le=10000,
        description=(
            "Número máximo de entradas a conservar en el historial de ruteo. "
            "Variable de entorno: ROUTER_HISTORY_MAX."
        ),
    )

    # Modelos locales — tus modelos en LM Studio
    model_fast: str = Field(
        default="qwen3-8b",
        description=(
            "Modelo local rápido para tareas simples (< complexity 3, < 2K tokens). "
            "Ejemplo: qwen3-8b. Variable de entorno: ROUTER_MODEL_FAST."
        ),
    )

    model_code: str = Field(
        default="devstral-small-2507",
        description=(
            "Modelo local especializado en código. Usado para generación, "
            "review y refactoring de código. "
            "Variable de entorno: ROUTER_MODEL_CODE."
        ),
    )

    model_reason: str = Field(
        default="deepseek-r1-0528-qwen3-8b",
        description=(
            "Modelo local con capacidades de razonamiento (chain-of-thought). "
            "Usado para análisis complejos que no requieren la nube. "
            "Variable de entorno: ROUTER_MODEL_REASON."
        ),
    )

    model_large_context: str = Field(
        default="qwen2.5-14b-instruct-1m",
        description=(
            "Modelo local con ventana de contexto grande (1M tokens). "
            "Usado para tareas con mucho contexto que pueden hacerse localmente. "
            "Variable de entorno: ROUTER_MODEL_LARGE."
        ),
    )

    # Nube
    cloud_provider: str = Field(
        default="anthropic",
        description=(
            "Proveedor de modelos en la nube: 'anthropic' o 'openai'. "
            "Variable de entorno: ROUTER_CLOUD_PROVIDER."
        ),
    )

    cloud_model: str = Field(
        default="claude-sonnet-4-5",
        description=(
            "Nombre del modelo de nube a usar para tareas complejas. "
            "Variable de entorno: ROUTER_CLOUD_MODEL."
        ),
    )

    cloud_api_key: str = Field(
        default="",
        description=(
            "API key del proveedor de nube. Dejar vacío si solo se usa local. "
            "Variable de entorno: ROUTER_CLOUD_API_KEY."
        ),
    )

    # Timeouts
    lmstudio_timeout_seconds: int = Field(
        default=120,
        ge=5,
        le=600,
        description="Timeout en segundos para llamadas a LM Studio. Variable: ROUTER_LMSTUDIO_TIMEOUT_SECONDS.",
    )

    cloud_timeout_seconds: int = Field(
        default=60,
        ge=5,
        le=300,
        description="Timeout en segundos para llamadas a la nube. Variable: ROUTER_CLOUD_TIMEOUT_SECONDS.",
    )

    def to_log_context(self) -> dict:
        """Extiende el contexto de log base con parámetros del router."""
        base = super().to_log_context()
        base.update(
            {
                "lmstudio_url": self.lmstudio_base_url,
                "complexity_threshold": self.complexity_threshold,
                "max_local_tokens": self.max_local_tokens,
                "privacy_mode": self.privacy_mode,
                "cloud_provider": self.cloud_provider,
                "cloud_model": self.cloud_model,
            }
        )
        return base


settings = RouterSettings()
