"""
Configuración del servidor mcp-calendar.

Extiende BaseMcpSettings con variables específicas del calendario y divisas.
Todas las variables se pueden sobreescribir mediante variables de entorno
o el archivo .env en el directorio raíz del workspace.
"""

from __future__ import annotations

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class CalendarSettings(BaseMcpSettings):
    """
    Configuración específica del servidor mcp-calendar.

    Variables de entorno disponibles (sin prefijo):
        DEFAULT_COUNTRY: Código ISO 3166-1 alpha-2 del país por defecto.
        EXCHANGE_RATE_PROVIDER: Proveedor de tasas de cambio.
        EXCHANGE_RATE_API_KEY: API key para exchangerate-api.com.
        EXCHANGE_CACHE_TTL_SECONDS: TTL del caché de tasas en segundos.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Calendario ---
    default_country: str = Field(
        default="MX",
        description=(
            "Código de país ISO 3166-1 alpha-2 usado por defecto en todas las "
            "operaciones de calendario cuando no se especifica explícitamente. "
            "Variable de entorno: DEFAULT_COUNTRY."
        ),
    )

    # --- Divisas ---
    exchange_rate_provider: str = Field(
        default="frankfurter",
        description=(
            "Proveedor de tasas de cambio a utilizar. "
            "Opciones: 'frankfurter' (gratuito, sin key) | 'exchangerate-api' (requiere key). "
            "Variable de entorno: EXCHANGE_RATE_PROVIDER."
        ),
    )
    exchange_rate_api_key: str = Field(
        default="",
        description=(
            "API key para exchangerate-api.com. "
            "Solo requerida cuando EXCHANGE_RATE_PROVIDER=exchangerate-api. "
            "Variable de entorno: EXCHANGE_RATE_API_KEY."
        ),
    )
    exchange_cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description=(
            "Tiempo de vida del caché de tasas de cambio en segundos. "
            "Rango válido: 60–86400 (1 minuto a 24 horas). "
            "Variable de entorno: EXCHANGE_CACHE_TTL_SECONDS."
        ),
    )

    # --- Nombre del servidor ---
    mcp_server_name: str = Field(
        default="mcp-calendar",
        description="Nombre identificador del servidor MCP en logs y metadatos.",
    )

    def to_log_context(self) -> dict:
        """Retorna contexto de log sin exponer la API key."""
        ctx = super().to_log_context()
        ctx.update(
            {
                "default_country": self.default_country,
                "exchange_rate_provider": self.exchange_rate_provider,
                "exchange_cache_ttl_seconds": self.exchange_cache_ttl_seconds,
                "has_api_key": bool(self.exchange_rate_api_key),
            }
        )
        return ctx
