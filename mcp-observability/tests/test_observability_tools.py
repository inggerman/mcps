from unittest.mock import MagicMock, patch

import pytest
from mcp_observability.tools.observability_tools import check_endpoint, query_prometheus
from mcp_shared.errors import ValidationError


@patch("mcp_observability.tools.observability_tools.httpx.get")
def test_prometheus_query(mock_get: MagicMock) -> None:
    response = MagicMock()
    response.json.return_value = {"status": "success"}
    mock_get.return_value = response
    assert query_prometheus("http://prometheus:9090", "up", 10)["status"] == "success"


def test_missing_prometheus_url() -> None:
    with pytest.raises(ValidationError):
        query_prometheus(None, "up", 10)


def test_health_rejects_non_http() -> None:
    with pytest.raises(ValidationError):
        check_endpoint("file:///tmp/status", 10)
