"""
Tools de iluminación para mcp-smart-home.

Controla bombillas, tiras LED e interruptores inteligentes Tuya.
"""

from __future__ import annotations

from typing import Any

from mcp_shared.errors import InvalidValueError, ValidationError

from mcp_smart_home.tools.devices import _get_client


def set_brightness(device_id: str, brightness: int) -> dict[str, Any]:
    """
    Ajusta el brillo de una bombilla o tira LED.

    Args:
        device_id: ID del dispositivo de iluminación.
        brightness: Nivel de brillo (0–100).

    Returns:
        Diccionario con device_id, brightness, ok (bool).
    """
    if not device_id:
        raise ValidationError(field="device_id", message="device_id es requerido.")
    if not 0 <= brightness <= 100:
        raise InvalidValueError(
            field="brightness",
            value=brightness,
            reason="brightness debe estar entre 0 y 100.",
        )
    client = _get_client()
    return client.send_command(device_id, "bright_value", str(brightness))


def set_color(
    device_id: str,
    color: str | None = None,
    temperature: int | None = None,
) -> dict[str, Any]:
    """
    Ajusta el color o temperatura de blanco de una luz.

    Para color RGB, usar formato hex: '#FF0000' (rojo), '#00FF00' (verde).
    Para temperatura de blanco, usar valor en Kelvin (2700–6500).

    Args:
        device_id: ID del dispositivo.
        color: Color en formato hex (ej: '#FF0000'). Opcional.
        temperature: Temperatura de blanco en Kelvin (2700–6500). Opcional.

    Returns:
        Diccionario con device_id, color o temperature, ok (bool).
    """
    if not device_id:
        raise ValidationError(field="device_id", message="device_id es requerido.")
    if color is None and temperature is None:
        raise ValidationError(
            field="color",
            message="Debe especificar color o temperature.",
        )

    client = _get_client()
    if color is not None:
        if not color.startswith("#") or len(color) != 7:
            raise InvalidValueError(
                field="color",
                value=color,
                reason="color debe estar en formato hex: '#RRGGBB' (ej: '#FF0000').",
            )
        return client.send_command(device_id, "colour_data", color)
    if temperature is not None:
        if not 2700 <= temperature <= 6500:
            raise InvalidValueError(
                field="temperature",
                value=temperature,
                reason="temperature debe estar entre 2700 y 6500 Kelvin.",
            )
        return client.send_command(device_id, "temp_value", str(temperature))
    return {"ok": False}


def set_light_mode(
    device_id: str,
    mode: str,
) -> dict[str, Any]:
    """
    Cambia el modo de operación de una luz inteligente.

    Args:
        device_id: ID del dispositivo.
        mode: Modo de luz. Valores: 'white', 'colour', 'scene', 'music'.

    Returns:
        Diccionario con device_id, mode, ok (bool).
    """
    if not device_id:
        raise ValidationError(field="device_id", message="device_id es requerido.")
    valid_modes = ("white", "colour", "scene", "music")
    if mode not in valid_modes:
        raise InvalidValueError(
            field="mode",
            value=mode,
            reason=f"mode debe ser uno de: {', '.join(valid_modes)}.",
        )
    client = _get_client()
    return client.send_command(device_id, "work_mode", mode)
