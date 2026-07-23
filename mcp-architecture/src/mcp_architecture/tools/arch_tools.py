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


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def analyze_circular_deps(project_path: Path, target: str = "") -> dict[str, Any]:
    """Detecta dependencias circulares entre modulos Python."""
    import os
    from collections import defaultdict

    search_path = project_path / target if target else project_path
    if not search_path.exists():
        raise FileNotFoundError(str(search_path))

    deps: dict[str, set[str]] = defaultdict(set)

    def scan_file(fp: Path) -> None:
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
        except Exception:
            pass

    if search_path.is_file():
        scan_file(search_path)
    else:
        for root, _dirs, files in os.walk(str(search_path)):
            for f in files:
                if f.endswith(".py"):
                    scan_file(Path(root) / f)

    circular: list[dict[str, Any]] = []
    for mod, dep_list in deps.items():
        for dep in dep_list:
            if dep in deps and mod in deps[dep]:
                circular.append({"module_a": mod, "module_b": dep, "type": "circular"})

    return {
        "target": target or str(project_path),
        "modules": len(deps),
        "circular_dependencies": circular,
        "has_circular": len(circular) > 0,
    }


def analyze_layering(project_path: Path, target: str = "") -> dict[str, Any]:
    """Analiza si el proyecto sigue una estructura por capas."""
    import os

    search_path = project_path / target if target else project_path
    if not search_path.exists():
        raise FileNotFoundError(str(search_path))

    layers = {"presentation": [], "business": [], "data": [], "utils": []}
    layer_keywords = {
        "presentation": ["api", "controller", "view", "endpoint", "route", "handler"],
        "business": ["service", "domain", "model", "logic", "usecase", "use_case"],
        "data": ["repository", "dao", "db", "database", "orm", "entity", "schema"],
        "utils": ["util", "helper", "common", "shared", "config"],
    }

    for root, dirs, files in os.walk(str(search_path)):
        dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".venv", "venv"]]
        for f in files:
            if f.endswith(".py"):
                rel_path = str(Path(root).relative_to(project_path) / f)
                path_lower = rel_path.lower()
                for layer, keywords in layer_keywords.items():
                    if any(kw in path_lower for kw in keywords):
                        layers[layer].append(rel_path)

    return {
        "target": target or str(project_path),
        "layers": layers,
        "layer_count": sum(1 for v in layers.values() if v),
        "has_clear_layers": sum(1 for v in layers.values() if v) >= 3,
    }


def find_entry_points(project_path: Path, target: str = "") -> list[dict[str, Any]]:
    """Encuentra puntos de entrada del proyecto (main, app, __main__)."""
    import os

    search_path = project_path / target if target else project_path
    if not search_path.exists():
        raise FileNotFoundError(str(search_path))

    entry_patterns = ["main.py", "__main__.py", "app.py", "run.py", "manage.py", "wsgi.py", "asgi.py"]
    results: list[dict[str, Any]] = []

    for root, _dirs, files in os.walk(str(search_path)):
        for f in files:
            if f in entry_patterns:
                fp = Path(root) / f
                rel = str(fp.relative_to(project_path))
                results.append({
                    "file": rel,
                    "type": f.replace(".py", ""),
                    "size": fp.stat().st_size if fp.exists() else 0,
                })

    return results


def analyze_coupling(project_path: Path, target: str = "") -> dict[str, Any]:
    """Analiza el acoplamiento entre modulos (afferent/efferent coupling)."""
    import os
    from collections import defaultdict

    search_path = project_path / target if target else project_path
    if not search_path.exists():
        raise FileNotFoundError(str(search_path))

    efferent: dict[str, set[str]] = defaultdict(set)
    afferent: dict[str, set[str]] = defaultdict(set)

    def scan_file(fp: Path) -> None:
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
            mod_name = str(fp.relative_to(project_path)).replace("/", ".").replace(".py", "")
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        efferent[mod_name].add(alias.name)
                        afferent[alias.name].add(mod_name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        efferent[mod_name].add(node.module)
                        afferent[node.module].add(mod_name)
        except Exception:
            pass

    if search_path.is_file():
        scan_file(search_path)
    else:
        for root, _dirs, files in os.walk(str(search_path)):
            for f in files:
                if f.endswith(".py"):
                    scan_file(Path(root) / f)

    coupling: list[dict[str, Any]] = []
    for mod in set(list(efferent.keys()) + list(afferent.keys())):
        ce = len(efferent.get(mod, set()))
        ca = len(afferent.get(mod, set()))
        instability = round(ce / (ca + ce), 2) if (ca + ce) > 0 else 0
        coupling.append({
            "module": mod,
            "efferent": ce,
            "afferent": ca,
            "instability": instability,
        })

    return {
        "target": target or str(project_path),
        "modules": coupling,
        "total_modules": len(coupling),
        "avg_coupling": round(sum(c["efferent"] for c in coupling) / len(coupling), 2) if coupling else 0,
    }


def analyze_cohesion(project_path: Path, target_file: str) -> dict[str, Any]:
    """Analiza la cohesion de un archivo Python (LCOM heuristico)."""
    file_path = project_path / target_file
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))
    if not file_path.name.endswith(".py"):
        raise ValidationError(field="target_file", message="El analisis requiere archivos Python (.py).")

    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    classes: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods: list[set[str]] = []
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    used = set()
                    for sub in ast.walk(child):
                        if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name):
                            if sub.value.id == "self":
                                used.add(sub.attr)
                    methods.append(used)

            if len(methods) < 2:
                cohesion_score = 1.0
            else:
                shared = 0
                total = 0
                for i in range(len(methods)):
                    for j in range(i + 1, len(methods)):
                        total += 1
                        if methods[i] & methods[j]:
                            shared += 1
                cohesion_score = round(shared / total, 2) if total > 0 else 1.0

            classes.append({
                "name": node.name,
                "methods": len(methods),
                "cohesion_score": cohesion_score,
                "cohesion_level": "high" if cohesion_score > 0.7 else "medium" if cohesion_score > 0.3 else "low",
            })

    return {
        "file": target_file,
        "classes": classes,
        "total_classes": len(classes),
        "avg_cohesion": round(sum(c["cohesion_score"] for c in classes) / len(classes), 2) if classes else 0,
    }


def count_classes_functions(project_path: Path, target: str = "") -> dict[str, Any]:
    """Cuenta clases y funciones en un archivo o directorio."""
    import os

    search_path = project_path / target if target else project_path
    if not search_path.exists():
        raise FileNotFoundError(str(search_path))

    total_classes = 0
    total_functions = 0
    total_async_functions = 0
    files_scanned = 0

    def scan_file(fp: Path) -> None:
        nonlocal total_classes, total_functions, total_async_functions, files_scanned
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    total_classes += 1
                elif isinstance(node, ast.AsyncFunctionDef):
                    total_async_functions += 1
                elif isinstance(node, ast.FunctionDef):
                    total_functions += 1
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
        "classes": total_classes,
        "functions": total_functions,
        "async_functions": total_async_functions,
        "total_callables": total_classes + total_functions + total_async_functions,
    }


def find_largest_files(project_path: Path, target: str = "", top_n: int = 10) -> list[dict[str, Any]]:
    """Encuentra los archivos Python mas grandes por lineas de codigo."""
    import os

    search_path = project_path / target if target else project_path
    if not search_path.exists():
        raise FileNotFoundError(str(search_path))

    results: list[dict[str, Any]] = []

    def count_lines(fp: Path) -> int:
        try:
            return sum(1 for _ in fp.read_text(encoding="utf-8").splitlines())
        except Exception:
            return 0

    if search_path.is_file():
        results.append({"file": str(search_path.relative_to(project_path)), "lines": count_lines(search_path)})
    else:
        for root, _dirs, files in os.walk(str(search_path)):
            for f in files:
                if f.endswith(".py"):
                    fp = Path(root) / f
                    results.append({"file": str(fp.relative_to(project_path)), "lines": count_lines(fp)})

    results.sort(key=lambda x: x["lines"], reverse=True)
    return results[:top_n]


def analyze_inheritance(project_path: Path, target_file: str) -> dict[str, Any]:
    """Analiza la jerarquia de herencia de un archivo Python."""
    file_path = project_path / target_file
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))
    if not file_path.name.endswith(".py"):
        raise ValidationError(field="target_file", message="El analisis requiere archivos Python (.py).")

    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    classes: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else "...")
            classes.append({
                "name": node.name,
                "bases": bases,
                "depth": len(bases),
                "is_abstract": any(b == "ABC" for b in bases),
            })

    return {
        "file": target_file,
        "classes": classes,
        "total_classes": len(classes),
        "max_depth": max((c["depth"] for c in classes), default=0),
        "abstract_classes": sum(1 for c in classes if c["is_abstract"]),
    }


def detect_code_smells(project_path: Path, target_file: str) -> dict[str, Any]:
    """Detecta code smells en un archivo Python."""
    file_path = project_path / target_file
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))
    if not file_path.name.endswith(".py"):
        raise ValidationError(field="target_file", message="El analisis requiere archivos Python (.py).")

    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    smells: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            line_count = (node.end_lineno or 0) - (node.lineno or 0)
            if line_count > 50:
                smells.append({"type": "LONG_METHOD", "entity": node.name, "lines": line_count, "line": node.lineno})
            if len(node.args.args) > 5:
                smells.append({"type": "LONG_PARAMETER_LIST", "entity": node.name, "args": len(node.args.args), "line": node.lineno})
            nesting = 0
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    nesting += 1
            if nesting > 5:
                smells.append({"type": "DEEP_NESTING", "entity": node.name, "nesting": nesting, "line": node.lineno})
        elif isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            line_count = (node.end_lineno or 0) - (node.lineno or 0)
            if len(methods) > 10:
                smells.append({"type": "GOD_CLASS", "entity": node.name, "methods": len(methods), "line": node.lineno})
            if line_count > 300:
                smells.append({"type": "LARGE_CLASS", "entity": node.name, "lines": line_count, "line": node.lineno})

    return {
        "file": target_file,
        "smells": smells,
        "total_smells": len(smells),
        "is_clean": len(smells) == 0,
    }


def generate_architecture_report(project_path: Path, target: str = "") -> dict[str, Any]:
    """Genera un reporte arquitectonico completo del proyecto."""
    tree_result = get_project_tree(project_path, max_depth=2)
    coupling_result = analyze_coupling(project_path, target)
    layering_result = analyze_layering(project_path, target)
    entry_points = find_entry_points(project_path, target)
    largest = find_largest_files(project_path, target, top_n=5)

    return {
        "project_tree": tree_result[:500],
        "coupling": {
            "total_modules": coupling_result["total_modules"],
            "avg_coupling": coupling_result["avg_coupling"],
        },
        "layering": {
            "layer_count": layering_result["layer_count"],
            "has_clear_layers": layering_result["has_clear_layers"],
        },
        "entry_points": len(entry_points),
        "largest_files": largest,
        "target": target or "all",
    }


def analyze_module_dependencies(project_path: Path, target: str = "") -> dict[str, Any]:
    """Analiza dependencias a nivel de modulo en todo el proyecto."""
    import os
    from collections import defaultdict

    search_path = project_path / target if target else project_path
    if not search_path.exists():
        raise FileNotFoundError(str(search_path))

    internal_deps: dict[str, set[str]] = defaultdict(set)
    external_deps: dict[str, set[str]] = defaultdict(set)

    def scan_file(fp: Path) -> None:
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
            mod_name = str(fp.relative_to(project_path)).replace("/", ".").replace(".py", "")
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith(mod_name.split(".")[0]) or "." in alias.name and alias.name.split(".")[0] in [d.name for d in project_path.iterdir() if d.is_dir()]:
                            internal_deps[mod_name].add(alias.name)
                        else:
                            external_deps[mod_name].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if node.module.startswith("."):
                            internal_deps[mod_name].add(node.module)
                        else:
                            external_deps[mod_name].add(node.module)
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
        "internal_dependencies": {k: sorted(v) for k, v in internal_deps.items()},
        "external_dependencies": {k: sorted(v) for k, v in external_deps.items()},
        "total_internal": sum(len(v) for v in internal_deps.values()),
        "total_external": sum(len(v) for v in external_deps.values()),
    }


def get_module_summary(project_path: Path, target: str = "") -> dict[str, Any]:
    """Genera un resumen rapido de metricas de un modulo o directorio."""
    count_result = count_classes_functions(project_path, target)
    largest = find_largest_files(project_path, target, top_n=3)
    entry_pts = find_entry_points(project_path, target)

    return {
        "target": target or str(project_path),
        "files_scanned": count_result["files_scanned"],
        "classes": count_result["classes"],
        "functions": count_result["functions"],
        "async_functions": count_result["async_functions"],
        "total_callables": count_result["total_callables"],
        "largest_files": largest,
        "entry_points": len(entry_pts),
    }
