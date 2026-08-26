# mcp-smart-home

MCP server para domótica Tuya SmartLife. Controla luces, enchufes, sensores y escenas desde el IDE o agentes de IA.

## Features

- **Dispositivos**: Listar, estado, info, on/off
- **Iluminación**: Brillo, color RGB, temperatura de blanco, modos
- **Sensores**: Temperatura, humedad, PIR, contacto, historial
- **Energía**: Consumo actual, voltaje, corriente, acumulado
- **Escenas**: Disparar escenas de SmartLife

## Requisitos

1. Cuenta en [Tuya IoT Platform](https://iot.tuya.com/)
2. Proyecto Cloud con Access ID y Access Secret
3. App SmartLife vinculada al proyecto

## Configuración

Copiar `.env.example` a `.env` y llenar credenciales:

```bash
TUYA_ACCESS_ID=tu_access_id
TUYA_ACCESS_KEY=tu_access_secret
TUYA_REGION=us
```

## Uso local

```bash
cd mcps
uv pip install -e mcp-smart-home
python -m mcp_smart_home.server
```

## Tools (12)

| Tool | Descripción |
|------|-------------|
| `tuya_list_devices` | Lista todos los dispositivos |
| `tuya_get_device_status` | Estado completo de un dispositivo |
| `tuya_get_device_info` | Info detallada (modelo, MAC, specs) |
| `tuya_set_device_power` | On/off de cualquier dispositivo |
| `tuya_set_brightness` | Brillo 0-100 |
| `tuya_set_color` | Color RGB o temperatura de blanco |
| `tuya_set_light_mode` | Modo: white, colour, scene, music |
| `tuya_get_sensor_data` | Lectura actual de sensor |
| `tuya_get_sensor_history` | Historial de lecturas |
| `tuya_get_energy_usage` | Consumo de enchufe |
| `tuya_get_power_state` | Estado on/off + medición |
| `tuya_trigger_scene` | Disparar escena SmartLife |

## Docker

```bash
docker build -t mcp-smart-home -f mcp-smart-home/Dockerfile .
docker run --env-file mcp-smart-home/.env mcp-smart-home
```
