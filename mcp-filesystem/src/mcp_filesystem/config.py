"""Configuration for mcp-filesystem."""

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class FilesystemSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="FILESYSTEM_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    root: Path = Field(default=Path.cwd())
    allow_write: bool = Field(default=False)
    max_read_bytes: int = Field(default=2 * 1024 * 1024, ge=1024)
    max_results: int = Field(default=500, ge=1, le=10_000)


settings = FilesystemSettings()
