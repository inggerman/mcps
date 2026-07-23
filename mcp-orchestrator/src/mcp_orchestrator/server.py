"""
Servidor FastMCP para mcp-orchestrator.

Expone herramientas para analizar y generar DAGs de orquestación.
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

from mcp_orchestrator import __version__
from mcp_orchestrator.config import settings
from mcp_orchestrator.tools.orchestrator_tools import (
    analyze_dag_complexity,
    analyze_dag_dependencies,
    calculate_dag_critical_path,
    compare_dags,
    export_dag_catalog,
    find_dag_cycles,
    generate_boilerplate_dag,
    generate_dag_documentation,
    generate_dag_test,
    generate_task_group,
    get_dag_stats,
    list_dags,
    parse_airflow_dag,
    validate_dag_acyclicity,
    validate_dag_structure,
)
from mcp_orchestrator import resources as res

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-orchestrator",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-orchestrator")
    logger.info(
        "mcp-orchestrator iniciando",
        version=__version__,
        dags_path=str(settings.dags_path),
    )
    yield
    logger.info("mcp-orchestrator detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-orchestrator",
    instructions=(
        "Servidor MCP para trabajar con orquestadores de flujos de trabajo (Data Engineering). "
        "Permite parsear DAGs de Airflow, validar que no haya ciclos infinitos, y generar código boilerplate."
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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del orquestador.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="orch_parse_airflow_dag",
    description="Parsea un archivo de Python que contiene un DAG de Airflow y extrae tareas y sus dependencias (AST).",
)
def tool_parse_airflow_dag(filename: str) -> dict[str, Any]:
    file_path = settings.dags_path / filename
    logger.info("orch_parse_airflow_dag llamado", file=filename)
    return _handle(parse_airflow_dag, file_path)


@mcp.tool(
    name="orch_validate_dag",
    description="Valida que un conjunto de aristas (dependencias) formen un grafo acíclico dirigido (DAG) válido.",
)
def tool_validate_dag(edges: list[tuple[str, str]]) -> dict[str, Any]:
    """edges debe ser una lista de tuplas [('task_A', 'task_B'), ...]"""
    logger.info("orch_validate_dag llamado", edge_count=len(edges))
    return _handle(validate_dag_acyclicity, edges)


@mcp.tool(
    name="orch_generate_boilerplate",
    description="Genera código Python (Airflow DAG) a partir de un dag_id y una lista de nombres de tareas.",
)
def tool_generate_boilerplate(dag_id: str, tasks: list[str]) -> str:
    logger.info("orch_generate_boilerplate llamado", dag_id=dag_id)
    return _handle(generate_boilerplate_dag, dag_id, tasks)


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="orch_list_dags",
    description="Lista todos los DAGs disponibles en el directorio configurado.",
)
def tool_list_dags() -> list[dict[str, Any]]:
    logger.info("orch_list_dags llamado")
    return _handle(list_dags, settings.dags_path)


@mcp.tool(
    name="orch_analyze_dag_dependencies",
    description="Analiza dependencias detalladas de un DAG. Parametros: filename.",
)
def tool_analyze_dag_dependencies(filename: str) -> dict[str, Any]:
    logger.info("orch_analyze_dag_dependencies llamado", file=filename)
    return _handle(analyze_dag_dependencies, settings.dags_path, filename)


@mcp.tool(
    name="orch_generate_task_group",
    description="Genera codigo boilerplate para un TaskGroup. Parametros: name, tasks (list), dependencies (list de tuplas, opcional).",
)
def tool_generate_task_group(name: str, tasks: list[str], dependencies: list[tuple[str, str]] | None = None) -> str:
    logger.info("orch_generate_task_group llamado", name=name)
    return _handle(generate_task_group, name, tasks, dependencies)


@mcp.tool(
    name="orch_find_dag_cycles",
    description="Encuentra ciclos especificos en un grafo. Parametros: edges (list de tuplas).",
)
def tool_find_dag_cycles(edges: list[tuple[str, str]]) -> dict[str, Any]:
    logger.info("orch_find_dag_cycles llamado", edge_count=len(edges))
    return _handle(find_dag_cycles, edges)


@mcp.tool(
    name="orch_calculate_critical_path",
    description="Calcula el camino critico de un DAG. Parametros: edges (list de tuplas), task_durations (dict).",
)
def tool_calculate_critical_path(edges: list[tuple[str, str]], task_durations: dict[str, float]) -> dict[str, Any]:
    logger.info("orch_calculate_critical_path llamado", edge_count=len(edges))
    return _handle(calculate_dag_critical_path, edges, task_durations)


@mcp.tool(
    name="orch_generate_dag_documentation",
    description="Genera documentacion markdown para un DAG. Parametros: filename.",
)
def tool_generate_dag_documentation(filename: str) -> str:
    logger.info("orch_generate_dag_documentation llamado", file=filename)
    return _handle(generate_dag_documentation, settings.dags_path, filename)


@mcp.tool(
    name="orch_validate_dag_structure",
    description="Valida estructura de un DAG verificando best practices. Parametros: filename.",
)
def tool_validate_dag_structure(filename: str) -> dict[str, Any]:
    logger.info("orch_validate_dag_structure llamado", file=filename)
    return _handle(validate_dag_structure, settings.dags_path, filename)


@mcp.tool(
    name="orch_export_dag_catalog",
    description="Exporta un catalogo completo de todos los DAGs.",
)
def tool_export_dag_catalog() -> dict[str, Any]:
    logger.info("orch_export_dag_catalog llamado")
    return _handle(export_dag_catalog, settings.dags_path)


@mcp.tool(
    name="orch_generate_dag_test",
    description="Genera un test boilerplate para un DAG. Parametros: filename.",
)
def tool_generate_dag_test(filename: str) -> str:
    logger.info("orch_generate_dag_test llamado", file=filename)
    return _handle(generate_dag_test, filename, settings.dags_path)


@mcp.tool(
    name="orch_analyze_dag_complexity",
    description="Analiza la complejidad de un DAG. Parametros: filename.",
)
def tool_analyze_dag_complexity(filename: str) -> dict[str, Any]:
    logger.info("orch_analyze_dag_complexity llamado", file=filename)
    return _handle(analyze_dag_complexity, settings.dags_path, filename)


@mcp.tool(
    name="orch_get_dag_stats",
    description="Genera estadisticas rapidas del catalogo de DAGs.",
)
def tool_get_dag_stats() -> dict[str, Any]:
    logger.info("orch_get_dag_stats llamado")
    return _handle(get_dag_stats, settings.dags_path)


@mcp.tool(
    name="orch_compare_dags",
    description="Compara dos DAGs en terminos de tasks y dependencias. Parametros: file_a, file_b.",
)
def tool_compare_dags(file_a: str, file_b: str) -> dict[str, Any]:
    logger.info("orch_compare_dags llamado", file_a=file_a, file_b=file_b)
    return _handle(compare_dags, settings.dags_path, file_a, file_b)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("orch://configuration")
def res_config() -> str:
    return res.orchestrator_configuration()


@mcp.resource("orch://airflow-guide")
def res_airflow() -> str:
    return res.orchestrator_airflow_guide()


@mcp.resource("orch://dag-patterns")
def res_patterns() -> str:
    return res.orchestrator_dag_patterns()


@mcp.resource("orch://best-practices")
def res_best() -> str:
    return res.orchestrator_best_practices()


@mcp.resource("orch://quick-reference")
def res_quick() -> str:
    return res.orchestrator_quick_reference()


@mcp.resource("orch://error-codes")
def res_errors() -> str:
    return res.orchestrator_error_codes()


@mcp.resource("orch://troubleshooting")
def res_trouble() -> str:
    return res.orchestrator_troubleshooting()


@mcp.resource("orch://examples")
def res_examples() -> str:
    return res.orchestrator_examples()


@mcp.resource("orch://scheduling")
def res_sched() -> str:
    return res.orchestrator_scheduling()


@mcp.resource("orch://xcom-guide")
def res_xcom() -> str:
    return res.orchestrator_xcom()


@mcp.resource("orch://operators")
def res_ops() -> str:
    return res.orchestrator_operators()


@mcp.resource("orch://testing")
def res_test() -> str:
    return res.orchestrator_testing()


@mcp.resource("orch://monitoring")
def res_mon() -> str:
    return res.orchestrator_monitoring()


@mcp.resource("orch://ci-cd")
def res_cicd() -> str:
    return res.orchestrator_ci_cd()


@mcp.resource("orch://security")
def res_sec() -> str:
    return res.orchestrator_security()


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
