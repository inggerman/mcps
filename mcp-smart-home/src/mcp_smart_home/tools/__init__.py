"""Tools de mcp-smart-home."""

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

__all__ = [
    "get_device_info",
    "get_device_status",
    "get_energy_usage",
    "get_power_state",
    "get_sensor_data",
    "get_sensor_history",
    "list_devices",
    "set_brightness",
    "set_color",
    "set_device_power",
    "set_light_mode",
    "trigger_scene",
]
