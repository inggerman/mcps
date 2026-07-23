"""Resources de solo lectura para mcp-code-quality."""

from __future__ import annotations

import json


def quality_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-code-quality",
            "version": "1.0.0",
            "linter_cmd": "uv run ruff check",
            "formatter_cmd": "uv run ruff format",
            "test_cmd": "uv run pytest",
        },
        indent=2,
        ensure_ascii=False,
    )


def quality_linting_guide() -> str:
    return (
        "# Guia de linting\n\n"
        "## Ruff\n"
        "- Linter rapido para Python\n"
        "- Reglas: E (pycodestyle), F (pyflakes), I (isort)\n"
        "- Config en pyproject.toml o ruff.toml\n\n"
        "## Reglas comunes\n"
        "- E501: linea muy larga\n"
        "- F401: import no usado\n"
        "- F811: redefinicion de funcion\n"
        "- I001: import desordenado\n\n"
        "## Comandos\n"
        "- run_lint() — lint todo el proyecto\n"
        "- run_lint(target='src/') — lint directorio\n"
        "- run_lint(target='file.py') — lint archivo"
    )


def quality_formatting_guide() -> str:
    return (
        "# Guia de formateo\n\n"
        "## Ruff format\n"
        "- Formateador rapido compatible con Black\n"
        "- Config en pyproject.toml\n\n"
        "## Opciones\n"
        "- line-length: 88 (default)\n"
        "- indent-style: space\n"
        "- quote-style: double\n\n"
        "## Comandos\n"
        "- run_format() — formatear todo\n"
        "- run_format(check_only=True) — verificar sin modificar\n"
        "- run_format(target='file.py') — formatear archivo"
    )


def quality_testing_guide() -> str:
    return (
        "# Guia de testing\n\n"
        "## Pytest\n"
        "- Framework de testing para Python\n"
        "- Descubrimiento automatico: test_*.py\n"
        "- Fixtures para setup/teardown\n\n"
        "## Comandos\n"
        "- run_tests() — ejecutar todos los tests\n"
        "- run_tests(target='tests/test_foo.py') — test especifico\n"
        "- run_tests(target='-k test_name') — por nombre\n\n"
        "## Cobertura\n"
        "- pytest --cov=src --cov-report=term-missing\n"
        "- Meta: >80% cobertura"
    )


def quality_best_practices() -> str:
    return (
        "# Mejores practicas de calidad\n\n"
        "1. Lint antes de commit\n"
        "2. Formatear consistentemente\n"
        "3. Tests para cada feature\n"
        "4. Cobertura >80%\n"
        "5. Sin warnings del linter\n"
        "6. Type hints en todas las funciones\n"
        "7. Docstrings en funciones publicas\n"
        "8. Nombres descriptivos\n"
        "9. Funciones cortas (<50 lineas)\n"
        "10. Sin codigo muerto"
    )


def quality_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- run_lint(target)\n"
        "- run_format(check_only, target)\n"
        "- run_tests(target)\n"
        "- check_complexity(file_path)\n"
        "- count_lines(target)\n"
        "- find_todos(target)\n"
        "- check_imports(file_path)\n"
        "- analyze_dependencies(target)\n\n"
        "## Variables .env\n"
        "- CQ_PROJECT_PATH\n"
        "- CQ_LINTER_CMD\n"
        "- CQ_FORMATTER_CMD\n"
        "- CQ_TEST_CMD"
    )


def quality_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "Comando no encontrado"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def quality_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## Linter falla\n"
        "- Verifica CQ_LINTER_CMD\n"
        "- Revisa que ruff este instalado\n"
        "- Usa run_lint(target='file.py') para aislar\n\n"
        "## Formateador no cambia\n"
        "- Verifica CQ_FORMATTER_CMD\n"
        "- Usa check_only=True para ver que cambiaria\n\n"
        "## Tests fallan\n"
        "- Verifica CQ_TEST_CMD\n"
        "- Usa run_tests(target='tests/test_x.py') para aislar\n"
        "- Revisa dependencias del test"
    )


def quality_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Ejemplo 1: Lint proyecto\n"
        "run_lint()\n\n"
        "## Ejemplo 2: Formatear sin modificar\n"
        "run_format(check_only=True)\n\n"
        "## Ejemplo 3: Tests especificos\n"
        "run_tests(target='tests/test_server.py')\n\n"
        "## Ejemplo 4: Complejidad\n"
        "check_complexity(file_path='src/main.py')\n\n"
        "## Ejemplo 5: Contar lineas\n"
        "count_lines(target='src/')"
    )


def quality_metrics_guide() -> str:
    return (
        "# Metricas de calidad\n\n"
        "## Complejidad ciclomatica\n"
        "- <5: simple\n"
        "- 5-10: moderado\n"
        "- >10: complejo (refactorizar)\n"
        "- >15: muy complejo (critico)\n\n"
        "## Lineas de codigo (LOC)\n"
        "- Funciones: <50 LOC ideal\n"
        "- Clases: <300 LOC ideal\n"
        "- Modulos: <500 LOC ideal\n\n"
        "## Cobertura\n"
        "- >90%: excelente\n"
        "- 80-90%: bueno\n"
        "- 60-80%: regular\n"
        "- <60%: deficiente"
    )


def quality_ci_integration() -> str:
    return (
        "# Integracion con CI/CD\n\n"
        "## GitHub Actions\n"
        "- run_lint() en cada PR\n"
        "- run_format(check_only=True) en cada PR\n"
        "- run_tests() en cada push\n\n"
        "## Pre-commit hooks\n"
        "- ruff check --fix\n"
        "- ruff format\n"
        "- pytest -x\n\n"
        "## Gates de calidad\n"
        "- 0 errores de lint\n"
        "- 0 archivos sin formatear\n"
        "- 0 tests fallidos\n"
        "- cobertura >80%"
    )


def quality_code_smells() -> str:
    return (
        "# Code smells\n\n"
        "## Funciones largas\n"
        "- Mas de 50 lineas\n"
        "- Solucion: extraer metodos\n\n"
        "## Clases grandes\n"
        "- Mas de 300 lineas\n"
        "- Solucion: separar responsabilidades\n\n"
        "## Duplicacion\n"
        "- Codigo repetido en 3+ lugares\n"
        "- Solucion: extraer funcion comun\n\n"
        "## Parametros largos\n"
        "- Mas de 4 parametros\n"
        "- Solucion: usar objeto parametro\n\n"
        "## Complejidad alta\n"
        "- Muchos if/else anidados\n"
        "- Solucion: early return, polimorfismo"
    )


def quality_security_checks() -> str:
    return (
        "# Chequeos de seguridad\n\n"
        "## Ruff security (S)\n"
        "- S101: assert statements\n"
        "- S102: exec/builtin\n"
        "- S103: bad file permissions\n"
        "- S104: hardcoded bind all interfaces\n"
        "- S105: hardcoded password\n"
        "- S106: hardcoded password argument\n"
        "- S301: pickle unsafe\n"
        "- S307: eval unsafe\n\n"
        "## Bandit\n"
        "- pip install bandit\n"
        "- bandit -r src/\n\n"
        "## pip-audit\n"
        "- pip-audit para vulnerabilidades\n"
        "- Audit dependencies"
    )


def quality_type_checking() -> str:
    return (
        "# Type checking\n\n"
        "## mypy\n"
        "- Verificador de tipos estatico\n"
        "- Config en mypy.ini o pyproject.toml\n\n"
        "## Comando\n"
        "- uv run mypy src/\n\n"
        "## Type hints\n"
        "- Usar typing para tipos complejos\n"
        "- from __future__ import annotations\n"
        "- Evitar Any cuando sea posible\n\n"
        "## Pyright\n"
        "- Alternativa mas rapida\n"
        "- Integracion con VS Code"
    )


def quality_refactoring_guide() -> str:
    return (
        "# Guia de refactoring\n\n"
        "## Cuando refactorizar\n"
        "- Complejidad ciclomatica > 10\n"
        "- Funciones > 50 lineas\n"
        "- Duplicacion de codigo\n"
        "- Nombres poco descriptivos\n\n"
        "## Tecnicas\n"
        "- Extract Method: separar bloques en funciones\n"
        "- Extract Class: separar responsabilidades\n"
        "- Rename: nombres mas claros\n"
        "- Inline: eliminar indireccion innecesaria\n"
        "- Move: mover metodo a clase correcta\n\n"
        "## Pasos seguros\n"
        "1. Tener tests que pasen\n"
        "2. Hacer cambios pequenos\n"
        "3. Verificar tests despues de cada cambio\n"
        "4. Usar git para revertir si algo falla"
    )
