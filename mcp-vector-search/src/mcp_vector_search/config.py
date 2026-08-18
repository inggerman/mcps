"""Configuración del servidor mcp-vector-search."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class VectorSearchSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="VECTOR_SEARCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    qdrant_url: str = Field(
        default="http://qdrant.mcps.svc.cluster.local:6333",
        description="URL de Qdrant. Variable: VECTOR_SEARCH_QDRANT_URL.",
    )
    qdrant_api_key: str = Field(
        default="",
        description="API key de Qdrant (opcional). Variable: VECTOR_SEARCH_QDRANT_API_KEY.",
    )
    embedding_base_url: str = Field(
        default="http://host.docker.internal:1234/v1",
        description="URL base del servicio de embeddings (LM Studio). Variable: VECTOR_SEARCH_EMBEDDING_BASE_URL.",
    )
    embedding_model: str = Field(
        default="text-embedding-nomic-embed-text-v1.5",
        description="Modelo de embeddings. Variable: VECTOR_SEARCH_EMBEDDING_MODEL.",
    )
    embedding_dim: int = Field(
        default=768,
        ge=1,
        description="Dimensión del vector de embeddings. Variable: VECTOR_SEARCH_EMBEDDING_DIM.",
    )
    allow_write: bool = Field(
        default=False,
        description="Permitir upsert y delete. Variable: VECTOR_SEARCH_ALLOW_WRITE.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="Timeout HTTP en segundos. Variable: VECTOR_SEARCH_DEFAULT_TIMEOUT.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["qdrant_url"] = self.qdrant_url
        base["embedding_model"] = self.embedding_model
        base["embedding_dim"] = self.embedding_dim
        base["allow_write"] = self.allow_write
        return base


settings = VectorSearchSettings()
