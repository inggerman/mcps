"""Configuración del servidor mcp-argocd."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class ArgoCDSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="ARGOCD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_url: str = Field(
        default="http://argocd-server.argocd.svc.cluster.local:80",
        description="URL de la API de ArgoCD. Variable: ARGOCD_API_URL.",
    )
    api_token: str = Field(
        default="",
        description="Token de API de ArgoCD. Variable: ARGOCD_API_TOKEN.",
    )
    allow_sync: bool = Field(
        default=False,
        description="Permitir operaciones de sync. Variable: ARGOCD_ALLOW_SYNC.",
    )
    allow_rollback: bool = Field(
        default=False,
        description="Permitir rollback. Variable: ARGOCD_ALLOW_ROLLBACK.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: ARGOCD_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["api_url"] = self.api_url
        base["allow_sync"] = self.allow_sync
        base["allow_rollback"] = self.allow_rollback
        return base


settings = ArgoCDSettings()
