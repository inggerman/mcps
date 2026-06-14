from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from mcp_shared.errors import ValidationError


def resolve_working_dir(root: Path, working_dir: str = ".") -> Path:
    base = root.resolve()
    target = (base / working_dir).resolve()
    if not target.is_relative_to(base):
        raise ValidationError(field="working_dir", message="La ruta está fuera de TERRAFORM_ROOT.")
    if not target.is_dir():
        raise ValidationError(field="working_dir", message="El directorio no existe.")
    return target


def run_terraform(
    binary: str,
    root: Path,
    working_dir: str,
    args: list[str],
    timeout_seconds: int,
) -> dict[str, Any]:
    target = resolve_working_dir(root, working_dir)
    try:
        result = subprocess.run(
            [binary, *args],
            cwd=target,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ValidationError(field="binary", message=f"No se encontró '{binary}'.") from exc
    return {
        "command": [binary, *args],
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.returncode == 0,
    }


def terraform_fmt_check(binary: str, root: Path, working_dir: str, timeout: int) -> dict[str, Any]:
    return run_terraform(binary, root, working_dir, ["fmt", "-check", "-recursive"], timeout)


def terraform_validate(binary: str, root: Path, working_dir: str, timeout: int) -> dict[str, Any]:
    return run_terraform(binary, root, working_dir, ["validate", "-json"], timeout)


def terraform_plan(
    binary: str,
    root: Path,
    working_dir: str,
    timeout: int,
    variables: dict[str, Any] | None = None,
    output_file: str = "tfplan",
) -> dict[str, Any]:
    safe_output = Path(output_file).name
    args = ["plan", "-input=false", "-no-color", f"-out={safe_output}"]
    for key, value in sorted((variables or {}).items()):
        args.extend(["-var", f"{key}={json.dumps(value) if not isinstance(value, str) else value}"])
    return run_terraform(binary, root, working_dir, args, timeout)


def terraform_show(
    binary: str,
    root: Path,
    working_dir: str,
    timeout: int,
    plan_file: str = "tfplan",
) -> dict[str, Any]:
    return run_terraform(
        binary, root, working_dir, ["show", "-json", Path(plan_file).name], timeout
    )


def terraform_apply(
    binary: str,
    root: Path,
    working_dir: str,
    timeout: int,
    plan_file: str,
    allow_apply: bool,
) -> dict[str, Any]:
    if not allow_apply:
        raise ValidationError(field="apply", message="TERRAFORM_ALLOW_APPLY está desactivado.")
    return run_terraform(
        binary,
        root,
        working_dir,
        ["apply", "-input=false", "-auto-approve", Path(plan_file).name],
        timeout,
    )
