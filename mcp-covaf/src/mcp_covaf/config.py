"""
Configuración de mcp-covaf.
"""

from __future__ import annotations

from pathlib import Path

from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict


class CovafSettings(BaseMcpSettings):
    """Configuración del servidor MCP COVAF."""

    model_config = SettingsConfigDict(
        env_prefix="COVAF_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    workspace_path: Path = Field(
        default=Path("/workspace"),
        description="Ruta raíz del workspace engineering (donde vive covaf/).",
    )

    java_back_path: Path = Field(
        default=Path("covaf/CovafDataRefineryBack"),
        description="Ruta relativa al motor Java (Cartas + Oficios PLD).",
    )

    python_api_path: Path = Field(
        default=Path("covaf/IA_IMPL_COVAF/datarefineryia-api"),
        description="Ruta relativa al motor Python (DataRefineryIA).",
    )

    frontend_path: Path = Field(
        default=Path("covaf/CovafAlternativosFront"),
        description="Ruta relativa al frontend Vue (Alternativos).",
    )

    derechos_path: Path = Field(
        default=Path("covaf/ServicioDerechos"),
        description="Ruta relativa al servicio Derechos.",
    )

    docs_path: Path = Field(
        default=Path("docs/projects/covaf"),
        description="Ruta relativa a la documentación canónica COVAF.",
    )

    def to_log_context(self) -> dict:
        base = super().to_log_context()
        base.update({
            "workspace_path": str(self.workspace_path),
            "java_back": str(self.java_back_path),
            "python_api": str(self.python_api_path),
            "frontend": str(self.frontend_path),
        })
        return base


settings = CovafSettings()
