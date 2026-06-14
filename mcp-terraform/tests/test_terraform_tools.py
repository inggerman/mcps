from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from mcp_shared.errors import ValidationError
from mcp_terraform.tools.terraform_tools import (
    resolve_working_dir,
    terraform_apply,
    terraform_plan,
)


def test_resolve_working_dir_blocks_escape(tmp_path: Path) -> None:
    with pytest.raises(ValidationError):
        resolve_working_dir(tmp_path, "../outside")


@patch("mcp_terraform.tools.terraform_tools.subprocess.run")
def test_plan_builds_safe_command(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
    result = terraform_plan("terraform", tmp_path, ".", 30, {"region": "us-east-1"})
    assert result["success"] is True
    assert result["command"][1] == "plan"


def test_apply_requires_opt_in(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="ALLOW_APPLY"):
        terraform_apply("terraform", tmp_path, ".", 30, "tfplan", False)
