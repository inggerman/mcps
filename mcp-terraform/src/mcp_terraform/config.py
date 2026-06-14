from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class TerraformSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="TERRAFORM_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    root: Path = Field(default=Path.cwd())
    binary: str = Field(default="terraform")
    timeout_seconds: int = Field(default=300, ge=10, le=3600)
    allow_apply: bool = Field(default=False)


settings = TerraformSettings()
