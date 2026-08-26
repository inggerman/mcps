"""Configuración del servidor mcp-web-search."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class WebSearchSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_WEB_SEARCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    provider: str = Field(
        default="duckduckgo",
        description="Search provider: duckduckgo | brave. Variable: MCP_WEB_SEARCH_PROVIDER.",
    )
    brave_api_key: str = Field(
        default="",
        description="Brave Search API key. Variable: MCP_WEB_SEARCH_BRAVE_API_KEY.",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max results per search. Variable: MCP_WEB_SEARCH_MAX_RESULTS.",
    )
    rate_limit_per_minute: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Max searches per minute. Variable: MCP_WEB_SEARCH_RATE_LIMIT_PER_MINUTE.",
    )
    trust_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Min trust score to include result. Variable: MCP_WEB_SEARCH_TRUST_THRESHOLD.",
    )
    snippet_max_length: int = Field(
        default=500,
        ge=50,
        description="Max length of result snippet. Variable: MCP_WEB_SEARCH_SNIPPET_MAX_LENGTH.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["provider"] = self.provider
        base["max_results"] = self.max_results
        base["trust_threshold"] = self.trust_threshold
        return base


settings = WebSearchSettings()
