"""Configuración del servidor MCP Documentation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from mcp_shared.config import BaseMcpSettings


class DocumentationSettings(BaseMcpSettings):
    """
    Configuración del servidor MCP Documentation.

    Variables de entorno soportadas (prefijo DOC_):
        DOC_ROOT_PATH: Ruta base canónica para documentación (default: C:/mcp-doc/).
        DOC_INDEX_PATH: Ruta para índice de búsqueda FTS (default: <root>/.index).
        DOC_MAX_FILE_SIZE_MB: Tamaño máximo de archivo en MB (default: 20).
        DOC_ALLOWED_EXTENSIONS: Extensiones permitidas separadas por coma.
        DOC_AUTO_CLASSIFY: Auto-clasificar documentos al crear (default: true).
        DOC_CUSTOM_CATEGORIES_PATH: Ruta a archivo de categorías custom.

    Variables heredadas (sin prefijo):
        LOG_LEVEL, LOG_FORMAT, MCP_HOST, MCP_PORT, MCP_TRANSPORT
    """

    model_config = SettingsConfigDict(
        env_prefix="DOC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    root_path: Path = Field(
        default=Path("C:/mcp-doc/"),
        description=(
            "Ruta base canónica para toda la documentación. "
            "Variable de entorno: DOC_ROOT_PATH."
        ),
    )

    index_path: Path | None = Field(
        default=None,
        description=(
            "Ruta para el índice de búsqueda full-text. "
            "Por defecto usa <root_path>/.index. "
            "Variable de entorno: DOC_INDEX_PATH."
        ),
    )

    max_file_size_mb: int = Field(
        default=20,
        ge=1,
        le=500,
        description=(
            "Tamaño máximo de archivo en MB. "
            "Variable de entorno: DOC_MAX_FILE_SIZE_MB."
        ),
    )

    allowed_extensions: str = Field(
        default=".md,.yaml,.yml,.xml,.txt,.json,.docx,.pdf,.mmd,.puml",
        description=(
            "Extensiones permitidas separadas por coma. "
            "Variable de entorno: DOC_ALLOWED_EXTENSIONS."
        ),
    )

    auto_classify: bool = Field(
        default=True,
        description=(
            "Auto-clasificar documentos al crear. "
            "Variable de entorno: DOC_AUTO_CLASSIFY."
        ),
    )

    custom_categories_path: Path | None = Field(
        default=None,
        description=(
            "Ruta a archivo JSON con categorías custom. "
            "Variable de entorno: DOC_CUSTOM_CATEGORIES_PATH."
        ),
    )

    def to_log_context(self) -> dict[str, Any]:
        """Extiende el contexto de log base con parámetros de Documentation."""
        base = super().to_log_context()
        base.update(
            {
                "root_path": str(self.root_path),
                "index_path": str(self.index_path) if self.index_path else None,
                "max_file_size_mb": self.max_file_size_mb,
                "auto_classify": self.auto_classify,
            }
        )
        return base

    @property
    def resolved_index_path(self) -> Path:
        """Retorna la ruta efectiva del índice."""
        if self.index_path is not None:
            return self.index_path
        return self.root_path / ".index"

    @property
    def extensions_list(self) -> list[str]:
        """Retorna la lista de extensiones permitidas."""
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",") if ext.strip()]

    def is_allowed_extension(self, path: Path) -> bool:
        """Verifica si un archivo tiene una extensión permitida."""
        return path.suffix.lower() in self.extensions_list

    @property
    def resolved_custom_categories_path(self) -> Path:
        """Retorna la ruta efectiva del archivo de categorías custom."""
        if self.custom_categories_path is not None:
            return self.custom_categories_path
        return self.root_path / ".categories.json"
