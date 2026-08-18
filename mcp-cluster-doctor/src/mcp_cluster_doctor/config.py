"""Configuración del servidor mcp-cluster-doctor."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class ClusterDoctorSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="CLUSTER_DOCTOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    kubeconfig_path: str = Field(
        default="",
        description="Ruta al kubeconfig (vacío = in-cluster). Variable: CLUSTER_DOCTOR_KUBECONFIG_PATH.",
    )
    default_namespace: str = Field(
        default="default",
        description="Namespace por defecto. Variable: CLUSTER_DOCTOR_DEFAULT_NAMESPACE.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["default_namespace"] = self.default_namespace
        base["in_cluster"] = not bool(self.kubeconfig_path)
        return base


settings = ClusterDoctorSettings()
