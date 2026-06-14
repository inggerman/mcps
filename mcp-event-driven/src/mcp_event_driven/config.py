"""
Configuración de mcp-event-driven.

Variables de entorno con prefijo EVENT_.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class EventDrivenSettings(BaseMcpSettings):
    """
    Configuración del servidor MCP Event Driven.

    Variables soportadas (prefijo EVENT_):
        EVENT_SCHEMAS_PATH: Ruta al directorio donde se guardan los esquemas (JSON Schema / AsyncAPI).
    """

    model_config = SettingsConfigDict(
        env_prefix="EVENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    schemas_path: Path = Field(
        default=Path("./schemas"),
        description="Ruta donde se almacenan los esquemas de eventos.",
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update({"schemas_path": str(self.schemas_path)})
        return base


settings = EventDrivenSettings()
