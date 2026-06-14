from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from mcp_kubernetes.tools.kubernetes_tools import list_pods, scale_deployment
from mcp_shared.errors import ValidationError


def test_list_pods() -> None:
    api = MagicMock()
    api.list_namespaced_pod.return_value.items = [
        SimpleNamespace(
            metadata=SimpleNamespace(name="api-1", namespace="default"),
            status=SimpleNamespace(phase="Running"),
            spec=SimpleNamespace(
                node_name="node-1",
                containers=[SimpleNamespace(name="api")],
            ),
        )
    ]
    assert list_pods(api, "default")[0]["phase"] == "Running"


def test_scale_requires_opt_in() -> None:
    with pytest.raises(ValidationError, match="ALLOW_WRITE"):
        scale_deployment(MagicMock(), "default", "api", 2, False)
