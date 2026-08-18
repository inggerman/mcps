"""Configuración del servidor mcp-log-explorer."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class LogExplorerSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="LOG_EXPLORER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    kubeconfig_path: str = Field(
        default="",
        description="Ruta al kubeconfig (vacío = in-cluster). Variable: LOG_EXPLORER_KUBECONFIG_PATH.",
    )
    default_namespace: str = Field(
        default="default",
        description="Namespace por defecto. Variable: LOG_EXPLORER_DEFAULT_NAMESPACE.",
    )
    max_lines: int = Field(
        default=500,
        ge=1,
        le=10000,
        description="Máximo de líneas a retornar. Variable: LOG_EXPLORER_MAX_LINES.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["default_namespace"] = self.default_namespace
        base["max_lines"] = self.max_lines
        return base


settings = LogExplorerSettings()
