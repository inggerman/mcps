"""
Configuracion especifica de mcp-gob-mexico.

Extiende BaseMcpSettings con variables de entorno para tokens de APIs
del gobierno mexicano (INEGI, Banxico).
"""

from __future__ import annotations

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class GobMexicoSettings(BaseMcpSettings):
    """
    Configuracion del servidor MCP Gob Mexico.

    Variables de entorno soportadas (prefijo GOB_MX_):
        GOB_MX_INEGI_TOKEN: Token para APIs del INEGI (gratuito).
        GOB_MX_BANXICO_TOKEN: Token para API SIE de Banxico (gratuito).
        GOB_MX_HTTP_TIMEOUT: Timeout HTTP en segundos (default 30).
        GOB_MX_MAX_RETRIES: Reintentos maximos por peticion (default 3).
        GOB_MX_CACHE_TTL: TTL de cache en segundos (default 300).
    """

    inegi_token: str = Field(default="", description="Token API INEGI")
    banxico_token: str = Field(default="", description="Token API Banxico SIE")
    http_timeout: int = Field(default=30, ge=5, le=120, description="Timeout HTTP en segundos")
    max_retries: int = Field(default=3, ge=1, le=10, description="Reintentos maximos")
    cache_ttl: int = Field(default=300, ge=0, le=3600, description="TTL cache en segundos")

    model_config = SettingsConfigDict(
        env_prefix="GOB_MX_",
        env_file=".env",
        extra="ignore",
    )


settings = GobMexicoSettings()
