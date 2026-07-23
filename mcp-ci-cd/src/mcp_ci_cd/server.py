"""
Servidor FastMCP para mcp-ci-cd.

Expone una herramienta para simular la ejecución de un pipeline.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_ci_cd import __version__
from mcp_ci_cd.config import settings
from mcp_ci_cd.tools.cicd_tools import (
    analyze_pipeline_health,
    check_dependencies,
    check_secrets,
    export_pipeline_config,
    generate_docker_compose,
    generate_makefile,
    generate_pre_commit_hook,
    generate_workflow,
    get_pipeline_status,
    list_pipeline_stages,
    run_lint,
    run_pipeline,
    run_security_scan,
    run_tests,
    validate_ci_config,
)
from mcp_ci_cd import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-ci-cd",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-ci-cd")
    logger.info(
        "mcp-ci-cd iniciando",
        version=__version__,
        project_path=str(settings.project_path),
    )
    yield
    logger.info("mcp-ci-cd detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-ci-cd",
    instructions=(
        "Servidor MCP para interactuar con procesos de Integración y Entrega Continua (CI/CD). "
        "Permite lanzar simulaciones de pipelines locales para asegurar la calidad antes de un commit real."
    ),
    lifespan=lifespan,
)


def _handle(fn: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__, error=str(exc))
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de CI/CD.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="cicd_run_pipeline",
    description="Ejecuta un pipeline local que incluye linting, testing y simulación de despliegue.",
)
def tool_run_pipeline() -> dict[str, Any]:
    logger.info("cicd_run_pipeline llamado")
    return _handle(
        run_pipeline,
        settings.project_path,
        settings.lint_cmd,
        settings.test_cmd,
        settings.deploy_cmd,
    )


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="cicd_run_lint",
    description="Ejecuta solo la fase de linting. Parametros: cmd (opcional).",
)
def tool_run_lint(cmd: str = "") -> dict[str, Any]:
    lint_cmd = cmd or settings.lint_cmd
    logger.info("cicd_run_lint llamado", cmd=lint_cmd)
    return _handle(run_lint, settings.project_path, lint_cmd)


@mcp.tool(
    name="cicd_run_tests",
    description="Ejecuta solo la fase de tests. Parametros: cmd (opcional).",
)
def tool_run_tests(cmd: str = "") -> dict[str, Any]:
    test_cmd = cmd or settings.test_cmd
    logger.info("cicd_run_tests llamado", cmd=test_cmd)
    return _handle(run_tests, settings.project_path, test_cmd)


@mcp.tool(
    name="cicd_run_security_scan",
    description="Ejecuta un scan de seguridad. Parametros: cmd (opcional).",
)
def tool_run_security_scan(cmd: str = "") -> dict[str, Any]:
    logger.info("cicd_run_security_scan llamado")
    return _handle(run_security_scan, settings.project_path, cmd)


@mcp.tool(
    name="cicd_validate_config",
    description="Valida la configuracion de CI/CD del proyecto.",
)
def tool_validate_ci_config() -> dict[str, Any]:
    logger.info("cicd_validate_config llamado")
    return _handle(validate_ci_config, settings.project_path)


@mcp.tool(
    name="cicd_generate_workflow",
    description="Genera un archivo de workflow. Parametros: platform (github/gitlab/jenkins), project_name.",
)
def tool_generate_workflow(platform: str, project_name: str = "mcp-project") -> str:
    logger.info("cicd_generate_workflow llamado", platform=platform)
    return _handle(generate_workflow, platform, project_name)


@mcp.tool(
    name="cicd_list_pipeline_stages",
    description="Lista las stages disponibles en el pipeline.",
)
def tool_list_pipeline_stages() -> list[dict[str, Any]]:
    logger.info("cicd_list_pipeline_stages llamado")
    return _handle(list_pipeline_stages)


@mcp.tool(
    name="cicd_check_dependencies",
    description="Verifica las dependencias del proyecto.",
)
def tool_check_dependencies() -> dict[str, Any]:
    logger.info("cicd_check_dependencies llamado")
    return _handle(check_dependencies, settings.project_path)


@mcp.tool(
    name="cicd_generate_docker_compose",
    description="Genera un docker-compose.yml basico para CI/CD.",
)
def tool_generate_docker_compose() -> str:
    logger.info("cicd_generate_docker_compose llamado")
    return _handle(generate_docker_compose, settings.project_path)


@mcp.tool(
    name="cicd_analyze_pipeline_health",
    description="Analiza la salud del pipeline revisando configuracion.",
)
def tool_analyze_pipeline_health() -> dict[str, Any]:
    logger.info("cicd_analyze_pipeline_health llamado")
    return _handle(analyze_pipeline_health, settings.project_path)


@mcp.tool(
    name="cicd_generate_makefile",
    description="Genera un Makefile basico para el proyecto.",
)
def tool_generate_makefile() -> str:
    logger.info("cicd_generate_makefile llamado")
    return _handle(generate_makefile, settings.project_path)


@mcp.tool(
    name="cicd_check_secrets",
    description="Escanea el proyecto en busca de posibles secrets expuestos.",
)
def tool_check_secrets() -> dict[str, Any]:
    logger.info("cicd_check_secrets llamado")
    return _handle(check_secrets, settings.project_path)


@mcp.tool(
    name="cicd_generate_pre_commit_hook",
    description="Genera una configuracion .pre-commit-config.yaml basica.",
)
def tool_generate_pre_commit_hook() -> str:
    logger.info("cicd_generate_pre_commit_hook llamado")
    return _handle(generate_pre_commit_hook)


@mcp.tool(
    name="cicd_get_pipeline_status",
    description="Retorna el estado actual del pipeline.",
)
def tool_get_pipeline_status() -> dict[str, Any]:
    logger.info("cicd_get_pipeline_status llamado")
    return _handle(get_pipeline_status, settings.project_path)


@mcp.tool(
    name="cicd_export_pipeline_config",
    description="Exporta la configuracion completa del pipeline.",
)
def tool_export_pipeline_config() -> dict[str, Any]:
    logger.info("cicd_export_pipeline_config llamado")
    return _handle(export_pipeline_config, settings.project_path)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("cicd://configuration")
def res_config() -> str:
    return res.cicd_configuration()


@mcp.resource("cicd://pipeline-guide")
def res_pipeline() -> str:
    return res.cicd_pipeline_guide()


@mcp.resource("cicd://github-actions")
def res_github() -> str:
    return res.cicd_github_actions()


@mcp.resource("cicd://gitlab-ci")
def res_gitlab() -> str:
    return res.cicd_gitlab_ci()


@mcp.resource("cicd://quick-reference")
def res_quick() -> str:
    return res.cicd_quick_reference()


@mcp.resource("cicd://error-codes")
def res_errors() -> str:
    return res.cicd_error_codes()


@mcp.resource("cicd://troubleshooting")
def res_trouble() -> str:
    return res.cicd_troubleshooting()


@mcp.resource("cicd://examples")
def res_examples() -> str:
    return res.cicd_examples()


@mcp.resource("cicd://security-scanning")
def res_security() -> str:
    return res.cicd_security_scanning()


@mcp.resource("cicd://artifacts")
def res_artifacts() -> str:
    return res.cicd_artifacts()


@mcp.resource("cicd://environments")
def res_envs() -> str:
    return res.cicd_environments()


@mcp.resource("cicd://notifications")
def res_notif() -> str:
    return res.cicd_notifications()


@mcp.resource("cicd://cache-strategy")
def res_cache() -> str:
    return res.cicd_cache_strategy()


@mcp.resource("cicd://best-practices")
def res_best() -> str:
    return res.cicd_best_practices()


@mcp.resource("cicd://deployment-strategies")
def res_deploy_strategies() -> str:
    return res.cicd_deployment_strategies()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
    else:
        mcp.run(transport="stdio")
