"""
Excepciones tipadas para el framework MCP.

Define la jerarquía de errores que todos los servidores MCP deben utilizar,
junto con un enum de códigos de error estructurados para identificación programática.
"""

from __future__ import annotations

from enum import StrEnum


# ---------------------------------------------------------------------------
# Códigos de error
# ---------------------------------------------------------------------------


class ErrorCode(StrEnum):
    """
    Códigos de error estructurados para identificación programática.

    Todos los códigos siguen el patrón DOMINIO_DESCRIPCION en mayúsculas.
    Se recomienda incluir siempre el ErrorCode en la respuesta de error para
    facilitar el manejo de errores en el cliente.
    """

    # --- Errores de archivo y sistema de archivos ---
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    """El archivo solicitado no existe en la ruta especificada."""

    FILE_READ_ERROR = "FILE_READ_ERROR"
    """Error al leer el contenido del archivo."""

    FILE_WRITE_ERROR = "FILE_WRITE_ERROR"
    """Error al escribir o crear el archivo."""

    FILE_PERMISSION_DENIED = "FILE_PERMISSION_DENIED"
    """Permisos insuficientes para acceder al archivo."""

    DIRECTORY_NOT_FOUND = "DIRECTORY_NOT_FOUND"
    """El directorio especificado no existe."""

    # --- Errores de formato ---
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    """El formato del archivo o dato no está soportado."""

    ENCODING_ERROR = "ENCODING_ERROR"
    """Error al codificar o decodificar el contenido del archivo."""

    # --- Errores de parseo ---
    PARSE_ERROR = "PARSE_ERROR"
    """Error general al parsear el contenido del archivo o respuesta."""

    PARSE_JSON_ERROR = "PARSE_JSON_ERROR"
    """Error al parsear JSON inválido."""

    PARSE_XML_ERROR = "PARSE_XML_ERROR"
    """Error al parsear XML inválido."""

    PARSE_CSV_ERROR = "PARSE_CSV_ERROR"
    """Error al parsear CSV inválido."""

    PARSE_PDF_ERROR = "PARSE_PDF_ERROR"
    """Error al parsear o extraer contenido de un PDF."""

    # --- Errores de red y APIs externas ---
    NETWORK_ERROR = "NETWORK_ERROR"
    """Error genérico de red o conexión."""

    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    """La solicitud de red excedió el tiempo límite."""

    NETWORK_CONNECTION_REFUSED = "NETWORK_CONNECTION_REFUSED"
    """La conexión fue rechazada por el servidor remoto."""

    API_ERROR = "API_ERROR"
    """Error retornado por una API externa."""

    API_RATE_LIMIT = "API_RATE_LIMIT"
    """Se alcanzó el límite de solicitudes de la API externa."""

    API_AUTHENTICATION_ERROR = "API_AUTHENTICATION_ERROR"
    """Credenciales inválidas o faltantes para la API externa."""

    API_NOT_FOUND = "API_NOT_FOUND"
    """El recurso solicitado no existe en la API externa (404)."""

    # --- Errores de validación ---
    VALIDATION_ERROR = "VALIDATION_ERROR"
    """Error general de validación de datos de entrada."""

    VALIDATION_MISSING_FIELD = "VALIDATION_MISSING_FIELD"
    """Falta un campo requerido en los datos de entrada."""

    VALIDATION_INVALID_VALUE = "VALIDATION_INVALID_VALUE"
    """Un campo contiene un valor fuera del rango o tipo esperado."""

    VALIDATION_INVALID_DATE = "VALIDATION_INVALID_DATE"
    """La fecha proporcionada tiene un formato inválido o es incoherente."""

    VALIDATION_INVALID_CURRENCY = "VALIDATION_INVALID_CURRENCY"
    """El código de divisa no es un código ISO 4217 válido."""

    # --- Errores internos ---
    INTERNAL_ERROR = "INTERNAL_ERROR"
    """Error interno inesperado del servidor MCP."""

    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    """La funcionalidad solicitada no ha sido implementada."""

    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    """Error en la configuración del servidor MCP."""


# ---------------------------------------------------------------------------
# Excepción base
# ---------------------------------------------------------------------------


class McpError(Exception):
    """
    Excepción base para todos los errores del framework MCP.

    Todas las excepciones específicas deben heredar de esta clase.
    Proporciona un código de error estructurado y contexto adicional.

    Atributos:
        message: Descripción legible del error.
        error_code: Código de error del enum ErrorCode.
        context: Diccionario con información adicional del contexto del error.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        context: dict | None = None,
    ) -> None:
        """
        Inicializa el error MCP con mensaje, código y contexto.

        Args:
            message: Descripción legible del error.
            error_code: Código de error estructurado. Por defecto INTERNAL_ERROR.
            context: Información adicional sobre el contexto del error.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context: dict = context or {}

    def __repr__(self) -> str:
        """Representación detallada del error para depuración."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"context={self.context!r})"
        )

    def __str__(self) -> str:
        """Representación de cadena legible del error."""
        return f"[{self.error_code}] {self.message}"


# ---------------------------------------------------------------------------
# Excepciones de archivo y sistema de archivos
# ---------------------------------------------------------------------------


class FileNotFoundError(McpError):
    """
    Error que indica que el archivo solicitado no fue encontrado.

    Se lanza cuando una ruta de archivo no existe en el sistema de archivos.
    """

    def __init__(self, file_path: str, context: dict | None = None) -> None:
        """
        Inicializa el error con la ruta del archivo no encontrado.

        Args:
            file_path: Ruta del archivo que no fue encontrado.
            context: Información adicional del contexto.
        """
        super().__init__(
            message=f"Archivo no encontrado: '{file_path}'",
            error_code=ErrorCode.FILE_NOT_FOUND,
            context={"file_path": file_path, **(context or {})},
        )
        self.file_path = file_path


class FileReadError(McpError):
    """
    Error al leer el contenido de un archivo.

    Se lanza cuando el archivo existe pero no puede ser leído correctamente.
    """

    def __init__(self, file_path: str, reason: str = "", context: dict | None = None) -> None:
        """
        Inicializa el error con la ruta y el motivo del fallo de lectura.

        Args:
            file_path: Ruta del archivo que no pudo ser leído.
            reason: Descripción del motivo del error de lectura.
            context: Información adicional del contexto.
        """
        message = f"Error al leer el archivo '{file_path}'"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            error_code=ErrorCode.FILE_READ_ERROR,
            context={"file_path": file_path, "reason": reason, **(context or {})},
        )
        self.file_path = file_path
        self.reason = reason


class FilePermissionError(McpError):
    """
    Error de permisos insuficientes para acceder a un archivo.

    Se lanza cuando la operación es rechazada por el sistema operativo.
    """

    def __init__(self, file_path: str, operation: str = "acceder", context: dict | None = None) -> None:
        """
        Inicializa el error con la ruta del archivo y la operación denegada.

        Args:
            file_path: Ruta del archivo con permisos insuficientes.
            operation: Operación denegada ('leer', 'escribir', 'acceder', etc.).
            context: Información adicional del contexto.
        """
        super().__init__(
            message=f"Permiso denegado para {operation} el archivo '{file_path}'",
            error_code=ErrorCode.FILE_PERMISSION_DENIED,
            context={"file_path": file_path, "operation": operation, **(context or {})},
        )
        self.file_path = file_path
        self.operation = operation


# ---------------------------------------------------------------------------
# Excepciones de formato
# ---------------------------------------------------------------------------


class UnsupportedFormatError(McpError):
    """
    Error que indica que el formato del archivo o dato no está soportado.

    Se lanza cuando se intenta procesar un tipo de archivo no reconocido.
    """

    def __init__(
        self,
        format_name: str,
        supported_formats: list[str] | None = None,
        context: dict | None = None,
    ) -> None:
        """
        Inicializa el error con el formato no soportado y la lista de formatos válidos.

        Args:
            format_name: Nombre o extensión del formato no soportado.
            supported_formats: Lista de formatos soportados por la herramienta.
            context: Información adicional del contexto.
        """
        message = f"Formato no soportado: '{format_name}'"
        if supported_formats:
            message += f". Formatos válidos: {', '.join(supported_formats)}"
        super().__init__(
            message=message,
            error_code=ErrorCode.UNSUPPORTED_FORMAT,
            context={
                "format_name": format_name,
                "supported_formats": supported_formats or [],
                **(context or {}),
            },
        )
        self.format_name = format_name
        self.supported_formats = supported_formats or []


# ---------------------------------------------------------------------------
# Excepciones de parseo
# ---------------------------------------------------------------------------


class ParseError(McpError):
    """
    Error al parsear el contenido de un archivo o respuesta.

    Se lanza cuando el contenido no puede ser interpretado correctamente.
    """

    def __init__(
        self,
        source: str,
        reason: str = "",
        line: int | None = None,
        column: int | None = None,
        context: dict | None = None,
    ) -> None:
        """
        Inicializa el error con la fuente y detalles de posición si están disponibles.

        Args:
            source: Nombre del archivo o descripción del origen del contenido.
            reason: Descripción del motivo del error de parseo.
            line: Línea donde ocurrió el error (si aplica).
            column: Columna donde ocurrió el error (si aplica).
            context: Información adicional del contexto.
        """
        message = f"Error al parsear '{source}'"
        if reason:
            message += f": {reason}"
        if line is not None:
            message += f" (línea {line}"
            if column is not None:
                message += f", columna {column}"
            message += ")"
        super().__init__(
            message=message,
            error_code=ErrorCode.PARSE_ERROR,
            context={
                "source": source,
                "reason": reason,
                "line": line,
                "column": column,
                **(context or {}),
            },
        )
        self.source = source
        self.reason = reason
        self.line = line
        self.column = column


# ---------------------------------------------------------------------------
# Excepciones de red y APIs
# ---------------------------------------------------------------------------


class NetworkError(McpError):
    """
    Error de red o comunicación con servicios externos.

    Clase base para errores relacionados con solicitudes HTTP o APIs.
    """

    def __init__(
        self,
        url: str,
        reason: str = "",
        status_code: int | None = None,
        context: dict | None = None,
    ) -> None:
        """
        Inicializa el error de red con la URL y el motivo del fallo.

        Args:
            url: URL o endpoint que causó el error.
            reason: Descripción del motivo del error de red.
            status_code: Código de respuesta HTTP si está disponible.
            context: Información adicional del contexto.
        """
        message = f"Error de red al contactar '{url}'"
        if status_code is not None:
            message += f" (HTTP {status_code})"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            error_code=ErrorCode.NETWORK_ERROR,
            context={
                "url": url,
                "reason": reason,
                "status_code": status_code,
                **(context or {}),
            },
        )
        self.url = url
        self.reason = reason
        self.status_code = status_code


class NetworkTimeoutError(NetworkError):
    """
    Error que indica que la solicitud de red excedió el tiempo límite.

    Se lanza cuando una operación de red no responde dentro del tiempo configurado.
    """

    def __init__(self, url: str, timeout_seconds: float | None = None, context: dict | None = None) -> None:
        """
        Inicializa el error de timeout con la URL y el tiempo límite.

        Args:
            url: URL que excedió el tiempo límite.
            timeout_seconds: Tiempo límite configurado en segundos.
            context: Información adicional del contexto.
        """
        reason = f"timeout después de {timeout_seconds}s" if timeout_seconds is not None else "timeout"
        super().__init__(url=url, reason=reason, context=context)
        self.error_code = ErrorCode.NETWORK_TIMEOUT
        self.timeout_seconds = timeout_seconds


class ApiError(NetworkError):
    """
    Error retornado por una API externa.

    Se lanza cuando la API responde con un código de error (4xx o 5xx).
    """

    def __init__(
        self,
        url: str,
        status_code: int,
        response_body: str = "",
        context: dict | None = None,
    ) -> None:
        """
        Inicializa el error de API con el código de estado y cuerpo de respuesta.

        Args:
            url: URL del endpoint que retornó el error.
            status_code: Código de respuesta HTTP (ej: 400, 401, 404, 500).
            response_body: Cuerpo de la respuesta de error de la API.
            context: Información adicional del contexto.
        """
        reason = f"respuesta de error de la API"
        if response_body:
            reason += f": {response_body[:200]}"  # Limitar a 200 chars
        super().__init__(url=url, reason=reason, status_code=status_code, context=context)
        self.error_code = ErrorCode.API_ERROR
        self.response_body = response_body


class ApiRateLimitError(ApiError):
    """
    Error que indica que se alcanzó el límite de solicitudes de la API.

    Se lanza típicamente al recibir HTTP 429 Too Many Requests.
    """

    def __init__(
        self,
        url: str,
        retry_after_seconds: float | None = None,
        context: dict | None = None,
    ) -> None:
        """
        Inicializa el error de rate limit con el tiempo de espera sugerido.

        Args:
            url: URL de la API que retornó el rate limit.
            retry_after_seconds: Segundos a esperar antes de reintentar (del header Retry-After).
            context: Información adicional del contexto.
        """
        super().__init__(url=url, status_code=429, context=context)
        self.error_code = ErrorCode.API_RATE_LIMIT
        self.retry_after_seconds = retry_after_seconds
        if retry_after_seconds is not None:
            self.message += f". Reintentar después de {retry_after_seconds}s"


class ApiAuthenticationError(ApiError):
    """
    Error de autenticación con una API externa.

    Se lanza cuando la API rechaza las credenciales (401 Unauthorized o 403 Forbidden).
    """

    def __init__(self, url: str, context: dict | None = None) -> None:
        """
        Inicializa el error de autenticación.

        Args:
            url: URL de la API que rechazó la autenticación.
            context: Información adicional del contexto.
        """
        super().__init__(
            url=url,
            status_code=401,
            response_body="Autenticación rechazada. Verifique las credenciales configuradas.",
            context=context,
        )
        self.error_code = ErrorCode.API_AUTHENTICATION_ERROR


# ---------------------------------------------------------------------------
# Excepciones de validación
# ---------------------------------------------------------------------------


class ValidationError(McpError):
    """
    Error de validación de datos de entrada.

    Se lanza cuando los parámetros de una herramienta MCP son inválidos
    o no cumplen las restricciones esperadas.
    """

    def __init__(
        self,
        field: str,
        message: str,
        value: object = None,
        context: dict | None = None,
    ) -> None:
        """
        Inicializa el error de validación con el campo y mensaje descriptivo.

        Args:
            field: Nombre del campo o parámetro que falló la validación.
            message: Descripción del problema de validación.
            value: Valor que causó el error de validación.
            context: Información adicional del contexto.
        """
        full_message = f"Error de validación en '{field}': {message}"
        super().__init__(
            message=full_message,
            error_code=ErrorCode.VALIDATION_ERROR,
            context={"field": field, "value": repr(value), **(context or {})},
        )
        self.field = field
        self.value = value


class MissingFieldError(ValidationError):
    """
    Error que indica que falta un campo requerido en los datos de entrada.

    Especialización de ValidationError para campos obligatorios ausentes.
    """

    def __init__(self, field: str, context: dict | None = None) -> None:
        """
        Inicializa el error de campo faltante.

        Args:
            field: Nombre del campo requerido que no fue proporcionado.
            context: Información adicional del contexto.
        """
        super().__init__(
            field=field,
            message="Campo requerido no proporcionado",
            context=context,
        )
        self.error_code = ErrorCode.VALIDATION_MISSING_FIELD


class InvalidValueError(ValidationError):
    """
    Error que indica que un campo contiene un valor inválido.

    Se lanza cuando el valor no pertenece al rango, tipo o conjunto de valores válidos.
    """

    def __init__(
        self,
        field: str,
        value: object,
        reason: str = "",
        context: dict | None = None,
    ) -> None:
        """
        Inicializa el error de valor inválido con el campo, valor y motivo.

        Args:
            field: Nombre del campo con el valor inválido.
            value: Valor inválido recibido.
            reason: Descripción del motivo por el que el valor no es válido.
            context: Información adicional del contexto.
        """
        message = reason or f"Valor no permitido: {value!r}"
        super().__init__(field=field, message=message, value=value, context=context)
        self.error_code = ErrorCode.VALIDATION_INVALID_VALUE
        self.reason = reason
