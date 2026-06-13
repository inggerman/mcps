# Referencia de `mcp_shared` — Librería compartida

**Paquete:** `mcp_shared`  
**Ubicación:** `shared/src/mcp_shared/`  
**Instalación:** automática via workspace uv — todos los servidores lo tienen disponible

---

## Módulos disponibles

| Módulo | Qué exporta |
|--------|-------------|
| `mcp_shared.config` | `BaseMcpSettings` |
| `mcp_shared.errors` | `ErrorCode`, `McpError` y 12 subclases |
| `mcp_shared.logging` | `setup_logging()`, `get_logger()` |
| `mcp_shared.models` | Modelos Pydantic reutilizables |

---

## `mcp_shared.config` — BaseMcpSettings

### Clase `BaseMcpSettings`

Base para la configuración de todos los servidores. Hereda de `pydantic_settings.BaseSettings`.

**Sin prefijo de entorno** (lee las variables directamente).

```python
from mcp_shared.config import BaseMcpSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

class MiSettings(BaseMcpSettings):
    model_config = SettingsConfigDict(
        env_prefix="MI_SERVIDOR_",
        env_file=".env",
        extra="ignore",
    )

    mi_variable: str = Field(default="valor", description="...")

settings = MiSettings()
```

### Campos de `BaseMcpSettings`

| Campo | Tipo | Default | Variable de entorno | Descripción |
|-------|------|---------|---------------------|-------------|
| `log_level` | `Literal["DEBUG","INFO","WARNING","ERROR","CRITICAL"]` | `"INFO"` | `LOG_LEVEL` | Nivel de logging |
| `log_format` | `Literal["json","console"]` | `"json"` | `LOG_FORMAT` | Formato de salida |
| `mcp_host` | `str` | `"0.0.0.0"` | `MCP_HOST` | Host HTTP |
| `mcp_port` | `int` | `8000` | `MCP_PORT` | Puerto HTTP (1024-65535) |
| `mcp_server_name` | `str` | `"mcp-server"` | `MCP_SERVER_NAME` | Nombre en logs |
| `mcp_debug` | `bool` | `False` | `MCP_DEBUG` | Modo debug |
| `mcp_workers` | `int` | `1` | `MCP_WORKERS` | Workers (1-64) |
| `mcp_transport` | `Literal["stdio","streamable-http"]` | `"stdio"` | `MCP_TRANSPORT` | Modo de transporte |

### Propiedades y métodos

```python
settings.server_address     # → "0.0.0.0:8000"  (host:port)
settings.is_debug           # → bool
settings.to_log_context()   # → dict con todos los campos relevantes para logging
```

### Validator de `log_level`

`log_level` se normaliza a mayúsculas automáticamente: `"info"` → `"INFO"`.

### Validator de `mcp_host`

Rechaza strings vacíos. Elimina espacios en blanco.

---

## `mcp_shared.errors` — Jerarquía de errores

### `ErrorCode` (StrEnum)

Enum con todos los códigos de error estructurados. Usar en el campo `code` al construir errores.

```python
from mcp_shared.errors import ErrorCode

ErrorCode.FILE_NOT_FOUND           # "FILE_NOT_FOUND"
ErrorCode.FILE_READ_ERROR          # "FILE_READ_ERROR"
ErrorCode.FILE_WRITE_ERROR         # "FILE_WRITE_ERROR"
ErrorCode.FILE_PERMISSION_DENIED   # "FILE_PERMISSION_DENIED"
ErrorCode.DIRECTORY_NOT_FOUND      # "DIRECTORY_NOT_FOUND"
ErrorCode.UNSUPPORTED_FORMAT       # "UNSUPPORTED_FORMAT"
ErrorCode.ENCODING_ERROR           # "ENCODING_ERROR"
ErrorCode.PARSE_ERROR              # "PARSE_ERROR"
ErrorCode.PARSE_JSON_ERROR         # "PARSE_JSON_ERROR"
ErrorCode.PARSE_XML_ERROR          # "PARSE_XML_ERROR"
ErrorCode.PARSE_CSV_ERROR          # "PARSE_CSV_ERROR"
ErrorCode.PARSE_PDF_ERROR          # "PARSE_PDF_ERROR"
ErrorCode.NETWORK_ERROR            # "NETWORK_ERROR"
ErrorCode.NETWORK_TIMEOUT          # "NETWORK_TIMEOUT"
ErrorCode.NETWORK_CONNECTION_REFUSED # "NETWORK_CONNECTION_REFUSED"
ErrorCode.API_ERROR                # "API_ERROR"
ErrorCode.API_RATE_LIMIT           # "API_RATE_LIMIT"
# ... y más (ver errors.py para la lista completa)
```

### Jerarquía de clases de excepción

```
Exception
└── McpError  (base — todos los errores del framework)
    ├── ValidationError      → parámetro inválido o faltante
    ├── NotFoundError        → recurso no encontrado (archivo, hoja, etc.)
    ├── InvalidValueError    → valor fuera de rango permitido
    ├── UnsupportedFormatError → formato no soportado
    ├── FileTooLargeError    → archivo supera el límite configurado
    ├── ParseError           → error al parsear contenido
    ├── NetworkError         → error genérico de red
    │   ├── NetworkTimeoutError → timeout de red
    │   └── ConnectionRefusedError → conexión rechazada
    └── ApiError             → error de API externa
        └── ApiRateLimitError → rate limit de API
```

### Uso en la capa `tools/*.py`

```python
from mcp_shared.errors import (
    NotFoundError,
    ValidationError,
    InvalidValueError,
    UnsupportedFormatError,
    FileTooLargeError,
    ParseError,
    NetworkError,
    NetworkTimeoutError,
    ApiError,
)

# Archivo no encontrado
raise NotFoundError(resource="archivo", identifier="/data/ventas.xlsx")

# Parámetro inválido
raise ValidationError(field="operator", message="Operador 'xyz' no soportado.")

# Valor fuera de rango
raise InvalidValueError(field="limit", value=limit, min_value=1, max_value=1000)

# Formato no soportado
raise UnsupportedFormatError(format=".pdf", supported=[".xlsx", ".csv"])

# Archivo demasiado grande
raise FileTooLargeError(file_path=path, size_mb=actual_mb, limit_mb=max_mb)

# Error de red con timeout
raise NetworkTimeoutError(url="https://api.frankfurter.app/...", timeout_seconds=30)

# Error de API externa
raise ApiError(api_name="frankfurter", status_code=503, message="Service unavailable")
```

### Conversión a `SdkMcpError` — solo en `server.py`

```python
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError

try:
    result = mi_tool(param)
except McpError as exc:
    # exc.code tiene el ErrorCode, exc.message el mensaje legible
    raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))
except Exception as exc:
    raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor."))
```

---

## `mcp_shared.logging` — Logging estructurado

### `setup_logging()`

Configura structlog globalmente. **Llamar UNA sola vez al inicio de `server.py`**, antes de crear la instancia de `FastMCP`.

```python
from mcp_shared.logging import setup_logging

setup_logging(
    log_level="INFO",          # o settings.log_level
    log_format="console",      # "json" (prod) | "console" (dev, colorido)
    server_name="mcp-tabular", # se agrega automáticamente a todos los logs
)
```

| `log_format` | Salida | Usar en |
|---|---|---|
| `"console"` | Colorido, legible por humanos (usando rich) | Desarrollo local |
| `"json"` | Una línea JSON por evento | Producción (ELK, Datadog, CloudWatch) |

**Ejemplo de salida JSON:**
```json
{"timestamp": "2026-06-08T12:00:00Z", "level": "info", "server_name": "mcp-tabular", "event": "Leyendo archivo", "path": "/data/ventas.xlsx", "rows": 1500}
```

### `get_logger()`

```python
from mcp_shared.logging import get_logger

logger = get_logger(__name__)

# Uso con contexto estructurado (siempre key=value, nunca string formateado)
logger.debug("Iniciando lectura", path=path, encoding=encoding)
logger.info("Archivo leído", path=path, rows=len(data), columns=len(headers))
logger.warning("Archivo truncado", path=path, original_rows=total, returned_rows=limit)
logger.error("Error de red", url=url, status_code=503, retry=2)
logger.exception("Error inesperado", exc_info=exc)  # incluye stack trace
```

### Contexto de structlog

En el `lifespan` de cada servidor se llama a `bind_contextvars` para que todos los logs del servidor incluyan automáticamente el nombre:

```python
import structlog

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-tabular")
    yield
    structlog.contextvars.clear_contextvars()
```

---

## `mcp_shared.models` — Modelos Pydantic

Contiene modelos de dominio reutilizables entre servidores. Ver `shared/src/mcp_shared/models.py` para la lista actualizada — estos modelos se agregan según las necesidades del proyecto.

---

## Importaciones de referencia rápida

```python
# Configuración
from mcp_shared.config import BaseMcpSettings

# Errores (en tools/*.py)
from mcp_shared.errors import (
    McpError,
    ValidationError,
    NotFoundError,
    InvalidValueError,
    UnsupportedFormatError,
    FileTooLargeError,
    ParseError,
    NetworkError,
    NetworkTimeoutError,
    ApiError,
    ErrorCode,
)

# Logging (en server.py)
from mcp_shared.logging import setup_logging, get_logger
```

---

*Última actualización: junio 2026*
