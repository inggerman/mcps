"""
Configuración de mcp-sonar.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class SonarSettings(BaseMcpSettings):
    """Configuración del servidor MCP Sonar."""

    model_config = SettingsConfigDict(
        env_prefix="SONAR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_path: Path = Field(
        default=Path(),
        description="Ruta base del proyecto.",
    )

    host_url: str = Field(
        default="http://localhost:9000",
        description="URL del servidor SonarQube."
    )

    api_token: str = Field(
        default="",
        description="Token de API de SonarQube."
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update({
            "project_path": str(self.project_path),
            "host_url": self.host_url,
            "has_token": bool(self.api_token)
        })
        return base


settings = SonarSettings()
