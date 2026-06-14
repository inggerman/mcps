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
    generate_boilerplate_dag,
    parse_airflow_dag,
    validate_dag_acyclicity,
)

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
