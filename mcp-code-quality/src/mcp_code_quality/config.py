"""
Configuración de mcp-code-quality.

Variables de entorno con prefijo CQ_.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class CodeQualitySettings(BaseMcpSettings):
    """
    Configuración del servidor MCP Code Quality.

    Variables soportadas (prefijo CQ_):
        CQ_PROJECT_PATH: Ruta al proyecto a analizar.
        CQ_LINTER_CMD: Comando base para linting (ej. "uv run ruff check").
        CQ_FORMATTER_CMD: Comando base para formateo (ej. "uv run ruff format").
        CQ_TEST_CMD: Comando base para testing (ej. "uv run pytest").
    """

    model_config = SettingsConfigDict(
        env_prefix="CQ_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    project_path: Path = Field(
        default=Path(),
        description="Ruta base del proyecto a analizar.",
    )

    linter_cmd: str = Field(
        default="uv run ruff check",
        description="Comando usado para linting de código.",
    )

    formatter_cmd: str = Field(
        default="uv run ruff format",
        description="Comando usado para formateo de código.",
    )

    test_cmd: str = Field(
        default="uv run pytest",
        description="Comando usado para correr tests unitarios.",
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update(
            {
                "project_path": str(self.project_path),
                "linter": self.linter_cmd,
            }
        )
        return base


settings = CodeQualitySettings()
