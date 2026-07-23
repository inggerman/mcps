"""
Configuración de mcp-agent-runner.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class AgentRunnerSettings(BaseMcpSettings):
    """Configuración del servidor MCP Agent Runner."""

    model_config = SettingsConfigDict(
        env_prefix="AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_path: Path = Field(
        default=Path(),
        description="Ruta base del proyecto.",
    )

    n8n_webhook_base_url: str = Field(
        default="http://localhost:5678/webhook",
        description="URL base para webhooks de n8n."
    )

    n8n_auth_token: str = Field(
        default="",
        description="Token opcional para autenticar webhooks de n8n."
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update({
            "project_path": str(self.project_path),
            "webhook_base": self.n8n_webhook_base_url,
        })
        return base


settings = AgentRunnerSettings()
