"""
Cliente de Tuya Cloud API para mcp-smart-home.

Encapsula el SDK oficial tuya-iot-python-sdk para listar dispositivos,
obtener estado, enviar comandos y disparar escenas.
"""

from __future__ import annotations

import time
from typing import Any

from mcp_shared.errors import ApiError, NotFoundError

from mcp_smart_home.config import SmartHomeSettings


class TuyaClient:
    """Cliente que envuelve la API de Tuya IoT Platform."""

    def __init__(self, settings: SmartHomeSettings | None = None) -> None:
        self._settings = settings or SmartHomeSettings()
        self._tuya = None

    @property
    def tuya(self):
        """Lazy-init del SDK de Tuya."""
        if self._tuya is None:
            try:
                from tuya_iot import TuyaOpenAPI

                self._tuya = TuyaOpenAPI(
                    endpoint=self._endpoint(),
                    access_id=self._settings.access_id,
                    access_key=self._settings.access_key_value,
                )
                self._tuya.connect()
            except ImportError:
                raise ApiError(
                    "tuya-iot-python-sdk no está instalado. Ejecuta: pip install tuya-iot-python-sdk",
                )
            except Exception as exc:
                raise ApiError(
                    f"Error conectando a Tuya Cloud: {exc}",
                    context={"region": self._settings.region},
                ) from exc
        return self._tuya

    def _endpoint(self) -> str:
        """URL del endpoint según la región."""
        endpoints = {
            "us": "https://openapi.tuyaus.com",
            "eu": "https://openapi.tuyaeu.com",
            "cn": "https://openapi.tuyacn.com",
            "in": "https://openapi.tuyain.com",
        }
        return endpoints.get(self._settings.region, endpoints["us"])

    def list_devices(self) -> list[dict[str, Any]]:
        """Lista todos los dispositivos del hogar."""
        try:
            resp = self.tuya.get("/v1.0/users/{}/devices".format(self._settings.access_id))
            if not resp.get("success"):
                raise ApiError(f"Tuya API error: {resp.get('msg', 'unknown')}")
            devices = resp.get("result", [])
            return sorted(devices, key=lambda d: d.get("name", ""))
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(f"Error listando dispositivos: {exc}") from exc

    def get_device_status(self, device_id: str) -> dict[str, Any]:
        """Obtiene el estado completo de un dispositivo."""
        try:
            resp = self.tuya.get(f"/v1.0/devices/{device_id}/status")
            if not resp.get("success"):
                raise ApiError(f"Tuya API error: {resp.get('msg', 'unknown')}")
            status_list = resp.get("result", [])
            status_map = {item["code"]: item["value"] for item in status_list}
            return {"device_id": device_id, "status": status_map, "raw": status_list}
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(f"Error obteniendo estado de {device_id}: {exc}") from exc

    def get_device_info(self, device_id: str) -> dict[str, Any]:
        """Obtiene info detallada de un dispositivo."""
        try:
            resp = self.tuya.get(f"/v1.0/device/{device_id}")
            if not resp.get("success"):
                if "not exist" in resp.get("msg", "").lower():
                    raise NotFoundError("device", device_id)
                raise ApiError(f"Tuya API error: {resp.get('msg', 'unknown')}")
            return resp.get("result", {})
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(f"Error obteniendo info de {device_id}: {exc}") from exc

    def send_command(
        self,
        device_id: str,
        code: str,
        value: str,
    ) -> dict[str, Any]:
        """Envía un comando a un dispositivo."""
        try:
            commands = [{"code": code, "value": value}]
            resp = self.tuya.post(
                f"/v1.0/device/{device_id}/commands",
                {"commands": commands},
            )
            if not resp.get("success"):
                raise ApiError(f"Tuya API error: {resp.get('msg', 'unknown')}")
            return {
                "device_id": device_id,
                "code": code,
                "value": value,
                "ok": True,
            }
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(f"Error enviando comando a {device_id}: {exc}") from exc

    def trigger_scene(self, scene_id: str) -> dict[str, Any]:
        """Dispara una escena de SmartLife."""
        try:
            resp = self.tuya.post(
                f"/v1.0/homes/scene/{scene_id}/trigger",
                {},
            )
            if not resp.get("success"):
                raise ApiError(f"Tuya API error: {resp.get('msg', 'unknown')}")
            return {"scene_id": scene_id, "ok": True}
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(f"Error disparando escena {scene_id}: {exc}") from exc

    def get_device_logs(
        self,
        device_id: str,
        max_records: int = 100,
    ) -> list[dict[str, Any]]:
        """Obtiene logs/historial de un dispositivo."""
        try:
            end_ts = int(time.time() * 1000)
            start_ts = end_ts - (7 * 24 * 60 * 60 * 1000)
            resp = self.tuya.get(
                f"/v1.0/device/{device_id}/logs",
                {
                    "start_time": start_ts,
                    "end_time": end_ts,
                    "size": max_records,
                },
            )
            if not resp.get("success"):
                raise ApiError(f"Tuya API error: {resp.get('msg', 'unknown')}")
            return resp.get("result", {}).get("logs", [])
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(f"Error obteniendo logs de {device_id}: {exc}") from exc
