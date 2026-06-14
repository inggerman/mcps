from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class KubernetesSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="KUBERNETES_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    context: str | None = Field(default=None)
    namespace: str = Field(default="default")
    in_cluster: bool = Field(default=False)
    allow_write: bool = Field(default=False)
    log_tail_lines: int = Field(default=200, ge=1, le=10_000)


settings = KubernetesSettings()
