"""
Lógica de negocio de mcp-ci-cd.

Ejecuta un flujo simplificado de CI/CD (lint, test, deploy).
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any


def _run_stage(cmd: str, cwd: Path, stage_name: str) -> dict[str, Any]:
    """Ejecuta una fase del pipeline."""
    try:
        args = shlex.split(cmd)
        result = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        success = result.returncode == 0
        output = result.stdout.strip()
        if result.stderr.strip():
            output += f"\n{result.stderr.strip()}"

        return {
            "stage": stage_name,
            "success": success,
            "output": output[:1000] + ("..." if len(output) > 1000 else ""),
        }
    except Exception as exc:
        return {"stage": stage_name, "success": False, "output": f"Fallo al ejecutar: {exc}"}


def run_pipeline(
    project_path: Path, lint_cmd: str, test_cmd: str, deploy_cmd: str
) -> dict[str, Any]:
    """Ejecuta un pipeline CI/CD completo secuencialmente."""
    stages = []

    # 1. Lint
    lint_res = _run_stage(lint_cmd, project_path, "lint")
    stages.append(lint_res)
    if not lint_res["success"]:
        return {"status": "failed_at_lint", "stages": stages}

    # 2. Test
    test_res = _run_stage(test_cmd, project_path, "test")
    stages.append(test_res)
    if not test_res["success"]:
        return {"status": "failed_at_test", "stages": stages}

    # 3. Deploy
    deploy_res = _run_stage(deploy_cmd, project_path, "deploy")
    stages.append(deploy_res)
    if not deploy_res["success"]:
        return {"status": "failed_at_deploy", "stages": stages}

    return {"status": "success", "stages": stages}
