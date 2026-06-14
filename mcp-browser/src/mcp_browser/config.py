from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class BrowserSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="BROWSER_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    headless: bool = Field(default=True)
    timeout_ms: int = Field(default=30_000, ge=1000, le=120_000)
    allowed_hosts: list[str] = Field(default_factory=list)
    output_dir: Path = Field(default=Path("./data/browser"))


settings = BrowserSettings()
