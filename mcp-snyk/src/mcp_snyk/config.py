"""
Configuración de mcp-snyk.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class SnykSettings(BaseMcpSettings):
    """Configuración del servidor MCP Snyk."""

    model_config = SettingsConfigDict(
        env_prefix="SNYK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_path: Path = Field(
        default=Path(),
        description="Ruta base del proyecto.",
    )

    api_token: str = Field(
        default="",
        description="Token de API de Snyk (opcional para CLI auth global)."
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update({
            "project_path": str(self.project_path),
            "has_token": bool(self.api_token)
        })
        return base


settings = SnykSettings()
