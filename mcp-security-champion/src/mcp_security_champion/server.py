"""
Servidor FastMCP para mcp-security-champion.

Expone herramientas de validación de seguridad y compliance financiero.
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

from mcp_security_champion import __version__
from mcp_security_champion.config import settings
from mcp_security_champion.tools.sec_tools import (
    sec_audit_code,
    sec_financial_compliance,
)

# ---------------------------------------------------------------------------
# Configuración de logging
# ---------------------------------------------------------------------------

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-security-champion",
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-security-champion")
    logger.info(
        "mcp-security-champion iniciando",
        version=__version__,
        project_path=str(settings.project_path),
    )
    yield
    logger.info("mcp-security-champion detenido")


# ---------------------------------------------------------------------------
# Instancia FastMCP
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="mcp-security-champion",
    instructions=(
        "Servidor MCP para auditar la seguridad del software (SAST ligero) y verificar normativas financieras. "
        "Úsalo para detectar hardcoded secrets, funciones inseguras (eval/exec) y violaciones PCI-DSS básicas."
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
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno de Security.")) from exc


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="sec_audit_code",
    description="Audita código fuente buscando hardcoded secrets o funciones inseguras (OWASP Top 10).",
)
def tool_sec_audit_code(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("sec_audit_code llamado", file=filename)
    return _handle(sec_audit_code, file_path)


@mcp.tool(
    name="sec_financial_compliance",
    description="Revisa el cumplimiento de normativas financieras como PCI-DSS (enmascaramiento de datos, uso de HTTPS).",
)
def tool_sec_financial_compliance(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("sec_financial_compliance llamado", file=filename)
    return _handle(sec_financial_compliance, file_path)


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
