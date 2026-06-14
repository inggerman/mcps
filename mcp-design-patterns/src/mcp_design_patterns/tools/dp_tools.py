"""
Lógica de mcp-design-patterns.

Evalúa AST en busca de métricas que indiquen antipatrones (ej. God Object).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from mcp_shared.errors import FileNotFoundError, ParseError


def analyze_code_patterns(file_path: Path) -> dict[str, Any]:
    """
    Analiza un archivo en busca de antipatrones (métricas simples):
    - God Object: Clase con demasiados métodos (> 10).
    - Long Method: Método con demasiadas líneas (> 50).
    - Too Many Arguments: Función con > 5 argumentos.
    """
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(str(file_path))

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except Exception as exc:
        raise ParseError(source=str(file_path), reason=str(exc)) from exc

    antipatterns = []

    for node in ast.walk(tree):
        # Evaluar clases
        if isinstance(node, ast.ClassDef):
            methods = [
                n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            if len(methods) > 10:
                antipatterns.append(
                    {
                        "type": "God Object",
                        "entity": node.name,
                        "line": node.lineno,
                        "detail": f"Clase tiene {len(methods)} métodos. Considera SRP (Single Responsibility Principle).",
                    }
                )

        # Evaluar funciones
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Demasiados argumentos
            if len(node.args.args) > 5:
                antipatterns.append(
                    {
                        "type": "Too Many Arguments",
                        "entity": node.name,
                        "line": node.lineno,
                        "detail": f"Función recibe {len(node.args.args)} argumentos. Considera usar un objeto de parámetros (DTO).",
                    }
                )

            # Método muy largo (aproximación)
            if (
                hasattr(node, "end_lineno")
                and node.end_lineno is not None
                and node.lineno is not None
            ):
                lines_count = node.end_lineno - node.lineno
                if lines_count > 50:
                    antipatterns.append(
                        {
                            "type": "Long Method",
                            "entity": node.name,
                            "line": node.lineno,
                            "detail": f"Función tiene aprox {lines_count} líneas. Divídela en funciones más pequeñas.",
                        }
                    )

    return {
        "file": file_path.name,
        "antipatterns_found": len(antipatterns),
        "antipatterns": antipatterns,
    }


def suggest_design_pattern(problem_description: str) -> dict[str, str]:
    """Sugiere patrones clásicos basados en keywords simples (simulación ligera)."""
    desc = problem_description.lower()

    if (
        "global" in desc
        or "única instancia" in desc
        or "instancia compartida" in desc
        or "single instance" in desc
    ):
        return {
            "pattern": "Singleton",
            "type": "Creational",
            "advice": "Cuidado con estado global mutable.",
        }
    if "crear" in desc and ("dinámico" in desc or "depende" in desc or "factory" in desc):
        return {
            "pattern": "Factory Method / Abstract Factory",
            "type": "Creational",
            "advice": "Desacopla la creación.",
        }
    if "notificar" in desc or "eventos" in desc or "suscrip" in desc:
        return {"pattern": "Observer", "type": "Behavioral", "advice": "Ideal para 1-a-N."}
    if "estados" in desc or "máquina" in desc:
        return {"pattern": "State", "type": "Behavioral", "advice": "Evita switch/case gigantes."}

    return {
        "pattern": "Unknown",
        "advice": "Describe mejor si necesitas instanciación, comportamiento o estructura.",
    }
