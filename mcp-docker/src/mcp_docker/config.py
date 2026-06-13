"""Configuración del servidor mcp-docker."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class DockerSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_DOCKER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    docker_host: str | None = Field(
        default=None,
        description=(
            "URL del daemon Docker. None = usa DOCKER_HOST del entorno o socket por defecto. "
            "Variable: MCP_DOCKER_DOCKER_HOST. Ej: unix:///var/run/docker.sock o tcp://host:2376"
        ),
    )
    log_lines: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Número de líneas de logs a retornar por defecto. Variable: MCP_DOCKER_LOG_LINES.",
    )
    exec_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout en segundos para exec en contenedor. Variable: MCP_DOCKER_EXEC_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["docker_host"] = self.docker_host or "default"
        return base


settings = DockerSettings()
