"""
Servidor FastMCP para mcp-smart-home.

Expone 12 herramientas para control de domótica Tuya SmartLife:
- 4 tools de dispositivos generales (listar, estado, info, power)
- 3 tools de iluminación (brillo, color, modo)
- 2 tools de sensores (lectura, historial)
- 2 tools de energía (consumo, estado)
- 1 tool de escenas (disparar)

Transporte: configurable mediante MCP_TRANSPORT (stdio | streamable-http).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_smart_home.config import SmartHomeSettings
from mcp_smart_home.tools.devices import (
    get_device_info,
    get_device_status,
    list_devices,
    set_device_power,
    trigger_scene,
)
from mcp_smart_home.tools.energy import (
    get_energy_usage,
    get_power_state,
)
from mcp_smart_home.tools.lighting import (
    set_brightness,
    set_color,
    set_light_mode,
)
from mcp_smart_home.tools.sensors import (
    get_sensor_data,
    get_sensor_history,
)
from mcp_smart_home import resources as res

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

settings = SmartHomeSettings()

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-smart-home",
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Context manager de ciclo de vida del servidor MCP."""
    structlog.contextvars.bind_contextvars(server_name="mcp-smart-home")
    logger.info(
        "Servidor mcp-smart-home iniciando",
        region=settings.region,
        access_id_configured=bool(settings.access_id),
        device_cache_ttl=settings.device_cache_ttl,
        log_level=settings.log_level,
        log_format=settings.log_format,
        transport=settings.mcp_transport,
    )
    yield
    logger.info("Servidor mcp-smart-home detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-smart-home",
    instructions=(
        "Servidor MCP para domótica Tuya SmartLife.\n\n"
        "## Dispositivos\n"
        "- **tuya_list_devices**: Lista todos los dispositivos del hogar.\n"
        "- **tuya_get_device_status**: Estado completo de un dispositivo.\n"
        "- **tuya_get_device_info**: Info detallada (modelo, categoría, specs).\n"
        "- **tuya_set_device_power**: Enciende o apaga cualquier dispositivo.\n\n"
        "## Iluminación\n"
        "- **tuya_set_brightness**: Ajusta brillo 0-100.\n"
        "- **tuya_set_color**: Color RGB (#FF0000) o temperatura de blanco (2700-6500K).\n"
        "- **tuya_set_light_mode**: Modo: white, colour, scene, music.\n\n"
        "## Sensores\n"
        "- **tuya_get_sensor_data**: Lectura actual (temp, humedad, PIR, contacto).\n"
        "- **tuya_get_sensor_history**: Historial de lecturas.\n\n"
        "## Energía\n"
        "- **tuya_get_energy_usage**: Consumo actual y acumulado de enchufes.\n"
        "- **tuya_get_power_state**: Estado on/off + medición instantánea.\n\n"
        "## Escenas\n"
        "- **tuya_trigger_scene**: Dispara una escena de SmartLife.\n\n"
        "Todos los device_id se obtienen con tuya_list_devices()."
    ),
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Helpers de manejo de errores
# ---------------------------------------------------------------------------


def _handle_mcp_error(tool_name: str, exc: McpError) -> None:
    """Registra un McpError y lo relanza como SdkMcpError."""
    logger.error(
        "Error en tool MCP",
        tool=tool_name,
        error_code=exc.error_code,
        message=exc.message,
        context=exc.context,
    )
    raise SdkMcpError(ErrorData(code=-32000, message=str(exc)))


def _handle_unexpected_error(tool_name: str, exc: Exception) -> None:
    """Registra un error inesperado y lo relanza como SdkMcpError."""
    logger.exception(
        "Error inesperado en tool MCP",
        tool=tool_name,
        error_type=type(exc).__name__,
        error=str(exc),
    )
    raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor."))


# ---------------------------------------------------------------------------
# Tools — Dispositivos generales
# ---------------------------------------------------------------------------


@mcp.tool(
    name="tuya_list_devices",
    description=(
        "Lista todos los dispositivos del hogar vinculados a Tuya Cloud. "
        "Retorna: lista con device_id, name, category, model, online, icon. "
        "No requiere parámetros. Los resultados se cachean (TUYA_DEVICE_CACHE_TTL)."
    ),
)
def tool_list_devices() -> list[dict[str, Any]]:
    """Lista todos los dispositivos Tuya."""
    try:
        return list_devices()
    except McpError as exc:
        _handle_mcp_error("tuya_list_devices", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_list_devices", exc)
    return []


@mcp.tool(
    name="tuya_get_device_status",
    description=(
        "Obtiene el estado completo de un dispositivo Tuya. "
        "Parámetros: device_id (ID del dispositivo). "
        "Retorna: device_id, status (mapa code→value), raw (lista completa)."
    ),
)
def tool_get_device_status(device_id: str) -> dict[str, Any]:
    """Obtiene el estado de un dispositivo."""
    try:
        return get_device_status(device_id=device_id)
    except McpError as exc:
        _handle_mcp_error("tuya_get_device_status", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_get_device_status", exc)
    return {}


@mcp.tool(
    name="tuya_get_device_info",
    description=(
        "Obtiene información detallada de un dispositivo: modelo, marca, "
        "categoría, MAC, UUID, capacidades. "
        "Parámetros: device_id. "
        "Retorna: diccionario con todos los metadatos del dispositivo."
    ),
)
def tool_get_device_info(device_id: str) -> dict[str, Any]:
    """Obtiene info detallada de un dispositivo."""
    try:
        return get_device_info(device_id=device_id)
    except McpError as exc:
        _handle_mcp_error("tuya_get_device_info", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_get_device_info", exc)
    return {}


@mcp.tool(
    name="tuya_set_device_power",
    description=(
        "Enciende o apaga cualquier dispositivo Tuya (luz, enchufe, interruptor). "
        "Parámetros: device_id, power_on (True=encender, False=apagar). "
        "Retorna: device_id, code, value, ok."
    ),
)
def tool_set_device_power(device_id: str, power_on: bool) -> dict[str, Any]:
    """Enciende o apaga un dispositivo."""
    try:
        return set_device_power(device_id=device_id, power_on=power_on)
    except McpError as exc:
        _handle_mcp_error("tuya_set_device_power", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_set_device_power", exc)
    return {}


# ---------------------------------------------------------------------------
# Tools — Iluminación
# ---------------------------------------------------------------------------


@mcp.tool(
    name="tuya_set_brightness",
    description=(
        "Ajusta el brillo de una bombilla o tira LED. "
        "Parámetros: device_id, brightness (0–100). "
        "Retorna: device_id, code, value, ok."
    ),
)
def tool_set_brightness(device_id: str, brightness: int) -> dict[str, Any]:
    """Ajusta el brillo de una luz."""
    try:
        return set_brightness(device_id=device_id, brightness=brightness)
    except McpError as exc:
        _handle_mcp_error("tuya_set_brightness", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_set_brightness", exc)
    return {}


@mcp.tool(
    name="tuya_set_color",
    description=(
        "Ajusta el color o temperatura de blanco de una luz. "
        "Para color RGB: color='#FF0000' (hex). "
        "Para blanco: temperature=4000 (Kelvin 2700–6500). "
        "Parámetros: device_id, color (opcional), temperature (opcional). "
        "Retorna: device_id, code, value, ok."
    ),
)
def tool_set_color(
    device_id: str,
    color: str | None = None,
    temperature: int | None = None,
) -> dict[str, Any]:
    """Cambia el color o temperatura de una luz."""
    try:
        return set_color(device_id=device_id, color=color, temperature=temperature)
    except McpError as exc:
        _handle_mcp_error("tuya_set_color", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_set_color", exc)
    return {}


@mcp.tool(
    name="tuya_set_light_mode",
    description=(
        "Cambia el modo de operación de una luz inteligente. "
        "Modos: 'white' (blanco), 'colour' (color), 'scene' (escena), 'music' (música). "
        "Parámetros: device_id, mode. "
        "Retorna: device_id, code, value, ok."
    ),
)
def tool_set_light_mode(device_id: str, mode: str) -> dict[str, Any]:
    """Cambia el modo de una luz."""
    try:
        return set_light_mode(device_id=device_id, mode=mode)
    except McpError as exc:
        _handle_mcp_error("tuya_set_light_mode", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_set_light_mode", exc)
    return {}


# ---------------------------------------------------------------------------
# Tools — Sensores
# ---------------------------------------------------------------------------


@mcp.tool(
    name="tuya_get_sensor_data",
    description=(
        "Obtiene las lecturas actuales de un sensor Tuya. "
        "Detecta automáticamente el tipo: temperatura/humedad, PIR, contacto. "
        "Parámetros: device_id. "
        "Retorna: device_id, status (mapa code→value), raw."
    ),
)
def tool_get_sensor_data(device_id: str) -> dict[str, Any]:
    """Lee datos de un sensor."""
    try:
        return get_sensor_data(device_id=device_id)
    except McpError as exc:
        _handle_mcp_error("tuya_get_sensor_data", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_get_sensor_data", exc)
    return {}


@mcp.tool(
    name="tuya_get_sensor_history",
    description=(
        "Obtiene el historial de lecturas de un sensor (últimos 7 días). "
        "Parámetros: device_id, max_records (1–1000, default 100). "
        "Retorna: lista de registros con timestamp, value, code."
    ),
)
def tool_get_sensor_history(
    device_id: str,
    max_records: int = 100,
) -> list[dict[str, Any]]:
    """Historial de un sensor."""
    try:
        return get_sensor_history(device_id=device_id, max_records=max_records)
    except McpError as exc:
        _handle_mcp_error("tuya_get_sensor_history", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_get_sensor_history", exc)
    return []


# ---------------------------------------------------------------------------
# Tools — Energía
# ---------------------------------------------------------------------------


@mcp.tool(
    name="tuya_get_energy_usage",
    description=(
        "Obtiene el consumo energético de un enchufe inteligente. "
        "Incluye: potencia actual (W), corriente (A), voltaje (V), "
        "energía acumulada (kWh), energía del día (kWh). "
        "Parámetros: device_id. "
        "Retorna: device_id, status (mapa code→value), raw."
    ),
)
def tool_get_energy_usage(device_id: str) -> dict[str, Any]:
    """Consumo de un enchufe."""
    try:
        return get_energy_usage(device_id=device_id)
    except McpError as exc:
        _handle_mcp_error("tuya_get_energy_usage", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_get_energy_usage", exc)
    return {}


@mcp.tool(
    name="tuya_get_power_state",
    description=(
        "Obtiene el estado de energía de un enchufe: on/off + medición instantánea. "
        "Parámetros: device_id. "
        "Retorna: device_id, status (switch bool, power_w, current_a, voltage_v), raw."
    ),
)
def tool_get_power_state(device_id: str) -> dict[str, Any]:
    """Estado de energía de un enchufe."""
    try:
        return get_power_state(device_id=device_id)
    except McpError as exc:
        _handle_mcp_error("tuya_get_power_state", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_get_power_state", exc)
    return {}


# ---------------------------------------------------------------------------
# Tools — Escenas
# ---------------------------------------------------------------------------


@mcp.tool(
    name="tuya_trigger_scene",
    description=(
        "Dispara una escena configurada en Tuya SmartLife. "
        "Parámetros: scene_id (ID de la escena). "
        "Retorna: scene_id, ok."
    ),
)
def tool_trigger_scene(scene_id: str) -> dict[str, Any]:
    """Dispara una escena."""
    try:
        return trigger_scene(scene_id=scene_id)
    except McpError as exc:
        _handle_mcp_error("tuya_trigger_scene", exc)
    except Exception as exc:
        _handle_unexpected_error("tuya_trigger_scene", exc)
    return {}


# ---------------------------------------------------------------------------
# Resources estáticos
# ---------------------------------------------------------------------------


@mcp.resource("smart-home://configuration")
def res_config() -> str:
    return res.smart_home_configuration()


@mcp.resource("smart-home://device-types")
def res_device_types() -> str:
    return res.device_types_guide()


@mcp.resource("smart-home://tuya-api-info")
def res_tuya_api() -> str:
    return res.tuya_api_info()


@mcp.resource("smart-home://common-workflows")
def res_workflows() -> str:
    return res.common_workflows()


@mcp.resource("smart-home://error-codes")
def res_errors() -> str:
    return res.error_codes()


# ---------------------------------------------------------------------------
# Factory + Entrypoint
# ---------------------------------------------------------------------------


def create_server() -> FastMCP:
    """Retorna la instancia del servidor MCP para uso externo."""
    return mcp


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
