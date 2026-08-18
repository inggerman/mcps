"""Configuración del servidor mcp-gitea."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class GiteaSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="GITEA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_url: str = Field(
        default="http://gitea-http.gitea.svc.cluster.local:3000/api/v1",
        description="URL de la API de Gitea. Variable: GITEA_API_URL.",
    )
    api_token: str = Field(
        default="",
        description="Token de API de Gitea. Variable: GITEA_API_TOKEN.",
    )
    allow_write: bool = Field(
        default=False,
        description="Permitir operaciones de escritura (crear PRs, issues). Variable: GITEA_ALLOW_WRITE.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: GITEA_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["api_url"] = self.api_url
        base["allow_write"] = self.allow_write
        return base


settings = GiteaSettings()
