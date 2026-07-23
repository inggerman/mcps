"""
Configuración de mcp-terraform.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class TerraformSettings(BaseMcpSettings):
    """Configuración del servidor MCP Terraform."""

    model_config = SettingsConfigDict(
        env_prefix="TF_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_path: Path = Field(
        default=Path(),
        description="Ruta base donde están los archivos .tf.",
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update({"project_path": str(self.project_path)})
        return base


settings = TerraformSettings()
