"""Configuración del servidor mcp-rabbitmq."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class RabbitMQSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="RABBITMQ_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_url: str = Field(
        default="http://rabbitmq.rabbitmq.svc.cluster.local:15672/api",
        description="URL de la API Management de RabbitMQ. Variable: RABBITMQ_API_URL.",
    )
    username: str = Field(
        default="guest",
        description="Usuario de RabbitMQ Management. Variable: RABBITMQ_USERNAME.",
    )
    password: str = Field(
        default="",
        description="Password de RabbitMQ Management. Variable: RABBITMQ_PASSWORD.",
    )
    allow_publish: bool = Field(
        default=False,
        description="Permitir publicación de mensajes. Variable: RABBITMQ_ALLOW_PUBLISH.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: RABBITMQ_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["api_url"] = self.api_url
        base["allow_publish"] = self.allow_publish
        return base


settings = RabbitMQSettings()
