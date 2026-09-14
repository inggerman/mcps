"""Configuración del servidor mcp-comfyui."""

from __future__ import annotations

import os
from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class ComfyUISettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_COMFYUI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    comfyui_url: str = Field(
        default_factory=lambda: os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188"),
        description="URL base del servidor ComfyUI. Variable: COMFYUI_URL o MCP_COMFYUI_COMFYUI_URL.",
    )
    default_timeout: float = Field(
        default=120.0,
        ge=1.0,
        le=600.0,
        description="Timeout en segundos para peticiones a ComfyUI (generaciones pueden tardar). Variable: MCP_COMFYUI_DEFAULT_TIMEOUT.",
    )
    poll_interval: float = Field(
        default=2.0,
        ge=0.5,
        le=30.0,
        description="Intervalo de polling para verificar estado de generación (segundos). Variable: MCP_COMFYUI_POLL_INTERVAL.",
    )
    max_poll_attempts: int = Field(
        default=300,
        ge=10,
        le=1800,
        description="Máximo número de intentos de polling antes de timeout (300 * 2s = 10min default). Variable: MCP_COMFYUI_MAX_POLL_ATTEMPTS.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["comfyui_url"] = self.comfyui_url
        base["default_timeout"] = self.default_timeout
        return base


settings = ComfyUISettings()
