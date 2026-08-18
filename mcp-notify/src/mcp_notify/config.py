"""Configuración del servidor mcp-notify."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class NotifySettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="NOTIFY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    smtp_host: str = Field(
        default="",
        description="Host del servidor SMTP. Variable: NOTIFY_SMTP_HOST.",
    )
    smtp_port: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="Puerto SMTP. Variable: NOTIFY_SMTP_PORT.",
    )
    smtp_user: str = Field(
        default="",
        description="Usuario SMTP. Variable: NOTIFY_SMTP_USER.",
    )
    smtp_password: str = Field(
        default="",
        description="Password SMTP. Variable: NOTIFY_SMTP_PASSWORD.",
    )
    smtp_from: str = Field(
        default="",
        description="Email remitente. Variable: NOTIFY_SMTP_FROM.",
    )
    smtp_use_tls: bool = Field(
        default=True,
        description="Usar TLS. Variable: NOTIFY_SMTP_USE_TLS.",
    )
    telegram_bot_token: str = Field(
        default="",
        description="Token del bot de Telegram. Variable: NOTIFY_TELEGRAM_BOT_TOKEN.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: NOTIFY_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["smtp_host"] = self.smtp_host
        base["smtp_from"] = self.smtp_from
        base["telegram_configured"] = bool(self.telegram_bot_token)
        return base


settings = NotifySettings()
