from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class DocumentSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="DOCUMENTS_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    root: Path = Field(default=Path.cwd())
    max_file_size_mb: int = Field(default=50, ge=1, le=500)
    max_pages: int = Field(default=200, ge=1, le=5000)


settings = DocumentSettings()
