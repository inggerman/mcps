"""
Configuración del servidor MCP Markdown.

Hereda la configuración base compartida y añade parámetros específicos
para el procesamiento de archivos Markdown.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración del servidor mcp-markdown.

    Parámetros cargados desde variables de entorno con prefijo MCP_MARKDOWN_.
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_MARKDOWN_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Servidor ---
    server_name: str = Field(
        default="mcp-markdown",
        description="Nombre del servidor MCP.",
    )
    server_version: str = Field(
        default="1.0.0",
        description="Versión del servidor.",
    )

    # --- Logging ---
    log_level: str = Field(
        default="INFO",
        description="Nivel de log: DEBUG | INFO | WARNING | ERROR.",
    )
    log_format: str = Field(
        default="json",
        description="Formato de log: json (producción) | console (desarrollo).",
    )

    # --- Markdown ---
    max_file_size_mb: float = Field(
        default=10.0,
        gt=0,
        description="Tamaño máximo permitido de archivo Markdown en MB.",
    )
    allowed_extensions: list[str] = Field(
        default=[".md", ".markdown", ".mdx", ".mdown", ".mkd"],
        description="Extensiones de archivo reconocidas como Markdown.",
    )
    default_max_toc_depth: int = Field(
        default=3,
        ge=1,
        le=6,
        description="Profundidad máxima por defecto para la tabla de contenidos.",
    )
    validate_external_links: bool = Field(
        default=False,
        description="Si True, valida que los enlaces externos respondan (requiere red).",
    )

    @property
    def max_file_size_bytes(self) -> int:
        """Tamaño máximo en bytes."""
        return int(self.max_file_size_mb * 1024 * 1024)

    def is_markdown_file(self, path: Path) -> bool:
        """Retorna True si la extensión del archivo es reconocida como Markdown."""
        return path.suffix.lower() in self.allowed_extensions


# Instancia singleton de configuración
settings = Settings()
