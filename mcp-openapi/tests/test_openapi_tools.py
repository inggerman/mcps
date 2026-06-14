from pathlib import Path

import pytest
from mcp_openapi.tools.openapi_tools import (
    describe_operation,
    invoke_operation,
    list_operations,
    load_spec,
)
from mcp_shared.errors import ValidationError

SPEC = {
    "openapi": "3.1.0",
    "servers": [{"url": "https://api.example.com"}],
    "paths": {
        "/users/{id}": {
            "get": {"operationId": "getUser", "summary": "Get user"},
        }
    },
}


def test_load_list_and_describe(tmp_path: Path) -> None:
    path = tmp_path / "openapi.yaml"
    path.write_text("openapi: 3.1.0\npaths:\n  /health:\n    get:\n      operationId: health\n")
    loaded = load_spec("openapi.yaml", tmp_path)
    assert list_operations(loaded)[0]["operation_id"] == "health"
    assert describe_operation(SPEC, "getUser")["method"] == "GET"


def test_invoke_requires_opt_in() -> None:
    with pytest.raises(ValidationError, match="ALLOW_INVOKE"):
        invoke_operation(SPEC, "getUser", False, ["api.example.com"])
