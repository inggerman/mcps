"""
Configuración de mcp-architecture.

Variables de entorno con prefijo ARCH_.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class ArchitectureSettings(BaseMcpSettings):
    """
    Configuración del servidor MCP Architecture.

    Variables soportadas (prefijo ARCH_):
        ARCH_PROJECT_PATH: Ruta al proyecto a analizar.
    """

    model_config = SettingsConfigDict(
        env_prefix="ARCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_path: Path = Field(
        default=Path(),
        description="Ruta base del proyecto a analizar.",
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update({"project_path": str(self.project_path)})
        return base


settings = ArchitectureSettings()
