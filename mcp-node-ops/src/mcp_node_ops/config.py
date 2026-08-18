"""Configuración del servidor mcp-node-ops."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class NodeOpsSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="NODE_OPS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    kubeconfig_path: str = Field(
        default="",
        description="Ruta al kubeconfig (vacío = in-cluster). Variable: NODE_OPS_KUBECONFIG_PATH.",
    )
    allow_write: bool = Field(
        default=False,
        description="Permitir cordon/uncordon/drain/taint. Variable: NODE_OPS_ALLOW_WRITE.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["allow_write"] = self.allow_write
        return base


settings = NodeOpsSettings()
