"""Tests para mcp-agent-runner."""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_agent_runner.tools.runner_tools import (
    agent_run_local,
    agent_trigger_webhook,
)


@pytest.mark.asyncio
async def test_agent_trigger_webhook(respx_mock) -> None:
    respx_mock.post("http://test.com/hook").respond(200, json={"job_id": 123})

    res = await agent_trigger_webhook("http://test.com/hook", {"task": "do something"})
    assert res["status"] == "success"
    assert res["response"]["job_id"] == 123


def test_agent_run_local(tmp_path: Path) -> None:
    script = tmp_path / "dummy.py"
    script.write_text("print('hello from subagent')\n", encoding="utf-8")

    res = agent_run_local(tmp_path, "dummy.py", "")
    assert res["status"] == "success"
    assert "hello from subagent" in res["stdout"]
