"""Configuración del servidor mcp-n8n."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class N8nSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="N8N_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_url: str = Field(
        default="http://n8n.n8n.svc.cluster.local:5678/api/v1",
        description="URL de la API de n8n. Variable: N8N_API_URL.",
    )
    api_key: str = Field(
        default="",
        description="API key de n8n. Variable: N8N_API_KEY.",
    )
    webhook_base_url: str = Field(
        default="http://n8n.n8n.svc.cluster.local:5678/webhook",
        description="URL base para webhooks de n8n. Variable: N8N_WEBHOOK_BASE_URL.",
    )
    allow_activate: bool = Field(
        default=False,
        description="Permitir activar/desactivar workflows. Variable: N8N_ALLOW_ACTIVATE.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: N8N_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["api_url"] = self.api_url
        base["allow_activate"] = self.allow_activate
        return base


settings = N8nSettings()
