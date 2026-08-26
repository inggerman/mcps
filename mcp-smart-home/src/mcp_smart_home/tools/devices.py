"""
Tools de dispositivos generales para mcp-smart-home.

Lista, consulta y controla dispositivos Tuya vía Cloud API.
"""

from __future__ import annotations

import time
from typing import Any

from mcp_shared.errors import ApiError, NotFoundError, ValidationError

from mcp_smart_home.tuya_client import TuyaClient

_client: TuyaClient | None = None
_device_cache: dict[str, Any] = {}
_device_cache_ts: float = 0


def _get_client() -> TuyaClient:
    global _client
    if _client is None:
        _client = TuyaClient()
    return _client


def list_devices() -> list[dict[str, Any]]:
    """
    Lista todos los dispositivos del hogar vinculados a Tuya Cloud.

    Returns:
        Lista de diccionarios con device_id, name, category, model,
        online, icon, parent_id. Ordenados por nombre.
    """
    global _device_cache, _device_cache_ts
    from mcp_smart_home.config import SmartHomeSettings

    settings = SmartHomeSettings()
    now = time.time()
    if _device_cache and (now - _device_cache_ts) < settings.device_cache_ttl:
        return _device_cache.get("devices", [])

    client = _get_client()
    devices = client.list_devices()
    _device_cache = {"devices": devices}
    _device_cache_ts = now
    return devices


def get_device_status(device_id: str) -> dict[str, Any]:
    """
    Obtiene el estado completo de un dispositivo.

    Args:
        device_id: ID del dispositivo Tuya.

    Returns:
        Diccionario con device_id, name, category, online, y todos los
        campos de estado (switch, brightness, color, temperature, etc.)
        según el tipo de dispositivo.
    """
    if not device_id:
        raise ValidationError(field="device_id", message="device_id es requerido.")
    client = _get_client()
    return client.get_device_status(device_id)


def get_device_info(device_id: str) -> dict[str, Any]:
    """
    Obtiene información detallada de un dispositivo.

    Args:
        device_id: ID del dispositivo Tuya.

    Returns:
        Diccionario con device_id, name, category, model, brand, icon,
        mac, uuid, node_id, status, specs, capabilities.
    """
    if not device_id:
        raise ValidationError(field="device_id", message="device_id es requerido.")
    client = _get_client()
    return client.get_device_info(device_id)


def set_device_power(device_id: str, power_on: bool) -> dict[str, Any]:
    """
    Enciende o apaga cualquier dispositivo Tuya.

    Args:
        device_id: ID del dispositivo.
        power_on: True para encender, False para apagar.

    Returns:
        Diccionario con device_id, power (bool), ok (bool).
    """
    if not device_id:
        raise ValidationError(field="device_id", message="device_id es requerido.")
    client = _get_client()
    return client.send_command(device_id, "switch", "1" if power_on else "0")


def trigger_scene(scene_id: str) -> dict[str, Any]:
    """
    Dispara una escena configurada en Tuya SmartLife.

    Args:
        scene_id: ID de la escena a ejecutar.

    Returns:
        Diccionario con scene_id, ok (bool).
    """
    if not scene_id:
        raise ValidationError(field="scene_id", message="scene_id es requerido.")
    client = _get_client()
    return client.trigger_scene(scene_id)
