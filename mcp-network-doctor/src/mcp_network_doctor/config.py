"""Configuración del servidor mcp-network-doctor."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class NetworkDoctorSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="NETWORK_DOCTOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    kubeconfig_path: str = Field(
        default="",
        description="Ruta al kubeconfig (vacío = in-cluster). Variable: NETWORK_DOCTOR_KUBECONFIG_PATH.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["in_cluster"] = not bool(self.kubeconfig_path)
        return base


settings = NetworkDoctorSettings()
