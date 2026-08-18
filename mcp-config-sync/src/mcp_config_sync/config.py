"""Configuración del servidor mcp-config-sync."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class ConfigSyncSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="CONFIG_SYNC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    kubeconfig_path: str = Field(
        default="",
        description="Ruta al kubeconfig (vacío = in-cluster). Variable: CONFIG_SYNC_KUBECONFIG_PATH.",
    )
    allow_write: bool = Field(
        default=False,
        description="Permitir crear/actualizar ConfigMaps. Variable: CONFIG_SYNC_ALLOW_WRITE.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["allow_write"] = self.allow_write
        return base


settings = ConfigSyncSettings()
