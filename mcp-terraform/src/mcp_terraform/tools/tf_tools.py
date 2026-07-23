"""
Lógica de mcp-terraform.

Ejecuta subprocesos para Terraform (plan, validate).
"""

from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from mcp_shared.errors import McpError


def tf_run(project_path: Path, args: str) -> dict[str, Any]:
    """Ejecuta un comando de Terraform."""
    tf_bin = shutil.which("terraform")

    if not tf_bin:
        # Mock mode
        return {
            "mode": "mock",
            "status": "success",
            "output": f"Mock execution of terraform {args}.\nPlan: 1 to add, 0 to change, 0 to destroy.",
            "message": "Terraform CLI no encontrado. Simulando ejecución."
        }

    try:
        cmd = [tf_bin, *shlex.split(args)]
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True
        )
        return {
            "mode": "real",
            "status": "success" if result.returncode == 0 else "error",
            "output": result.stdout[:2000] + ("\n..." if len(result.stdout) > 2000 else ""),
            "error": result.stderr[:2000] if result.stderr else None
        }
    except Exception as exc:
        raise McpError(f"Fallo al ejecutar Terraform: {exc}") from exc


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def tf_init(project_path: Path, backend: bool = True, upgrade: bool = False) -> dict[str, Any]:
    """Ejecuta terraform init."""
    args = "init"
    if not backend:
        args += " -backend=false"
    if upgrade:
        args += " -upgrade"
    return tf_run(project_path, args)


def tf_plan(project_path: Path, destroy: bool = False, var_file: str | None = None) -> dict[str, Any]:
    """Ejecuta terraform plan."""
    args = "plan"
    if destroy:
        args += " -destroy"
    if var_file:
        args += f" -var-file={var_file}"
    return tf_run(project_path, args)


def tf_validate(project_path: Path) -> dict[str, Any]:
    """Ejecuta terraform validate."""
    return tf_run(project_path, "validate")


def tf_apply(project_path: Path, auto_approve: bool = False, var_file: str | None = None) -> dict[str, Any]:
    """Ejecuta terraform apply."""
    args = "apply"
    if auto_approve:
        args += " -auto-approve"
    if var_file:
        args += f" -var-file={var_file}"
    return tf_run(project_path, args)


def tf_destroy(project_path: Path, auto_approve: bool = False) -> dict[str, Any]:
    """Ejecuta terraform destroy."""
    args = "destroy"
    if auto_approve:
        args += " -auto-approve"
    return tf_run(project_path, args)


def tf_fmt(project_path: Path, check: bool = False, recursive: bool = True) -> dict[str, Any]:
    """Ejecuta terraform fmt."""
    args = "fmt"
    if check:
        args += " -check"
    if recursive:
        args += " -recursive"
    return tf_run(project_path, args)


def tf_show(project_path: Path, plan_file: str = "tfplan") -> dict[str, Any]:
    """Ejecuta terraform show."""
    return tf_run(project_path, f"show {plan_file}")


def tf_output(project_path: Path, json_format: bool = True) -> dict[str, Any]:
    """Ejecuta terraform output."""
    args = "output"
    if json_format:
        args += " -json"
    return tf_run(project_path, args)


def tf_state_list(project_path: Path) -> dict[str, Any]:
    """Lista recursos en el state."""
    return tf_run(project_path, "state list")


def tf_workspace_list(project_path: Path) -> dict[str, Any]:
    """Lista workspaces."""
    return tf_run(project_path, "workspace list")


def tf_workspace_select(project_path: Path, workspace: str) -> dict[str, Any]:
    """Selecciona un workspace."""
    if not workspace.strip():
        raise McpError("Workspace no puede estar vacio.")
    return tf_run(project_path, f"workspace select {workspace}")


def tf_import(project_path: Path, resource_addr: str, resource_id: str) -> dict[str, Any]:
    """Importa un recurso al state."""
    if not resource_addr.strip() or not resource_id.strip():
        raise McpError("resource_addr y resource_id no pueden estar vacios.")
    return tf_run(project_path, f"import {resource_addr} {resource_id}")


def tf_taint(project_path: Path, resource_addr: str) -> dict[str, Any]:
    """Marca un recurso como tainted."""
    if not resource_addr.strip():
        raise McpError("resource_addr no puede estar vacio.")
    return tf_run(project_path, f"taint {resource_addr}")


def tf_graph(project_path: Path, plan: bool = False) -> dict[str, Any]:
    """Genera el grafo de dependencias."""
    args = "graph"
    if plan:
        args += " -type=plan"
    return tf_run(project_path, args)
