"""
Configuración de mcp-covaf-data.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class CovafDataSettings(BaseMcpSettings):
    """Configuración del servidor MCP COVAF Data."""

    model_config = SettingsConfigDict(
        env_prefix="COVAF_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    workspace_path: Path = Field(
        default=Path("/workspace"),
        description="Ruta raíz del workspace engineering (donde vive covaf/).",
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update({"workspace_path": str(self.workspace_path)})
        return base


settings = CovafDataSettings()
