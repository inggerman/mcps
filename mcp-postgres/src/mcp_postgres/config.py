"""Configuración del servidor mcp-postgres."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class PostgresSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    host: str = Field(
        default="postgres-postgresql.postgres.svc.cluster.local",
        description="Host de PostgreSQL. Variable: POSTGRES_HOST.",
    )
    port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        description="Puerto de PostgreSQL. Variable: POSTGRES_PORT.",
    )
    database: str = Field(
        default="postgres",
        description="Base de datos por defecto. Variable: POSTGRES_DATABASE.",
    )
    user: str = Field(
        default="postgres",
        description="Usuario de PostgreSQL. Variable: POSTGRES_USER.",
    )
    password: str = Field(
        default="",
        description="Password de PostgreSQL. Variable: POSTGRES_PASSWORD.",
    )
    allow_write: bool = Field(
        default=False,
        description="Permitir queries de escritura (INSERT/UPDATE/DELETE/DDL). Variable: POSTGRES_ALLOW_WRITE.",
    )
    query_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Timeout de queries en segundos. Variable: POSTGRES_QUERY_TIMEOUT.",
    )
    max_rows: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Máximo número de filas a retornar. Variable: POSTGRES_MAX_ROWS.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["host"] = self.host
        base["port"] = self.port
        base["database"] = self.database
        base["allow_write"] = self.allow_write
        return base

    @property
    def connection_string(self) -> str:
        return f"host={self.host} port={self.port} dbname={self.database} user={self.user} password={self.password}"


settings = PostgresSettings()
