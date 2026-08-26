"""Tests de tools de mcp-smart-home."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mcp_shared.errors import ValidationError


class TestDevices:
    """Tests de tools de dispositivos."""

    @patch("mcp_smart_home.tools.devices._get_client")
    def test_list_devices(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.list_devices.return_value = [
            {"id": "dev1", "name": "Luz Sala", "category": "dj"},
            {"id": "dev2", "name": "Enchufe Cocina", "category": "cz"},
        ]
        from mcp_smart_home.tools.devices import list_devices

        result = list_devices()
        assert len(result) == 2
        assert result[0]["name"] == "Enchufe Cocina"

    @patch("mcp_smart_home.tools.devices._get_client")
    def test_get_device_status(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.get_device_status.return_value = {
            "device_id": "dev1",
            "status": {"switch": True},
            "raw": [],
        }
        from mcp_smart_home.tools.devices import get_device_status

        result = get_device_status("dev1")
        assert result["device_id"] == "dev1"
        assert result["status"]["switch"] is True

    def test_get_device_status_empty_id(self):
        from mcp_smart_home.tools.devices import get_device_status

        with pytest.raises(ValidationError):
            get_device_status("")

    @patch("mcp_smart_home.tools.devices._get_client")
    def test_set_device_power(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.send_command.return_value = {
            "device_id": "dev1",
            "code": "switch",
            "value": "1",
            "ok": True,
        }
        from mcp_smart_home.tools.devices import set_device_power

        result = set_device_power("dev1", True)
        assert result["ok"] is True
        mock_client.send_command.assert_called_once_with("dev1", "switch", "1")


class TestLighting:
    """Tests de tools de iluminación."""

    @patch("mcp_smart_home.tools.devices._get_client")
    def test_set_brightness(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.send_command.return_value = {"ok": True}
        from mcp_smart_home.tools.lighting import set_brightness

        result = set_brightness("dev1", 50)
        assert result["ok"] is True

    def test_set_brightness_invalid(self):
        from mcp_smart_home.tools.lighting import set_brightness

        with pytest.raises(ValidationError):
            set_brightness("dev1", 150)

    @patch("mcp_smart_home.tools.devices._get_client")
    def test_set_color_hex(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.send_command.return_value = {"ok": True}
        from mcp_smart_home.tools.lighting import set_color

        result = set_color("dev1", color="#FF0000")
        assert result["ok"] is True

    def test_set_color_invalid_hex(self):
        from mcp_smart_home.tools.lighting import set_color

        with pytest.raises(ValidationError):
            set_color("dev1", color="FF0000")

    @patch("mcp_smart_home.tools.devices._get_client")
    def test_set_light_mode(self, mock_client_fn):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.send_command.return_value = {"ok": True}
        from mcp_smart_home.tools.lighting import set_light_mode

        result = set_light_mode("dev1", "colour")
        assert result["ok"] is True

    def test_set_light_mode_invalid(self):
        from mcp_smart_home.tools.lighting import set_light_mode

        with pytest.raises(ValidationError):
            set_light_mode("dev1", "invalid")


class TestServer:
    """Tests del servidor MCP."""

    def test_create_server(self):
        from mcp_smart_home.server import create_server

        server = create_server()
        assert server is not None
        assert server.name == "mcp-smart-home"
