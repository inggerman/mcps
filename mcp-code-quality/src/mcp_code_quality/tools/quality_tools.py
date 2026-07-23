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


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def check_complexity(project_path: Path, file_path: str) -> dict[str, Any]:
    """Analiza la complejidad ciclomatica de un archivo Python."""
    if not file_path or not file_path.strip():
        raise ValidationError(field="file_path", message="Debes especificar un archivo.")
    full_path = project_path / file_path
    if not full_path.exists():
        raise ValidationError(field="file_path", message=f"Archivo no encontrado: {file_path}")

    import ast

    try:
        source = full_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValidationError(field="file_path", message=f"Error de sintaxis: {exc}") from exc

    functions: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "complexity": complexity,
                "severity": "low" if complexity <= 5 else "moderate" if complexity <= 10 else "high" if complexity <= 15 else "critical",
            })

    avg = round(sum(f["complexity"] for f in functions) / len(functions), 2) if functions else 0
    return {
        "file": file_path,
        "functions": functions,
        "total_functions": len(functions),
        "avg_complexity": avg,
        "max_complexity": max((f["complexity"] for f in functions), default=0),
    }


def count_lines(project_path: Path, target: str = "") -> dict[str, Any]:
    """Cuenta lineas de codigo en un archivo o directorio."""
    import os

    search_path = project_path / target if target else project_path
    if not search_path.exists():
        raise ValidationError(field="target", message=f"No encontrado: {target}")

    total_lines = 0
    code_lines = 0
    blank_lines = 0
    comment_lines = 0
    file_count = 0

    def process_file(fp: Path) -> None:
        nonlocal total_lines, code_lines, blank_lines, comment_lines, file_count
        try:
            for line in fp.read_text(encoding="utf-8").splitlines():
                total_lines += 1
                stripped = line.strip()
                if not stripped:
                    blank_lines += 1
                elif stripped.startswith("#"):
                    comment_lines += 1
                else:
                    code_lines += 1
            file_count += 1
        except Exception:
            pass

    if search_path.is_file():
        process_file(search_path)
    else:
        for root, _dirs, files in os.walk(str(search_path)):
            for f in files:
                if f.endswith(".py"):
                    process_file(Path(root) / f)

    return {
        "target": target or str(project_path),
        "files": file_count,
        "total_lines": total_lines,
        "code_lines": code_lines,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
    }


def find_todos(project_path: Path, target: str = "") -> list[dict[str, Any]]:
    """Busca TODOs, FIXMEs y HACKs en el codigo."""
    import os
    import re

    pattern = re.compile(r"#\s*(TODO|FIXME|HACK|XXX|BUG)[:\s]*(.*)", re.IGNORECASE)
    search_path = project_path / target if target else project_path
    if not search_path.exists():
        raise ValidationError(field="target", message=f"No encontrado: {target}")

    results: list[dict[str, Any]] = []

    def scan_file(fp: Path) -> None:
        try:
            for i, line in enumerate(fp.read_text(encoding="utf-8").splitlines(), 1):
                m = pattern.search(line)
                if m:
                    results.append({
                        "file": str(fp.relative_to(project_path)),
                        "line": i,
                        "type": m.group(1).upper(),
                        "text": m.group(2).strip(),
                    })
        except Exception:
            pass

    if search_path.is_file():
        scan_file(search_path)
    else:
        for root, _dirs, files in os.walk(str(search_path)):
            for f in files:
                if f.endswith(".py"):
                    scan_file(Path(root) / f)

    return results


def check_imports(project_path: Path, file_path: str) -> dict[str, Any]:
    """Analiza los imports de un archivo Python."""
    if not file_path or not file_path.strip():
        raise ValidationError(field="file_path", message="Debes especificar un archivo.")
    full_path = project_path / file_path
    if not full_path.exists():
        raise ValidationError(field="file_path", message=f"Archivo no encontrado: {file_path}")

    import ast

    try:
        source = full_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValidationError(field="file_path", message=f"Error de sintaxis: {exc}") from exc

    imports: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"type": "import", "module": alias.name, "line": node.lineno})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append({"type": "from", "module": module, "name": alias.name, "line": node.lineno})

    return {
        "file": file_path,
        "imports": imports,
        "total": len(imports),
        "standard": sum(1 for i in imports if not i["module"].startswith(".")),
        "relative": sum(1 for i in imports if i["module"].startswith(".")),
    }


def analyze_dependencies(project_path: Path, target: str = "") -> dict[str, Any]:
    """Analiza dependencias entre modulos Python."""
    import ast
    import os
    from collections import defaultdict

    search_path = project_path / target if target else project_path
    if not search_path.exists():
        raise ValidationError(field="target", message=f"No encontrado: {target}")

    deps: dict[str, set[str]] = defaultdict(set)
    files_scanned = 0

    def scan_file(fp: Path) -> None:
        nonlocal files_scanned
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
            mod_name = str(fp.relative_to(project_path)).replace("/", ".").replace(".py", "")
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        deps[mod_name].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        deps[mod_name].add(node.module)
            files_scanned += 1
        except Exception:
            pass

    if search_path.is_file():
        scan_file(search_path)
    else:
        for root, _dirs, files in os.walk(str(search_path)):
            for f in files:
                if f.endswith(".py"):
                    scan_file(Path(root) / f)

    return {
        "target": target or str(project_path),
        "files_scanned": files_scanned,
        "modules": {k: sorted(v) for k, v in deps.items()},
        "total_modules": len(deps),
        "total_dependencies": sum(len(v) for v in deps.values()),
    }


def run_type_check(project_path: Path, target: str = "") -> dict[str, Any]:
    """Ejecuta mypy para verificacion de tipos."""
    cmd = "uv run mypy"
    if target:
        cmd += f" {shlex.quote(target)}"
    success, output = _run_command(cmd, project_path)
    return {
        "success": success,
        "output": output,
        "command_run": cmd,
    }


def run_security_scan(project_path: Path, target: str = "") -> dict[str, Any]:
    """Ejecuta bandit para escaneo de seguridad."""
    cmd = "uv run bandit -r"
    if target:
        cmd += f" {shlex.quote(target)}"
    else:
        cmd += " ."
    success, output = _run_command(cmd, project_path)
    return {
        "success": success,
        "output": output,
        "command_run": cmd,
    }


def check_coverage(project_path: Path, target: str = "") -> dict[str, Any]:
    """Ejecuta pytest con cobertura."""
    cmd = "uv run pytest --cov"
    if target:
        cmd += f" {shlex.quote(target)}"
    cmd += " --cov-report=term-missing"
    success, output = _run_command(cmd, project_path)
    return {
        "success": success,
        "output": output,
        "command_run": cmd,
    }


def find_dead_code(project_path: Path, target: str = "") -> dict[str, Any]:
    """Ejecuta vulture para encontrar codigo muerto."""
    cmd = "uv run vulture"
    if target:
        cmd += f" {shlex.quote(target)}"
    else:
        cmd += " ."
    success, output = _run_command(cmd, project_path)
    return {
        "success": success,
        "output": output,
        "command_run": cmd,
    }


def check_dependencies_versions(project_path: Path) -> dict[str, Any]:
    """Verifica versiones de dependencias instaladas."""
    cmd = "uv pip list"
    success, output = _run_command(cmd, project_path)
    return {
        "success": success,
        "output": output,
        "command_run": cmd,
    }


def audit_dependencies(project_path: Path) -> dict[str, Any]:
    """Ejecuta pip-audit para auditar vulnerabilidades."""
    cmd = "uv run pip-audit"
    success, output = _run_command(cmd, project_path)
    return {
        "success": success,
        "output": output,
        "command_run": cmd,
    }


def generate_quality_report(project_path: Path, target: str = "") -> dict[str, Any]:
    """Genera un reporte completo de calidad: lint, format check, tests."""
    lint_result = run_lint(project_path, "uv run ruff check", target)
    format_result = run_format(project_path, "uv run ruff format", check_only=True, target=target)
    test_result = run_tests(project_path, "uv run pytest", target)

    return {
        "lint": {"success": lint_result["success"], "output": lint_result["output"][:500]},
        "format": {"success": format_result["success"], "output": format_result["output"][:500]},
        "tests": {"success": test_result["success"], "output": test_result["output"][:500]},
        "overall_success": lint_result["success"] and format_result["success"] and test_result["success"],
        "target": target or "all",
    }
