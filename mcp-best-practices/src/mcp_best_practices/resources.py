"""Resources de solo lectura para mcp-best-practices."""

from __future__ import annotations

import json


def bp_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-best-practices",
            "version": "1.0.0",
            "project_path": ".",
            "docs_path": "./docs",
        },
        indent=2,
        ensure_ascii=False,
    )


def bp_documentation_guide() -> str:
    return (
        "# Guia de documentacion retroactiva\n\n"
        "## Concepto\n"
        "- Documentacion generada automaticamente\n"
        "- Refleja estado actual del proyecto\n"
        "- Actualizable en cualquier momento\n\n"
        "## Documentos generados\n"
        "- project-state.md: estado general del proyecto\n"
        "- servers-reference.md: referencia de servidores MCP\n"
        "- architecture.md: diagrama de arquitectura\n"
        "- dependencies.md: mapa de dependencias\n\n"
        "## Workflow\n"
        "1. Ejecutar bp_update_project_state\n"
        "2. Ejecutar bp_update_servers_reference\n"
        "3. Commit de cambios\n"
        "4. Repetir tras cambios significativos"
    )


def bp_naming_conventions() -> str:
    return (
        "# Convenciones de nombres\n\n"
        "## Servidores MCP\n"
        "- Prefijo: mcp-\n"
        "- Kebab case: mcp-my-server\n"
        "- Descriptivo: mcp-code-quality\n\n"
        "## Python\n"
        "- Modulos: snake_case\n"
        "- Clases: PascalCase\n"
        "- Funciones: snake_case\n"
        "- Constantes: UPPER_SNAKE\n\n"
        "## Docker\n"
        "- Imagenes: mcp-{name}:latest\n"
        "- Contenedores: mcp-{name}\n"
        "- Puertos: 80XX (XX = numero de servidor)\n\n"
        "## Variables de entorno\n"
        "- Prefijo por servidor: {PREFIX}_\n"
        "- UPPER_CASE\n"
        "- Descriptivas: ARCH_PROJECT_PATH"
    )


def bp_project_structure() -> str:
    return (
        "# Estructura de proyecto\n\n"
        "## Layout estandar\n"
        "```\n"
        "mcp-{name}/\n"
        "  src/\n"
        "    mcp_{name}/\n"
        "      __init__.py\n"
        "      server.py\n"
        "      config.py\n"
        "      resources.py\n"
        "      tools/\n"
        "        __init__.py\n"
        "        {name}_tools.py\n"
        "  tests/\n"
        "    test_{name}_tools.py\n"
        "    test_server.py\n"
        "  Dockerfile\n"
        "  pyproject.toml\n"
        "```\n\n"
        "## Reglas\n"
        "- src layout con namespace package\n"
        "- tests separados\n"
        "- Dockerfile en raiz del servidor\n"
        "- pyproject.toml con dependencias minimas"
    )


def bp_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- bp_update_project_state()\n"
        "- bp_update_servers_reference()\n"
        "- bp_generate_architecture_doc()\n"
        "- bp_generate_dependencies_doc()\n"
        "- bp_scan_code_quality()\n\n"
        "## Variables .env\n"
        "- BP_PROJECT_PATH\n"
        "- BP_DOCS_PATH"
    )


def bp_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno de BP"},
                {"code": -32001, "description": "FileNotFoundError: archivo no encontrado"},
                {"code": -32002, "description": "ParseError: error de parseo"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def bp_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## project-state.md no se genera\n"
        "- Verificar BP_PROJECT_PATH\n"
        "- Verificar permisos de escritura en BP_DOCS_PATH\n\n"
        "## servers-reference.md vacio\n"
        "- Verificar claude_desktop_config.json existe\n"
        "- Verificar JSON valido\n\n"
        "## Tokens visibles\n"
        "- Las variables con TOKEN se ocultan automaticamente\n"
        "- Verificar que el nombre contiene 'TOKEN'"
    )


def bp_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Ejemplo 1: Actualizar estado del proyecto\n"
        "bp_update_project_state()\n\n"
        "## Ejemplo 2: Actualizar referencia de servidores\n"
        "bp_update_servers_reference()\n\n"
        "## Ejemplo 3: Generar doc de arquitectura\n"
        "bp_generate_architecture_doc()\n\n"
        "## Ejemplo 4: Escanear calidad\n"
        'bp_scan_code_quality(target="src/")'
    )


def bp_code_standards() -> str:
    return (
        "# Estandares de codigo\n\n"
        "## Python\n"
        "- Type hints en todas las funciones\n"
        "- Docstrings en funciones publicas\n"
        "- from __future__ import annotations\n"
        "- Pydantic para validacion\n\n"
        "## Testing\n"
        "- pytest como framework\n"
        "- Fixtures para datos de prueba\n"
        "- Cobertura > 80%\n"
        "- Tests por cada tool\n\n"
        "## Linting\n"
        "- ruff para linting\n"
        "- ruff format para formateo\n"
        "- Line length: 120\n"
        "- Import sorting automatico"
    )


def bp_docker_standards() -> str:
    return (
        "# Estandares Docker\n\n"
        "## Dockerfile\n"
        "- Multi-stage: builder + runtime\n"
        "- Base: python:3.12-slim\n"
        "- uv para instalacion de paquetes\n"
        "- Non-root user: mcpuser (uid 1001)\n"
        "- HEALTHCHECK configurado\n"
        "- PYTHONPATH=/app/src\n\n"
        "## docker-compose\n"
        "- restart: unless-stopped\n"
        "- env_file: .env\n"
        "- Ports: 80XX\n"
        "- Networks: default\n\n"
        "## Optimizacion\n"
        "- --no-cache en pip install\n"
        "- Capas ordenadas por cambio\n"
        "- .dockerignore configurado"
    )


def bp_testing_standards() -> str:
    return (
        "# Estandares de testing\n\n"
        "## Estructura\n"
        "- tests/test_{name}_tools.py: tests unitarios\n"
        "- tests/test_server.py: tests de integracion\n"
        "- Fixtures en conftest.py si es necesario\n\n"
        "## Cobertura\n"
        "- Cada tool debe tener al menos un test\n"
        "- Tests de error handling\n"
        "- Tests de edge cases\n\n"
        "## Ejecucion\n"
        "- uv run pytest -v\n"
        "- uv run pytest --cov\n"
        "- CI: pytest en cada PR\n\n"
        "## Assertions\n"
        "- Verificar tipos de retorno\n"
        "- Verificar conteos (tools, resources)\n"
        "- Verificar nombres de servidor"
    )


def bp_git_workflow() -> str:
    return (
        "# Workflow de Git\n\n"
        "## Ramas\n"
        "- main: produccion\n"
        "- feature/*: nuevas caracteristicas\n"
        "- fix/*: correccion de bugs\n"
        "- refactor/*: mejoras de codigo\n\n"
        "## Commits\n"
        "- Conventional commits\n"
        "- feat: nueva caracteristica\n"
        "- fix: correccion\n"
        "- docs: documentacion\n"
        "- refactor: refactorizacion\n\n"
        "## PRs\n"
        "- Descripcion clara\n"
        "- Tests incluidos\n"
        "- Review obligatorio\n"
        "- CI verde antes de merge"
    )


def bp_security_practices() -> str:
    return (
        "# Practicas de seguridad\n\n"
        "## Secrets\n"
        "- Nunca hardcodear tokens\n"
        "- Usar .env (gitignored)\n"
        "- Variables con prefijo por servidor\n"
        "- Ocultar en documentacion automatica\n\n"
        "## Dependencias\n"
        "- Versiones pinneadas\n"
        "- Audit regular con pip-audit\n"
        "- Actualizar dependencias periodicamente\n\n"
        "## Docker\n"
        "- Non-root user\n"
        "- Imagenes base oficiales\n"
        "- Scan de vulnerabilidades\n"
        "- Secrets como env vars, no en imagen"
    )


def bp_performance_tips() -> str:
    return (
        "# Tips de rendimiento\n\n"
        "## Python\n"
        "- Usar generators para datos grandes\n"
        "- List comprehensions sobre loops\n"
        "- asyncio para I/O bound\n"
        "- Cache para operaciones repetidas\n\n"
        "## Docker\n"
        "- Imagenes slim\n"
        "- Layer caching ordenado\n"
        "- .dockerignore para reducir contexto\n"
        "- Multi-stage para reducir tamano\n\n"
        "## MCP\n"
        "- Tools sincronas simples\n"
        "- Resources estaticos sin I/O\n"
        "- Logging estructurado\n"
        "- Error handling robusto"
    )


def bp_deployment_guide() -> str:
    return (
        "# Guia de despliegue\n\n"
        "## Docker Compose\n"
        "- docker compose up -d --build {service}\n"
        "- docker compose down {service}\n"
        "- docker compose logs {service} --tail 10\n\n"
        "## Verificacion\n"
        "- python .verify_mcp.py (cambiar URL al puerto)\n"
        "- Verificar tools count y resources count\n"
        "- Verificar healthcheck del contenedor\n\n"
        "## Puertos asignados\n"
        "- 8001-8099: servidores MCP\n"
        "- Un puerto por servidor\n"
        "- Documentar en docker-compose.yml\n\n"
        "## Troubleshooting\n"
        "- docker logs para errores\n"
        "- docker exec -it {container} sh para debug\n"
        "- Verificar PYTHONPATH=/app/src"
    )
