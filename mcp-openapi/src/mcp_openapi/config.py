from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class OpenApiSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPENAPI_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    spec: str = Field(default="./openapi.yaml")
    allowed_root: Path = Field(default=Path.cwd())
    timeout_seconds: float = Field(default=30.0, ge=1, le=120)
    allow_invoke: bool = Field(default=False)
    allowed_hosts: list[str] = Field(default_factory=list)


settings = OpenApiSettings()
