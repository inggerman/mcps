"""Configuration for mcp-database."""

from __future__ import annotations

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class DatabaseSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    url: str = Field(default="sqlite:///./data/database.db")
    read_only: bool = Field(default=True)
    max_rows: int = Field(default=500, ge=1, le=10_000)
    statement_timeout_seconds: int = Field(default=30, ge=1, le=300)

    def to_log_context(self) -> dict:
        context = super().to_log_context()
        context.update({"read_only": self.read_only, "max_rows": self.max_rows})
        return context


settings = DatabaseSettings()
