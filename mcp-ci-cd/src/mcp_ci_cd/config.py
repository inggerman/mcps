"""
Configuración de mcp-ci-cd.

Variables de entorno con prefijo CICD_.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class CiCdSettings(BaseMcpSettings):
    """Configuración del servidor MCP CI/CD."""

    model_config = SettingsConfigDict(
        env_prefix="CICD_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_path: Path = Field(
        default=Path(),
        description="Ruta base del proyecto.",
    )

    # Comandos simulados para el pipeline
    test_cmd: str = Field(default="uv run pytest", description="Comando de test.")
    lint_cmd: str = Field(default="uv run ruff check", description="Comando de lint.")
    deploy_cmd: str = Field(
        default="echo 'Despliegue simulado exitoso'", description="Comando de despliegue."
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update({"project_path": str(self.project_path)})
        return base


settings = CiCdSettings()
