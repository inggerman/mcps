"""
Configuración del servidor MCP Prompt Engineer.

Hereda de BaseMcpSettings (pydantic-settings) para gestión uniforme
de variables de entorno en todo el framework MCP.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración del servidor mcp-prompt-engineer.

    Todas las variables se pueden sobrescribir con variables de entorno
    con el prefijo MCP_PE_ (por compatibilidad con otros servidores del framework).
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_PE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: str = Field(
        default="INFO",
        description="Nivel de logging: DEBUG | INFO | WARNING | ERROR",
        alias="LOG_LEVEL",
    )
    log_format: str = Field(
        default="json",
        description="Formato de logging: json (producción) | console (desarrollo)",
        alias="LOG_FORMAT",
    )

    # -------------------------------------------------------------------------
    # Límites del analizador
    # -------------------------------------------------------------------------
    max_prompt_length: int = Field(
        default=100_000,
        ge=100,
        le=1_000_000,
        description="Longitud máxima del prompt en caracteres.",
    )
    max_variations: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Número máximo de variaciones a generar.",
    )
    default_variations: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Número por defecto de variaciones a generar.",
    )

    # -------------------------------------------------------------------------
    # Tokenización
    # -------------------------------------------------------------------------
    default_model: str = Field(
        default="gpt-4o",
        description="Modelo por defecto para estimación de tokens.",
    )
    tiktoken_cache_dir: str | None = Field(
        default=None,
        description="Directorio de caché para modelos tiktoken (opcional).",
    )

    # -------------------------------------------------------------------------
    # Servidor MCP
    # -------------------------------------------------------------------------
    server_name: str = Field(
        default="mcp-prompt-engineer",
        description="Nombre del servidor MCP.",
    )
    server_version: str = Field(
        default="1.0.0",
        description="Versión del servidor MCP.",
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Instancia global de configuración
settings = Settings()
