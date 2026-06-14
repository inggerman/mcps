"""Tests para mcp-ci-cd."""

from __future__ import annotations

from pathlib import Path

from mcp_ci_cd.tools.cicd_tools import run_pipeline


def test_run_pipeline_success(tmp_path: Path) -> None:
    res = run_pipeline(
        tmp_path,
        lint_cmd="python -c pass",
        test_cmd="python -c pass",
        deploy_cmd="python -c pass",
    )
    assert res["status"] == "success"
    assert len(res["stages"]) == 3
    for stage in res["stages"]:
        assert stage["success"] is True


def test_run_pipeline_fail_lint(tmp_path: Path) -> None:
    res = run_pipeline(
        tmp_path,
        lint_cmd='python -c "import sys; sys.exit(1)"',
        test_cmd="python -c pass",
        deploy_cmd="python -c pass",
    )
    assert res["status"] == "failed_at_lint"
    assert len(res["stages"]) == 1
    assert res["stages"][0]["success"] is False
