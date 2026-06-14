"""Configuration for mcp-object-storage."""

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class ObjectStorageSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="OBJECT_STORAGE_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    endpoint_url: str | None = Field(default=None)
    region: str = Field(default="us-east-1")
    profile: str | None = Field(default=None)
    allow_write: bool = Field(default=False)
    max_keys: int = Field(default=500, ge=1, le=1000)


settings = ObjectStorageSettings()
