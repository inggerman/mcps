"""Configuration for mcp-personal-vault."""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class PersonalVaultSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="PERSONAL_VAULT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    database_path: Path = Field(default=Path("data/personal-vault/personal.db"))
    key_file: Path = Field(default=Path("data/personal-vault/vault.key"))
    encryption_key: str | None = Field(default=None, repr=False)
    allow_write: bool = Field(default=False)
    allow_highly_sensitive: bool = Field(default=False)
    allow_secrets: bool = Field(default=False)
    max_results: int = Field(default=25, ge=1, le=200)

    def to_log_context(self) -> dict:
        context = super().to_log_context()
        context.update(
            {
                "database_path": str(self.database_path),
                "allow_write": self.allow_write,
                "allow_highly_sensitive": self.allow_highly_sensitive,
                "allow_secrets": self.allow_secrets,
            }
        )
        return context


settings = PersonalVaultSettings()
