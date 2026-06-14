"""
Configuración de mcp-best-practices.

Variables de entorno con prefijo BP_.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class BestPracticesSettings(BaseMcpSettings):
    """Configuración del servidor MCP Best Practices."""

    model_config = SettingsConfigDict(
        env_prefix="BP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_path: Path = Field(
        default=Path(),
        description="Ruta base del proyecto.",
    )
    docs_path: Path = Field(
        default=Path("./docs"),
        description="Ruta donde se almacenará la documentación retroactiva.",
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update(
            {
                "project_path": str(self.project_path),
                "docs_path": str(self.docs_path),
            }
        )
        return base


settings = BestPracticesSettings()
