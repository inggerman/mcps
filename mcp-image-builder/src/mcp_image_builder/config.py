"""Configuración del servidor mcp-image-builder."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class ImageBuilderSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="IMAGE_BUILDER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    harbor_url: str = Field(
        default="http://harbor-core.harbor.svc.cluster.local:80",
        description="URL de Harbor Core. Variable: IMAGE_BUILDER_HARBOR_URL.",
    )
    harbor_username: str = Field(
        default="admin",
        description="Usuario de Harbor. Variable: IMAGE_BUILDER_HARBOR_USERNAME.",
    )
    harbor_password: str = Field(
        default="",
        description="Password de Harbor. Variable: IMAGE_BUILDER_HARBOR_PASSWORD.",
    )
    harbor_project: str = Field(
        default="ghl",
        description="Proyecto de Harbor. Variable: IMAGE_BUILDER_HARBOR_PROJECT.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: IMAGE_BUILDER_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["harbor_url"] = self.harbor_url
        base["harbor_project"] = self.harbor_project
        return base


settings = ImageBuilderSettings()
