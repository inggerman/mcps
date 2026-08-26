"""
Tools de energía para mcp-smart-home.

Medición y control de consumo de enchufes inteligentes Tuya.
"""

from __future__ import annotations

from typing import Any

from mcp_shared.errors import ValidationError

from mcp_smart_home.tools.devices import _get_client


def get_energy_usage(device_id: str) -> dict[str, Any]:
    """
    Obtiene el consumo energético actual y acumulado de un enchufe inteligente.

    Args:
        device_id: ID del enchufe inteligente.

    Returns:
        Diccionario con device_id, power_w (potencia actual),
        current_a (corriente), voltage_v (voltaje),
        total_energy_kwh (energía acumulada), today_energy_kwh.
    """
    if not device_id:
        raise ValidationError(field="device_id", message="device_id es requerido.")
    client = _get_client()
    status = client.get_device_status(device_id)
    return status


def get_power_state(device_id: str) -> dict[str, Any]:
    """
    Obtiene el estado de energía de un enchufe: on/off + medición instantánea.

    Args:
        device_id: ID del enchufe inteligente.

    Returns:
        Diccionario con device_id, switch (bool on/off),
        power_w, current_a, voltage_v.
    """
    if not device_id:
        raise ValidationError(field="device_id", message="device_id es requerido.")
    client = _get_client()
    status = client.get_device_status(device_id)
    return status
