"""
Configuración de mcp-orchestrator.

Variables de entorno con prefijo ORCH_.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class OrchestratorSettings(BaseMcpSettings):
    """
    Configuración del servidor MCP Orchestrator.

    Variables soportadas (prefijo ORCH_):
        ORCH_DAGS_PATH: Ruta al directorio donde se guardan los DAGs de Airflow u otros.
    """

    model_config = SettingsConfigDict(
        env_prefix="ORCH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    dags_path: Path = Field(
        default=Path("./dags"),
        description="Ruta donde se almacenan los archivos de DAGs.",
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update({"dags_path": str(self.dags_path)})
        return base


settings = OrchestratorSettings()
