"""Resources de solo lectura para mcp-smart-home."""

from __future__ import annotations

import json

from mcp_smart_home.config import SmartHomeSettings

settings = SmartHomeSettings()


def smart_home_configuration() -> str:
    """Configuración actual del servidor smart-home."""
    return json.dumps(
        {
            "region": settings.region,
            "device_cache_ttl": settings.device_cache_ttl,
            "mcp_server_name": settings.mcp_server_name,
            "access_id_configured": bool(settings.access_id),
        },
        indent=2,
        ensure_ascii=False,
    )


def device_types_guide() -> str:
    """Guía de tipos de dispositivos Tuya soportados."""
    return (
        "# Tipos de dispositivos Tuya soportados\n\n"
        "## Iluminación\n"
        "- **dj**: Bombilla inteligente (on/off, brillo, color, modo)\n"
        "- **dd**: Tira LED (on/off, brillo, color, modo)\n"
        "- **tgkg**: Interruptor inteligente (on/off)\n\n"
        "## Enchufes\n"
        "- **cz**: Enchufe inteligente (on/off, medición de consumo)\n"
        "- **pc**: Enchufe con medición avanzada\n\n"
        "## Sensores\n"
        "- **wsdcg**: Sensor de temperatura y humedad\n"
        "- **pir**: Sensor de movimiento PIR\n"
        "- **mcs**: Sensor de contacto de puerta/ventana\n"
        "- **ywbj**: Sensor de humo/gas\n\n"
        "## Cámaras\n"
        "- **sp**: Cámara IP (integrable con vision-hub vía ONVIF)\n\n"
        "Usa list_devices() para ver tus dispositivos y sus categorías."
    )


def tuya_api_info() -> str:
    """Información sobre la API de Tuya."""
    return (
        "# Tuya IoT Platform API\n\n"
        "- URL: https://iot.tuya.com/\n"
        "- SDK: tuya-iot-python-sdk\n"
        "- Autenticación: Access ID + Access Secret\n"
        f"- Región configurada: {settings.region}\n"
        "- Los dispositivos se importan vinculando la app SmartLife\n"
        "- Cache de dispositivos con TTL configurable\n"
        f"- TTL actual: {settings.device_cache_ttl}s"
    )


def common_workflows() -> str:
    """Flujos de trabajo comunes de domótica."""
    return (
        "# Flujos comunes\n\n"
        "## Listar dispositivos\n"
        "tuya_list_devices()\n\n"
        "## Encender luz\n"
        "tuya_set_device_power(device_id='xxx', power_on=True)\n\n"
        "## Ajustar brillo\n"
        "tuya_set_brightness(device_id='xxx', brightness=50)\n\n"
        "## Cambiar color\n"
        "tuya_set_color(device_id='xxx', color='#FF0000')\n\n"
        "## Leer sensor\n"
        "tuya_get_sensor_data(device_id='xxx')\n\n"
        "## Consumo de enchufe\n"
        "tuya_get_energy_usage(device_id='xxx')\n\n"
        "## Disparar escena\n"
        "tuya_trigger_scene(scene_id='xxx')"
    )


def error_codes() -> str:
    """Códigos de error comunes."""
    return json.dumps(
        {
            "errors": [
                {"code": "VALIDATION_ERROR", "description": "Parámetro inválido o faltante"},
                {"code": "API_ERROR", "description": "Error en la API de Tuya Cloud"},
                {"code": "API_AUTHENTICATION_ERROR", "description": "Credenciales Tuya inválidas"},
                {"code": "RESOURCE_NOT_FOUND", "description": "Dispositivo no encontrado"},
                {"code": "NETWORK_ERROR", "description": "Error de red al contactar Tuya"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )
