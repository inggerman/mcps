"""
Lógica de negocio de mcp-code-quality.

Ejecuta linters, formateadores y tests en el proyecto objetivo.
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Any

from mcp_shared.errors import ValidationError


def _run_command(cmd: str, cwd: Path) -> tuple[bool, str]:
    """Ejecuta un comando en shell, retorna (éxito, salida combinada)."""
    try:
        args = shlex.split(cmd)
        result = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        # Combina stdout y stderr para mejor contexto
        output = result.stdout.strip()
        if result.stderr.strip():
            output += f"\n[STDERR]\n{result.stderr.strip()}"

        return (result.returncode == 0, output)
    except Exception as exc:
        raise ValidationError(
            field="command",
            message=f"No se pudo ejecutar '{cmd}': {exc}",
        ) from exc


def run_lint(project_path: Path, linter_cmd: str, target: str = "") -> dict[str, Any]:
    """Ejecuta el linter sobre el proyecto o un archivo/directorio específico."""
    cmd = linter_cmd
    if target:
        cmd += f" {shlex.quote(target)}"

    success, output = _run_command(cmd, project_path)
    return {
        "success": success,
        "output": output,
        "command_run": cmd,
    }


def run_format(
    project_path: Path, formatter_cmd: str, check_only: bool = False, target: str = ""
) -> dict[str, Any]:
    """Ejecuta el formateador. Si check_only=True, no modifica archivos."""
    cmd = formatter_cmd
    if check_only:
        # Asume formato ruff/black (usan --check)
        cmd += " --check"
    if target:
        cmd += f" {shlex.quote(target)}"

    success, output = _run_command(cmd, project_path)
    return {
        "success": success,
        "output": output,
        "command_run": cmd,
    }


def run_tests(project_path: Path, test_cmd: str, target: str = "") -> dict[str, Any]:
    """Ejecuta los tests unitarios."""
    cmd = test_cmd
    if target:
        cmd += f" {shlex.quote(target)}"

    success, output = _run_command(cmd, project_path)
    return {
        "success": success,
        "output": output,
        "command_run": cmd,
    }
