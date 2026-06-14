from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class ObservabilitySettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="OBSERVABILITY_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    prometheus_url: str | None = Field(default=None)
    loki_url: str | None = Field(default=None)
    timeout_seconds: float = Field(default=30.0, ge=1, le=120)
    bearer_token: str | None = Field(default=None)
    max_entries: int = Field(default=500, ge=1, le=5000)


settings = ObservabilitySettings()
