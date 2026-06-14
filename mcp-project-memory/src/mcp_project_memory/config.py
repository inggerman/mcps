"""
Configuración de mcp-project-memory.

Extiende BaseMcpSettings con variables para controlar la ubicación
y comportamiento del almacenamiento de memoria del proyecto.
Variables de entorno con prefijo MEMORY_ (ej: MEMORY_DIR=/ruta/.ai-memory).
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class MemorySettings(BaseMcpSettings):
    """
    Configuración del servidor MCP Project Memory.

    Variables de entorno soportadas (prefijo MEMORY_):
        MEMORY_DIR: Directorio donde se almacena el archivo de memoria.
        MEMORY_FILE: Nombre del archivo JSON de memoria.
        MEMORY_PROJECT_NAME: Nombre del proyecto para identificación.
        MEMORY_AUTO_SYNC: Si true, sincroniza con el filesystem al leer.
        MEMORY_PROJECT_ROOT: Raíz del proyecto para sincronización.
        MEMORY_MAX_SESSIONS: Máximo de sesiones a conservar en historial.

    Variables heredadas (sin prefijo):
        LOG_LEVEL, LOG_FORMAT, MCP_HOST, MCP_PORT, MCP_TRANSPORT
    """

    model_config = SettingsConfigDict(
        env_prefix="MEMORY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    memory_dir: Path = Field(
        default=Path(".ai-memory"),
        description=(
            "Directorio donde se almacena el archivo JSON de memoria del proyecto. "
            "Puede ser relativo al directorio de trabajo o absoluto. "
            "Variable de entorno: MEMORY_DIR."
        ),
    )

    memory_file: str = Field(
        default="project_memory.json",
        description=(
            "Nombre del archivo JSON que almacena la memoria del proyecto. "
            "Variable de entorno: MEMORY_FILE."
        ),
    )

    project_name: str = Field(
        default="mcps",
        description=(
            "Nombre del proyecto para identificación en los metadatos. "
            "Variable de entorno: MEMORY_PROJECT_NAME."
        ),
    )

    auto_sync: bool = Field(
        default=False,
        description=(
            "Si es true, sincroniza automáticamente el estado de componentes "
            "con el filesystem al leer el estado del proyecto. "
            "Variable de entorno: MEMORY_AUTO_SYNC."
        ),
    )

    project_root: Path = Field(
        default=Path(),
        description=(
            "Ruta raíz del proyecto para sincronización con el filesystem. "
            "Variable de entorno: MEMORY_PROJECT_ROOT."
        ),
    )

    max_sessions: int = Field(
        default=100,
        ge=10,
        le=10000,
        description=(
            "Número máximo de sesiones a conservar en el historial. "
            "Las más antiguas se eliminan al superar el límite. "
            "Variable de entorno: MEMORY_MAX_SESSIONS."
        ),
    )

    @property
    def memory_path(self) -> Path:
        """Retorna la ruta absoluta al archivo de memoria."""
        return self.memory_dir / self.memory_file

    def to_log_context(self) -> dict:
        """Extiende el contexto de log base con parámetros de memoria."""
        base = super().to_log_context()
        base.update(
            {
                "memory_dir": str(self.memory_dir),
                "project_name": self.project_name,
                "auto_sync": self.auto_sync,
            }
        )
        return base


settings = MemorySettings()
