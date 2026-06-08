"""
Configuración base con pydantic-settings para todos los servidores MCP.

Proporciona la clase `BaseMcpSettings` que los servidores pueden extender
para añadir sus propias variables de entorno específicas. Soporta lectura
de archivos `.env` y variables de entorno del sistema operativo.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseMcpSettings(BaseSettings):
    """
    Configuración base compartida por todos los servidores MCP.

    Carga valores desde:
    1. Variables de entorno del sistema operativo (mayor prioridad).
    2. Archivo `.env` en el directorio de trabajo actual.
    3. Valores por defecto definidos en la clase (menor prioridad).

    Los servidores MCP deben heredar de esta clase y agregar sus propios
    campos de configuración específicos.

    Ejemplo de extensión:
        ```python
        class MyServerSettings(BaseMcpSettings):
            api_key: str = Field(..., description="API key del servicio externo.")
            max_retries: int = Field(default=3, ge=1)

            model_config = SettingsConfigDict(
                env_prefix="MY_SERVER_",
                env_file=".env",
                extra="ignore",
            )
        ```
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description=(
            "Nivel mínimo de log. "
            "Valores válidos: DEBUG, INFO, WARNING, ERROR, CRITICAL. "
            "Variable de entorno: LOG_LEVEL."
        ),
    )
    log_format: Literal["json", "console"] = Field(
        default="json",
        description=(
            "Formato de salida del log. "
            "'json' para producción (ELK, Datadog), 'console' para desarrollo. "
            "Variable de entorno: LOG_FORMAT."
        ),
    )

    # --- Servidor MCP ---
    mcp_host: str = Field(
        default="0.0.0.0",
        description=(
            "Dirección IP en la que el servidor MCP escuchará conexiones. "
            "Use '0.0.0.0' para todas las interfaces o '127.0.0.1' para solo localhost. "
            "Variable de entorno: MCP_HOST."
        ),
    )
    mcp_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description=(
            "Puerto TCP en el que el servidor MCP escuchará conexiones. "
            "Debe estar entre 1024 y 65535. "
            "Variable de entorno: MCP_PORT."
        ),
    )
    mcp_server_name: str = Field(
        default="mcp-server",
        description=(
            "Nombre identificador del servidor MCP. "
            "Se incluye en los logs y metadatos de respuesta. "
            "Variable de entorno: MCP_SERVER_NAME."
        ),
    )
    mcp_debug: bool = Field(
        default=False,
        description=(
            "Activa el modo de depuración del servidor. "
            "En modo debug se pueden exponer más detalles de errores internos. "
            "Variable de entorno: MCP_DEBUG."
        ),
    )
    mcp_workers: int = Field(
        default=1,
        ge=1,
        le=64,
        description=(
            "Número de workers del servidor MCP. "
            "Variable de entorno: MCP_WORKERS."
        ),
    )

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        """Normaliza el nivel de log a mayúsculas para validación consistente."""
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator("mcp_host", mode="before")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Valida que el host no esté vacío y elimina espacios en blanco."""
        v = v.strip()
        if not v:
            raise ValueError("mcp_host no puede ser una cadena vacía.")
        return v

    @property
    def server_address(self) -> str:
        """Retorna la dirección completa host:puerto del servidor."""
        return f"{self.mcp_host}:{self.mcp_port}"

    @property
    def is_debug(self) -> bool:
        """Retorna True si el servidor está en modo de depuración."""
        return self.mcp_debug

    def to_log_context(self) -> dict:
        """
        Retorna un diccionario con los campos relevantes para incluir en los logs.

        Se excluyen campos sensibles como claves de API o contraseñas.
        Los servidores derivados pueden sobreescribir este método para
        personalizar los campos expuestos en el contexto de log.

        Returns:
            Diccionario con nombre del servidor, host, puerto y nivel de log.
        """
        return {
            "server_name": self.mcp_server_name,
            "host": self.mcp_host,
            "port": self.mcp_port,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "debug": self.mcp_debug,
            "workers": self.mcp_workers,
        }
