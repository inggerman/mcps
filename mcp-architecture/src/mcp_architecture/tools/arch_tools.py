"""
Lógica de negocio de mcp-architecture.

Analiza estructura de directorios, dependencias mediante AST y heurísticas de principios SOLID.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from mcp_shared.errors import FileNotFoundError, ParseError, ValidationError


def get_project_tree(
    project_path: Path, max_depth: int = 3, ignore_dirs: list[str] | None = None
) -> str:
    """Retorna un string con el árbol de directorios del proyecto."""
    if not project_path.exists():
        raise FileNotFoundError(str(project_path))

    _ignore = ignore_dirs or [
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
    ]

    lines = []

    def _walk(dir_path: Path, current_depth: int, prefix: str = "") -> None:
        if current_depth > max_depth:
            return

        try:
            items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return

        # Filtrar ignorados
        items = [i for i in items if i.name not in _ignore]

        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{item.name}")

            if item.is_dir():
                extension = "    " if is_last else "│   "
                _walk(item, current_depth + 1, prefix + extension)

    lines.append(project_path.name or ".")
    _walk(project_path, 1)

    return "\n".join(lines)


def analyze_dependencies(project_path: Path, target_file: str) -> dict[str, Any]:
    """Analiza los imports de un archivo usando AST para descubrir dependencias."""
    file_path = project_path / target_file
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    if not file_path.name.endswith(".py"):
        raise ValidationError(
            field="target_file", message="El análisis AST requiere archivos Python (.py)."
        )

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    imports = []
    from_imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                from_imports.append({"module": module, "name": alias.name})

    return {
        "file": target_file,
        "absolute_imports": imports,
        "from_imports": from_imports,
        "total_dependencies": len(imports) + len(from_imports),
    }


def analyze_solid_heuristics(project_path: Path, target_file: str) -> dict[str, Any]:
    """Analiza el código en busca de posibles violaciones a los principios SOLID."""
    file_path = project_path / target_file
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    if not file_path.name.endswith(".py"):
        raise ValidationError(
            field="target_file", message="El análisis AST requiere archivos Python (.py)."
        )

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    classes = []
    functions = []
    warnings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [
                n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            lines = (node.end_lineno or 0) - (node.lineno or 0)

            # Heurística SRP (Single Responsibility Principle)
            if len(methods) > 10 or lines > 300:
                warnings.append(
                    {
                        "type": "SRP_WARNING",
                        "entity": node.name,
                        "reason": f"Clase demasiado grande ({lines} líneas, {len(methods)} métodos). Posible violación de Responsabilidad Única.",
                    }
                )

            classes.append(
                {
                    "name": node.name,
                    "methods": len(methods),
                    "lines": lines,
                }
            )

        elif isinstance(node, ast.FunctionDef):
            args_count = len(node.args.args)
            if args_count > 5:
                warnings.append(
                    {
                        "type": "TOO_MANY_ARGS",
                        "entity": node.name,
                        "reason": f"Función recibe demasiados argumentos ({args_count}).",
                    }
                )
            functions.append({"name": node.name, "args": args_count})

    return {
        "file": target_file,
        "classes_analyzed": len(classes),
        "functions_analyzed": len(functions),
        "warnings": warnings,
        "is_healthy": len(warnings) == 0,
    }
