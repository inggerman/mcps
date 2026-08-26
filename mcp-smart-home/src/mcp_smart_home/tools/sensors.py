"""
Tools de sensores para mcp-smart-home.

Lee datos de sensores Tuya: temperatura, humedad, PIR, contacto.
"""

from __future__ import annotations

from typing import Any

from mcp_shared.errors import ValidationError

from mcp_smart_home.tools.devices import _get_client


def get_sensor_data(device_id: str) -> dict[str, Any]:
    """
    Obtiene las lecturas actuales de un sensor Tuya.

    Detecta automáticamente el tipo de sensor y retorna los campos relevantes:
    - Sensor temp/humedad: temperature, humidity
    - Sensor PIR: pir_state (pir), presence
    - Sensor de contacto: door_contact_state, door_open (bool)
    - Sensor multi-propósito: todos los campos disponibles

    Args:
        device_id: ID del sensor.

    Returns:
        Diccionario con device_id, sensor_type, y los campos de lectura.
    """
    if not device_id:
        raise ValidationError(field="device_id", message="device_id es requerido.")
    client = _get_client()
    status = client.get_device_status(device_id)
    return status


def get_sensor_history(
    device_id: str,
    max_records: int = 100,
) -> list[dict[str, Any]]:
    """
    Obtiene el historial de lecturas de un sensor (si está disponible).

    Args:
        device_id: ID del sensor.
        max_records: Número máximo de registros (1–1000).

    Returns:
        Lista de diccionarios con timestamp, value, code (tipo de lectura).
    """
    if not device_id:
        raise ValidationError(field="device_id", message="device_id es requerido.")
    if not 1 <= max_records <= 1000:
        raise ValidationError(
            field="max_records",
            message="max_records debe estar entre 1 y 1000.",
        )
    client = _get_client()
    return client.get_device_logs(device_id, max_records)
