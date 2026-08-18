"""Configuración del servidor mcp-harbor."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class HarborSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="HARBOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_url: str = Field(
        default="http://harbor-core.harbor.svc.cluster.local:80/api/v2.0",
        description="URL de la API de Harbor. Variable: HARBOR_API_URL.",
    )
    username: str = Field(
        default="admin",
        description="Usuario de Harbor. Variable: HARBOR_USERNAME.",
    )
    password: str = Field(
        default="",
        description="Password de Harbor. Variable: HARBOR_PASSWORD.",
    )
    allow_delete: bool = Field(
        default=False,
        description="Permitir borrado de tags. Variable: HARBOR_ALLOW_DELETE.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: HARBOR_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["api_url"] = self.api_url
        base["allow_delete"] = self.allow_delete
        return base


settings = HarborSettings()
