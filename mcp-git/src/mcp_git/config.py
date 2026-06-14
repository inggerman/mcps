"""
Configuración de mcp-git.

Extiende BaseMcpSettings con variables para controlar la ubicación
del repositorio y restricciones de operaciones Git.
Variables de entorno con prefijo GIT_ (ej: GIT_REPO_PATH=.).
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class GitSettings(BaseMcpSettings):
    """
    Configuración del servidor MCP Git.

    Variables de entorno soportadas (prefijo GIT_):
        GIT_REPO_PATH: Ruta al directorio del repositorio Git.
        GIT_DEFAULT_BRANCH: Rama principal (main o master).
        GIT_ALLOW_FORCE_PUSH: Si es true, permite hacer push --force.

    Variables heredadas (sin prefijo):
        LOG_LEVEL, LOG_FORMAT, MCP_HOST, MCP_PORT, MCP_TRANSPORT
    """

    model_config = SettingsConfigDict(
        env_prefix="GIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    repo_path: Path = Field(
        default=Path(),
        description=(
            "Ruta al repositorio Git sobre el que operará el servidor. "
            "Variable de entorno: GIT_REPO_PATH."
        ),
    )

    default_branch: str = Field(
        default="main",
        description=(
            "Nombre de la rama principal por defecto. Variable de entorno: GIT_DEFAULT_BRANCH."
        ),
    )

    allow_force_push: bool = Field(
        default=False,
        description=(
            "Si es true, permite al agente usar push --force (peligroso). "
            "Variable de entorno: GIT_ALLOW_FORCE_PUSH."
        ),
    )

    def to_log_context(self) -> dict:
        """Extiende el contexto de log base con parámetros de Git."""
        base = super().to_log_context()
        base.update(
            {
                "repo_path": str(self.repo_path),
                "default_branch": self.default_branch,
                "allow_force_push": self.allow_force_push,
            }
        )
        return base


settings = GitSettings()
