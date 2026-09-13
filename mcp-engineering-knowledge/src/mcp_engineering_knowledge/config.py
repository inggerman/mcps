"""Configuration for mcp-engineering-knowledge."""

from __future__ import annotations

from typing import Any

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class KnowledgeSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="KB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    docs_path: str = Field(
        default="/repo/docs",
        description="Path to the docs/ directory. Variable: KB_DOCS_PATH.",
    )
    qdrant_url: str = Field(
        default="http://qdrant.qdrant.svc.cluster.local:6333",
        description="URL of Qdrant. Variable: KB_QDRANT_URL.",
    )
    qdrant_api_key: str = Field(
        default="",
        description="API key for Qdrant (optional). Variable: KB_QDRANT_API_KEY.",
    )
    embedding_base_url: str = Field(
        default="http://host.docker.internal:1234/v1",
        description="LM Studio embedding API base URL. Variable: KB_EMBEDDING_BASE_URL.",
    )
    embedding_model: str = Field(
        default="text-embedding-nomic-embed-text-v1.5",
        description="Embedding model name. Variable: KB_EMBEDDING_MODEL.",
    )
    embedding_dim: int = Field(
        default=768,
        ge=1,
        description="Embedding vector dimension. Variable: KB_EMBEDDING_DIM.",
    )
    allow_write: bool = Field(
        default=False,
        description="Allow write operations (update, reindex, invalidate). Variable: KB_ALLOW_WRITE.",
    )
    trust_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum trust score for sources. Variable: KB_TRUST_THRESHOLD.",
    )
    chunk_size: int = Field(
        default=800,
        ge=100,
        le=4000,
        description="Target chunk size in tokens. Variable: KB_CHUNK_SIZE.",
    )
    chunk_overlap: int = Field(
        default=100,
        ge=0,
        le=500,
        description="Overlap between chunks in tokens. Variable: KB_CHUNK_OVERLAP.",
    )
    collection_name: str = Field(
        default="engineering-knowledge",
        description="Qdrant collection name. Variable: KB_COLLECTION_NAME.",
    )
    default_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        description="HTTP timeout in seconds. Variable: KB_DEFAULT_TIMEOUT.",
    )
    freshness_standards_days: int = Field(
        default=90,
        ge=1,
        description="Staleness threshold for standards in days. Variable: KB_FRESHNESS_STANDARDS_DAYS.",
    )
    freshness_patterns_days: int = Field(
        default=180,
        ge=1,
        description="Staleness threshold for patterns in days. Variable: KB_FRESHNESS_PATTERNS_DAYS.",
    )
    freshness_manuals_days: int = Field(
        default=365,
        ge=1,
        description="Staleness threshold for manuals in days. Variable: KB_FRESHNESS_MANUALS_DAYS.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["docs_path"] = self.docs_path
        base["qdrant_url"] = self.qdrant_url
        base["embedding_model"] = self.embedding_model
        base["allow_write"] = self.allow_write
        base["collection_name"] = self.collection_name
        return base


settings = KnowledgeSettings()
