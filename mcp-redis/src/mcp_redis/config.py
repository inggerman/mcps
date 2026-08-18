"""Configuración del servidor mcp-redis."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class RedisSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    host: str = Field(
        default="redis-master.redis.svc.cluster.local",
        description="Host de Redis. Variable: REDIS_HOST.",
    )
    port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Puerto de Redis. Variable: REDIS_PORT.",
    )
    password: str = Field(
        default="",
        description="Password de Redis. Variable: REDIS_PASSWORD.",
    )
    db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Número de base de datos Redis. Variable: REDIS_DB.",
    )
    allow_write: bool = Field(
        default=False,
        description="Permitir operaciones de escritura (SET, DEL, EXPIRE). Variable: REDIS_ALLOW_WRITE.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["host"] = self.host
        base["port"] = self.port
        base["db"] = self.db
        base["allow_write"] = self.allow_write
        return base


settings = RedisSettings()
