"""
Configuración específica de mcp-tabular.

Extiende BaseMcpSettings con variables de entorno propias del servidor tabular.
Las variables se cargan desde el archivo .env o del entorno del sistema operativo
con el prefijo TABULAR_ (ej: TABULAR_MAX_ROWS_PREVIEW=500).
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from mcp_shared.config import BaseMcpSettings


class TabularSettings(BaseMcpSettings):
    """
    Configuración del servidor MCP Tabular.

    Hereda la configuración base (logging, host, puerto) y agrega opciones
    específicas para el procesamiento de archivos tabulares.

    Variables de entorno soportadas (prefijo TABULAR_):
        TABULAR_MAX_ROWS_PREVIEW: Máximo de filas en respuesta sin paginación.
        TABULAR_MAX_FILE_SIZE_MB: Tamaño máximo de archivo permitido en MB.
        TABULAR_DEFAULT_ENCODING: Encoding por defecto para archivos de texto.
        TABULAR_SAMPLE_VALUES_COUNT: Cantidad de valores de muestra por columna.

    Variables heredadas (sin prefijo):
        LOG_LEVEL, LOG_FORMAT, MCP_HOST, MCP_PORT, MCP_SERVER_NAME, MCP_DEBUG
    """

    model_config = SettingsConfigDict(
        env_prefix="TABULAR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    max_rows_preview: int = Field(
        default=1000,
        ge=1,
        le=100_000,
        description=(
            "Máximo de filas retornadas en una respuesta sin paginación. "
            "Si el archivo tiene más filas, se trunca y se indica en 'truncated'. "
            "Variable de entorno: TABULAR_MAX_ROWS_PREVIEW."
        ),
    )

    max_file_size_mb: int = Field(
        default=100,
        ge=1,
        le=2048,
        description=(
            "Tamaño máximo permitido de archivo en MB. "
            "Archivos más grandes serán rechazados con un error descriptivo. "
            "Variable de entorno: TABULAR_MAX_FILE_SIZE_MB."
        ),
    )

    default_encoding: str = Field(
        default="utf-8",
        description=(
            "Encoding por defecto para archivos CSV y TSV cuando no se puede detectar "
            "automáticamente con chardet. Ejemplos: 'utf-8', 'latin-1', 'cp1252'. "
            "Variable de entorno: TABULAR_DEFAULT_ENCODING."
        ),
    )

    sample_values_count: int = Field(
        default=5,
        ge=1,
        le=50,
        description=(
            "Número de valores de muestra a incluir por columna en la respuesta. "
            "Variable de entorno: TABULAR_SAMPLE_VALUES_COUNT."
        ),
    )

    chardet_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description=(
            "Umbral mínimo de confianza para aceptar la detección de encoding con chardet. "
            "Si la confianza es menor, se usa default_encoding. "
            "Variable de entorno: TABULAR_CHARDET_CONFIDENCE_THRESHOLD."
        ),
    )

    @property
    def max_file_size_bytes(self) -> int:
        """Retorna el tamaño máximo de archivo en bytes."""
        return self.max_file_size_mb * 1024 * 1024

    def to_log_context(self) -> dict:
        """Extiende el contexto de log base con parámetros tabulares."""
        base = super().to_log_context()
        base.update(
            {
                "max_rows_preview": self.max_rows_preview,
                "max_file_size_mb": self.max_file_size_mb,
                "default_encoding": self.default_encoding,
            }
        )
        return base
