"""
Configuración del servidor mcp-smart-home.

Extiende BaseMcpSettings con variables específicas de Tuya IoT Platform.
Todas las variables se pueden sobreescribir mediante variables de entorno
o el archivo .env en el directorio raíz del workspace.
"""

from __future__ import annotations

from typing import Literal

from mcp_shared.config import BaseMcpSettings
from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict


class SmartHomeSettings(BaseMcpSettings):
    """
    Configuración específica del servidor mcp-smart-home.

    Variables de entorno disponibles (con prefijo TUYA_):
        TUYA_ACCESS_ID: Access ID del proyecto en Tuya IoT Platform.
        TUYA_ACCESS_KEY: Access Secret del proyecto.
        TUYA_REGION: Región del data center (us, eu, cn, in).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TUYA_",
        extra="ignore",
        case_sensitive=False,
    )

    access_id: str = Field(
        default="",
        description=(
            "Access ID del proyecto en Tuya IoT Platform (iot.tuya.com). "
            "Variable de entorno: TUYA_ACCESS_ID."
        ),
    )

    access_key: SecretStr = Field(
        default=SecretStr(""),
        description=(
            "Access Secret del proyecto en Tuya IoT Platform. "
            "Variable de entorno: TUYA_ACCESS_KEY."
        ),
    )

    region: Literal["us", "eu", "cn", "in"] = Field(
        default="us",
        description=(
            "Región del data center de Tuya. "
            "Valores válidos: us, eu, cn, in. "
            "Variable de entorno: TUYA_REGION."
        ),
    )

    device_cache_ttl: int = Field(
        default=300,
        ge=30,
        le=3600,
        description=(
            "TTL del caché de lista de dispositivos en segundos. "
            "Rango válido: 30–3600. "
            "Variable de entorno: TUYA_DEVICE_CACHE_TTL."
        ),
    )

    mcp_server_name: str = Field(
        default="mcp-smart-home",
        description="Nombre identificador del servidor MCP en logs y metadatos.",
    )

    @property
    def access_key_value(self) -> str:
        """Retorna el Access Secret como string plano."""
        return self.access_key.get_secret_value()

    def to_log_context(self) -> dict:
        """Retorna contexto de log sin exponer el Access Secret."""
        ctx = super().to_log_context()
        ctx.update(
            {
                "access_id": self.access_id,
                "region": self.region,
                "device_cache_ttl": self.device_cache_ttl,
            }
        )
        return ctx
