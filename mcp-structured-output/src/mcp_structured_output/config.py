"""Configuración del servidor mcp-structured-output."""

from __future__ import annotations

from typing import Any

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from mcp_shared.config import BaseMcpSettings


class StructuredOutputSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_SO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    aws_region: str = Field(
        default="us-east-1",
        description="Región AWS por defecto para Bedrock. Variable: MCP_SO_AWS_REGION.",
    )
    aws_profile: str | None = Field(
        default=None,
        description="Perfil AWS opcional (boto3 credential chain). Variable: MCP_SO_AWS_PROFILE.",
    )
    default_provider: str = Field(
        default="bedrock-converse",
        description=(
            "Proveedor por defecto: bedrock-converse | bedrock-invoke-claude | "
            "bedrock-invoke-openweight | openai-compatible. Variable: MCP_SO_DEFAULT_PROVIDER."
        ),
    )
    default_model_id: str = Field(
        default="amazon.nova-pro-v1:0",
        description="ID del modelo por defecto. Variable: MCP_SO_DEFAULT_MODEL_ID.",
    )
    default_max_tokens: int = Field(
        default=2048,
        ge=1,
        le=32768,
        description="Max tokens por defecto. Variable: MCP_SO_DEFAULT_MAX_TOKENS.",
    )
    default_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Temperature por defecto (0.0 recomendado para structured output). "
            "Variable: MCP_SO_DEFAULT_TEMPERATURE."
        ),
    )
    openai_base_url: str | None = Field(
        default=None,
        description=(
            "URL base para endpoints OpenAI-compatible. Variable: MCP_SO_OPENAI_BASE_URL."
        ),
    )
    openai_api_key: str | None = Field(
        default=None,
        description="API key para endpoints OpenAI-compatible. Variable: MCP_SO_OPENAI_API_KEY.",
    )

    def to_log_context(self) -> dict[str, Any]:
        base = super().to_log_context()
        base["aws_region"] = self.aws_region
        base["default_provider"] = self.default_provider
        base["default_model_id"] = self.default_model_id
        return base


settings = StructuredOutputSettings()
