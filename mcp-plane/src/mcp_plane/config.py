"""Configuración del servidor mcp-plane."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class PlaneSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="PLANE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_url: str = Field(
        default="http://plane.plane.svc.cluster.local/api/v1",
        description="URL de la API de Plane. Variable: PLANE_API_URL.",
    )
    api_token: str = Field(
        default="",
        description="Token de API de Plane. Variable: PLANE_API_TOKEN.",
    )
    workspace_slug: str = Field(
        default="",
        description="Slug del workspace por defecto en Plane. Variable: PLANE_WORKSPACE_SLUG.",
    )
    allow_write: bool = Field(
        default=False,
        description="Permitir operaciones de escritura (crear/actualizar issues). Variable: PLANE_ALLOW_WRITE.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: PLANE_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["api_url"] = self.api_url
        base["workspace_slug"] = self.workspace_slug
        base["allow_write"] = self.allow_write
        return base


settings = PlaneSettings()
