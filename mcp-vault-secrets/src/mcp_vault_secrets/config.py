"""Configuración del servidor mcp-vault-secrets."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class VaultSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="VAULT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_url: str = Field(
        default="http://vault.vault.svc.cluster.local:8200",
        description="URL de la API de Vault. Variable: VAULT_API_URL.",
    )
    token: str = Field(
        default="",
        description="Token de Vault. Variable: VAULT_TOKEN.",
    )
    allowed_paths: str = Field(
        default="",
        description="Comma-separated list of allowed secret path prefixes. Variable: VAULT_ALLOWED_PATHS.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: VAULT_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["api_url"] = self.api_url
        base["allowed_paths"] = self.allowed_paths
        return base

    @property
    def allowed_path_list(self) -> list[str]:
        if not self.allowed_paths:
            return []
        return [p.strip() for p in self.allowed_paths.split(",") if p.strip()]


settings = VaultSettings()
