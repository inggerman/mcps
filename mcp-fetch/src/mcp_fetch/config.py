"""Configuración del servidor mcp-fetch."""

from __future__ import annotations

from typing import Any

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from mcp_shared.config import BaseMcpSettings


class FetchSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_FETCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout en segundos para peticiones HTTP. Variable: MCP_FETCH_DEFAULT_TIMEOUT.",
    )
    max_content_length: int = Field(
        default=5 * 1024 * 1024,
        ge=1024,
        description="Tamaño máximo de respuesta en bytes (default 5 MB). Variable: MCP_FETCH_MAX_CONTENT_LENGTH.",
    )
    user_agent: str = Field(
        default="mcp-fetch/1.0 (MCP HTTP client)",
        description="User-Agent enviado en peticiones. Variable: MCP_FETCH_USER_AGENT.",
    )
    follow_redirects: bool = Field(
        default=True,
        description="Seguir redirecciones HTTP. Variable: MCP_FETCH_FOLLOW_REDIRECTS.",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Verificar certificados SSL. Variable: MCP_FETCH_VERIFY_SSL.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["default_timeout"] = self.default_timeout
        base["max_content_length"] = self.max_content_length
        return base


settings = FetchSettings()
