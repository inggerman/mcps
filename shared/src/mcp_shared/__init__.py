"""
mcp_shared — Librería compartida para todos los servidores MCP del framework.

Exporta los componentes principales: modelos de respuesta estándar, jerarquía
de errores tipados, configuración de logging y clase base de configuración.

Uso típico en un servidor MCP:
    ```python
    from mcp_shared import (
        StandardResponse,
        ErrorCode,
        McpError,
        setup_logging,
        get_logger,
        BaseMcpSettings,
    )

    settings = BaseMcpSettings()
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)
    logger = get_logger(__name__)
    ```
"""

from mcp_shared.config import BaseMcpSettings
from mcp_shared.errors import (
    ApiAuthenticationError,
    ApiError,
    ApiRateLimitError,
    ErrorCode,
    FileNotFoundError,
    FilePermissionError,
    FileReadError,
    InvalidValueError,
    McpError,
    MissingFieldError,
    NetworkError,
    NetworkTimeoutError,
    ParseError,
    UnsupportedFormatError,
    ValidationError,
)
from mcp_shared.logging import get_logger, setup_logging
from mcp_shared.models import (
    BusinessDaysResult,
    ConversionResult,
    DocumentContent,
    DocumentMetadata,
    ExchangeRate,
    Holiday,
    ImageData,
    MarkdownCodeBlock,
    MarkdownDocument,
    MarkdownHeading,
    MarkdownLink,
    PromptAnalysis,
    StandardResponse,
    StandardTableResponse,
    TableData,
    TableRecord,
    TextStats,
    TokenEstimate,
)

__version__ = "1.0.0"
__author__ = "MCP Framework Team"

__all__ = [
    # Versión
    "__version__",
    # Configuración
    "BaseMcpSettings",
    # Errores y códigos
    "ErrorCode",
    "McpError",
    "FileNotFoundError",
    "FileReadError",
    "FilePermissionError",
    "UnsupportedFormatError",
    "ParseError",
    "NetworkError",
    "NetworkTimeoutError",
    "ApiError",
    "ApiRateLimitError",
    "ApiAuthenticationError",
    "ValidationError",
    "MissingFieldError",
    "InvalidValueError",
    # Logging
    "setup_logging",
    "get_logger",
    # Modelos — Respuestas estándar
    "StandardResponse",
    "TableRecord",
    "StandardTableResponse",
    # Modelos — Documentos
    "DocumentContent",
    "DocumentMetadata",
    "TableData",
    "ImageData",
    # Modelos — Calendario
    "Holiday",
    "BusinessDaysResult",
    # Modelos — Divisas
    "ExchangeRate",
    "ConversionResult",
    # Modelos — Markdown
    "MarkdownDocument",
    "MarkdownHeading",
    "MarkdownLink",
    "MarkdownCodeBlock",
    # Modelos — Análisis de texto
    "PromptAnalysis",
    "TokenEstimate",
    "TextStats",
]
