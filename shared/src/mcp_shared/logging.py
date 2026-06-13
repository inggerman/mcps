"""
Configuración production-grade de structlog para el framework MCP.

Proporciona logging estructurado con soporte para formato JSON (producción)
y formato colorido con rich (desarrollo). Incluye contexto automático de
timestamp ISO 8601, nivel de log y nombre del servidor.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Literal

import structlog
from structlog.types import EventDict, Processor

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["json", "console"]


# ---------------------------------------------------------------------------
# Processors personalizados
# ---------------------------------------------------------------------------


def _add_server_context(
    logger: Any,
    method: str,
    event_dict: EventDict,
) -> EventDict:
    """
    Processor de structlog que agrega el contexto del servidor MCP al log.

    Añade 'server_name' si está configurado en el contexto de structlog.

    Args:
        logger: Logger de structlog (no utilizado directamente).
        method: Nombre del método de log ('info', 'error', etc.).
        event_dict: Diccionario del evento de log actual.

    Returns:
        EventDict enriquecido con el contexto del servidor.
    """
    # El server_name se inyecta vía structlog.contextvars.bind_contextvars()
    return event_dict


def _drop_color_message_key(
    logger: Any,
    method: str,
    event_dict: EventDict,
) -> EventDict:
    """
    Processor que elimina la clave '_record' si está presente.

    Necesario para evitar duplicación de datos al usar el LogRecordProxy
    de la integración con el módulo logging estándar de Python.

    Args:
        logger: Logger de structlog.
        method: Nombre del método de log.
        event_dict: Diccionario del evento de log actual.

    Returns:
        EventDict sin la clave '_record' redundante.
    """
    event_dict.pop("color_message", None)
    return event_dict


# ---------------------------------------------------------------------------
# Configuración principal
# ---------------------------------------------------------------------------


def setup_logging(
    log_level: LogLevel = "INFO",
    log_format: LogFormat = "json",
    server_name: str | None = None,
) -> None:
    """
    Configura structlog para uso production-grade en servidores MCP.

    En formato 'json' se producen logs estructurados compatibles con
    sistemas de agregación como Datadog, ELK o Cloud Logging. En formato
    'console' se usa una salida colorida con rich, ideal para desarrollo.

    Esta función debe llamarse una sola vez al inicio del servidor MCP,
    antes de cualquier operación de logging.

    Args:
        log_level: Nivel mínimo de log a registrar. Por defecto 'INFO'.
        log_format: Formato de salida. 'json' para producción, 'console' para desarrollo.
        server_name: Nombre del servidor MCP para incluir en todos los logs.
                     Se agrega automáticamente a cada evento como 'server_name'.

    Ejemplo:
        >>> setup_logging(log_level="DEBUG", log_format="console", server_name="file-processor")
    """
    # Normalizar nivel de log
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Processors compartidos para procesamiento de logs del módulo logging estándar
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        _drop_color_message_key,
    ]

    if log_format == "json":
        # Formato JSON para producción
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
        )
    else:
        # Formato colorido para desarrollo
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
        )

    # Configurar el handler raíz de Python logging estándar
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Vincular el nombre del servidor al contexto global si se proporcionó
    if server_name:
        structlog.contextvars.bind_contextvars(server_name=server_name)

    # Silenciar loggers ruidosos de terceros
    for noisy_logger in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Fábrica de loggers
# ---------------------------------------------------------------------------


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Obtiene un logger structlog vinculado al nombre especificado.

    El logger retornado hereda la configuración establecida por `setup_logging`.
    Si `setup_logging` no fue llamado antes, los logs se emiten con la
    configuración por defecto de structlog.

    Args:
        name: Nombre del logger, típicamente __name__ del módulo llamante.
              Se usará como valor de 'logger' en los eventos de log.

    Returns:
        Logger de structlog configurado y listo para usar.

    Ejemplo:
        >>> logger = get_logger(__name__)
        >>> logger.info("Servidor iniciado", port=8000)
        >>> logger.error("Error al procesar archivo", file="doc.pdf", exc_info=True)
    """
    return structlog.get_logger(name)
