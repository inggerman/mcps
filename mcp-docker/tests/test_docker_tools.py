"""Tests unitarios para docker_tools (mocking del Docker SDK)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from mcp_docker.tools.docker_tools import (
    _parse_stats,
    container_exec,
    container_logs,
    containers_list,
    images_list,
    run_container,
    stop_container,
)
from mcp_shared.errors import ValidationError

# ---------------------------------------------------------------------------
# Helper: mock container
# ---------------------------------------------------------------------------


def _mock_container(
    short_id: str = "abc123",
    name: str = "web",
    status: str = "running",
    image_tags: list[str] | None = None,
) -> MagicMock:
    c = MagicMock()
    c.short_id = short_id
    c.name = name
    c.status = status
    c.image.tags = image_tags or ["nginx:latest"]
    c.image.short_id = "img123"
    c.attrs = {
        "Created": "2024-01-01T00:00:00Z",
        "State": {"StartedAt": "2024-01-01T00:01:00Z"},
        "Config": {"Cmd": ["nginx"], "Labels": {}},
        "NetworkSettings": {"Ports": {"80/tcp": [{"HostPort": "8080"}]}},
    }
    return c


def _mock_image(
    short_id: str = "img123", tags: list[str] | None = None, size: int = 50 * 1024 * 1024
) -> MagicMock:
    img = MagicMock()
    img.short_id = short_id
    img.tags = tags or ["nginx:latest"]
    img.attrs = {
        "Size": size,
        "Created": "2024-01-01T00:00:00Z",
        "Architecture": "amd64",
        "Os": "linux",
    }
    return img


# ---------------------------------------------------------------------------
# _parse_stats
# ---------------------------------------------------------------------------


class TestParseStats:
    def _raw_stats(self) -> dict:
        return {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 2_000_000, "percpu_usage": [1_000_000, 1_000_000]},
                "system_cpu_usage": 100_000_000,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 1_000_000},
                "system_cpu_usage": 90_000_000,
            },
            "memory_stats": {
                "usage": 100 * 1024 * 1024,
                "limit": 512 * 1024 * 1024,
                "stats": {"cache": 10 * 1024 * 1024},
            },
            "networks": {"eth0": {"rx_bytes": 1024 * 1024, "tx_bytes": 512 * 1024}},
            "blkio_stats": {
                "io_service_bytes_recursive": [
                    {"op": "read", "value": 2 * 1024 * 1024},
                    {"op": "write", "value": 1 * 1024 * 1024},
                ]
            },
        }

    def test_cpu_percent_calculated(self) -> None:
        result = _parse_stats(self._raw_stats(), "abc123")
        assert result["cpu_percent"] >= 0
        assert isinstance(result["cpu_percent"], float)

    def test_memory_mb(self) -> None:
        result = _parse_stats(self._raw_stats(), "abc123")
        assert result["memory_mb"] == pytest.approx(90.0, abs=1)
        assert result["memory_limit_mb"] == pytest.approx(512.0, abs=1)

    def test_network_bytes(self) -> None:
        result = _parse_stats(self._raw_stats(), "abc123")
        assert result["net_rx_mb"] == pytest.approx(1.0, abs=0.01)
        assert result["net_tx_mb"] == pytest.approx(0.5, abs=0.01)

    def test_block_io(self) -> None:
        result = _parse_stats(self._raw_stats(), "abc123")
        assert result["block_read_mb"] == pytest.approx(2.0, abs=0.01)
        assert result["block_write_mb"] == pytest.approx(1.0, abs=0.01)

    def test_container_id_preserved(self) -> None:
        result = _parse_stats(self._raw_stats(), "mycontainer")
        assert result["container_id"] == "mycontainer"


# ---------------------------------------------------------------------------
# containers_list
# ---------------------------------------------------------------------------


class TestContainersList:
    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_returns_running_containers(self, mock_client: MagicMock) -> None:
        c1 = _mock_container("abc", "web", "running")
        c2 = _mock_container("def", "db", "running")
        mock_client.return_value.containers.list.return_value = [c1, c2]

        result = containers_list()
        assert result["count"] == 2
        assert result["showing"] == "running"
        assert result["containers"][0]["name"] == "web"

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_all_containers_flag(self, mock_client: MagicMock) -> None:
        mock_client.return_value.containers.list.return_value = []
        result = containers_list(all_containers=True)
        assert result["showing"] == "all"
        mock_client.return_value.containers.list.assert_called_once_with(all=True, filters={})

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_filters_passed(self, mock_client: MagicMock) -> None:
        mock_client.return_value.containers.list.return_value = []
        containers_list(filters={"name": "web"})
        mock_client.return_value.containers.list.assert_called_once_with(
            all=False, filters={"name": "web"}
        )


# ---------------------------------------------------------------------------
# container_logs
# ---------------------------------------------------------------------------


class TestContainerLogs:
    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            container_logs("")

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_returns_logs(self, mock_client: MagicMock) -> None:
        container = _mock_container()
        container.logs.return_value = b"line1\nline2\nline3"
        mock_client.return_value.containers.get.return_value = container

        result = container_logs("web", lines=50)
        assert "line1" in result["logs"]
        assert result["lines_requested"] == 50
        assert result["status"] == "running"

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_container_not_found(self, mock_client: MagicMock) -> None:
        mock_client.return_value.containers.get.side_effect = Exception("Not found")
        with pytest.raises(ValidationError):
            container_logs("nonexistent")


# ---------------------------------------------------------------------------
# container_exec
# ---------------------------------------------------------------------------


class TestContainerExec:
    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            container_exec("", "ls")

    def test_empty_command_raises(self) -> None:
        with pytest.raises(ValidationError):
            container_exec("web", "")

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_not_running_raises(self, mock_client: MagicMock) -> None:
        container = _mock_container(status="exited")
        mock_client.return_value.containers.get.return_value = container
        with pytest.raises(ValidationError):
            container_exec("web", "ls")

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_successful_exec(self, mock_client: MagicMock) -> None:
        container = _mock_container()
        container.exec_run.return_value = (0, b"total 20\ndrwxr-xr-x")
        mock_client.return_value.containers.get.return_value = container

        result = container_exec("web", "ls -la")
        assert result["exit_code"] == 0
        assert result["success"] is True
        assert "total" in result["output"]

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_failed_exec(self, mock_client: MagicMock) -> None:
        container = _mock_container()
        container.exec_run.return_value = (1, b"command not found")
        mock_client.return_value.containers.get.return_value = container

        result = container_exec("web", "nonexistent_cmd")
        assert result["exit_code"] == 1
        assert result["success"] is False


# ---------------------------------------------------------------------------
# run_container
# ---------------------------------------------------------------------------


class TestRunContainer:
    def test_empty_image_raises(self) -> None:
        with pytest.raises(ValidationError):
            run_container("")

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_run_detached(self, mock_client: MagicMock) -> None:
        container = _mock_container("abc", "my-nginx", "running")
        container.reload = MagicMock()
        mock_client.return_value.containers.run.return_value = container

        result = run_container("nginx:latest", name="my-nginx")
        assert result["name"] == "my-nginx"
        assert result["status"] == "running"


# ---------------------------------------------------------------------------
# stop_container
# ---------------------------------------------------------------------------


class TestStopContainer:
    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            stop_container("")

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_stop_without_remove(self, mock_client: MagicMock) -> None:
        container = _mock_container()
        mock_client.return_value.containers.get.return_value = container

        result = stop_container("web")
        container.stop.assert_called_once()
        container.remove.assert_not_called()
        assert result["removed"] is False
        assert result["action"] == "stopped"

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_stop_with_remove(self, mock_client: MagicMock) -> None:
        container = _mock_container()
        mock_client.return_value.containers.get.return_value = container

        result = stop_container("web", remove=True)
        container.stop.assert_called_once()
        container.remove.assert_called_once()
        assert result["removed"] is True
        assert result["action"] == "stopped_and_removed"

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_container_not_found(self, mock_client: MagicMock) -> None:
        mock_client.return_value.containers.get.side_effect = Exception("Not found")
        with pytest.raises(ValidationError):
            stop_container("nonexistent")


# ---------------------------------------------------------------------------
# images_list
# ---------------------------------------------------------------------------


class TestImagesList:
    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_returns_images(self, mock_client: MagicMock) -> None:
        img1 = _mock_image("img1", ["nginx:latest"])
        img2 = _mock_image("img2", ["python:3.12"])
        mock_client.return_value.images.list.return_value = [img1, img2]

        result = images_list()
        assert result["count"] == 2
        assert result["images"][0]["tags"] == ["nginx:latest"]
        assert result["images"][0]["size_mb"] == pytest.approx(50.0, abs=1)

    @patch("mcp_docker.tools.docker_tools._get_client")
    def test_filter_by_name(self, mock_client: MagicMock) -> None:
        mock_client.return_value.images.list.return_value = []
        images_list(name="nginx")
        mock_client.return_value.images.list.assert_called_once_with(name="nginx", filters={})
