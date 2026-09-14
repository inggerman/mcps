"""Configuración del servidor mcp-openproject."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class OpenProjectSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPENPROJECT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_url: str = Field(
        default="http://openproject.openproject.svc.cluster.local/api/v3",
        description="URL de la API de OpenProject. Variable: OPENPROJECT_API_URL.",
    )
    api_token: str = Field(
        default="",
        description="Token de API (Basic auth con apikey). Variable: OPENPROJECT_API_TOKEN.",
    )
    allow_write: bool = Field(
        default=False,
        description="Permitir operaciones de escritura. Variable: OPENPROJECT_ALLOW_WRITE.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: OPENPROJECT_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["api_url"] = self.api_url
        base["allow_write"] = self.allow_write
        return base


settings = OpenProjectSettings()
