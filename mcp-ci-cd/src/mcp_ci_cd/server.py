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
from mcp_ci_cd.tools.cicd_tools import run_pipeline

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
