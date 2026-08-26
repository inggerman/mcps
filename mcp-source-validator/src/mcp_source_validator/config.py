"""Configuración del servidor mcp-source-validator."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class SourceValidatorSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_SOURCE_VALIDATOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    default_timeout: float = Field(
        default=15.0,
        ge=1.0,
        le=60.0,
        description="Timeout for HTTP checks. Variable: MCP_SOURCE_VALIDATOR_DEFAULT_TIMEOUT.",
    )
    min_trust_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum trust score to consider a source valid.",
    )
    check_ssl: bool = Field(
        default=True,
        description="Check SSL certificate validity.",
    )
    check_content_freshness: bool = Field(
        default=True,
        description="Check if content has a recent last-modified date.",
    )
    freshness_days: int = Field(
        default=365,
        ge=1,
        description="Max days since last-modified to consider fresh.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["min_trust_score"] = self.min_trust_score
        base["check_ssl"] = self.check_ssl
        return base


settings = SourceValidatorSettings()
