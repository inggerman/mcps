"""
Configuración de mcp-github.

Controla la autenticación y repositorio objetivo para operaciones
contra la API de GitHub. Variables de entorno con prefijo GITHUB_.
"""

from __future__ import annotations

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class GitHubSettings(BaseMcpSettings):
    """
    Configuración del servidor MCP GitHub.

    Variables de entorno soportadas (prefijo GITHUB_):
        GITHUB_TOKEN: Personal Access Token de GitHub.
        GITHUB_OWNER: Propietario del repositorio (usuario u organización).
        GITHUB_REPO: Nombre del repositorio por defecto.
        GITHUB_API_URL: URL base de la API (útil para GitHub Enterprise).

    Variables heredadas (sin prefijo):
        LOG_LEVEL, LOG_FORMAT, MCP_HOST, MCP_PORT, MCP_TRANSPORT
    """

    model_config = SettingsConfigDict(
        env_prefix="GITHUB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    token: str = Field(
        default="",
        description=(
            "Personal Access Token (PAT) de GitHub para autenticación. "
            "Requerido para la mayoría de operaciones. "
            "Variable de entorno: GITHUB_TOKEN."
        ),
    )

    owner: str = Field(
        default="",
        description=(
            "Usuario u organización propietaria del repositorio. Variable de entorno: GITHUB_OWNER."
        ),
    )

    repo: str = Field(
        default="",
        description=(
            "Nombre del repositorio objetivo principal. Variable de entorno: GITHUB_REPO."
        ),
    )

    api_url: str = Field(
        default="https://api.github.com",
        description=(
            "URL base de la API de GitHub. Útil para GitHub Enterprise Server. "
            "Variable de entorno: GITHUB_API_URL."
        ),
    )

    timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Timeout para peticiones a la API en segundos.",
    )

    def to_log_context(self) -> dict:
        """Extiende el contexto de log base con parámetros de GitHub."""
        base = super().to_log_context()
        base.update(
            {
                "github_owner": self.owner,
                "github_repo": self.repo,
                "api_url": self.api_url,
                "has_token": bool(self.token),
            }
        )
        return base


settings = GitHubSettings()
