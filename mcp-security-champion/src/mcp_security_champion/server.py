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
    audit_project_security,
    check_https_usage,
    check_owasp_top10,
    check_password_policy,
    check_secrets,
    export_security_findings,
    generate_security_checklist,
    generate_security_policy,
    generate_security_report,
    generate_threat_model,
    get_security_metrics,
    scan_dependencies,
    sec_audit_code,
    sec_financial_compliance,
    validate_input_handling,
)
from mcp_security_champion import resources as res

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
# Tools nuevos
# ---------------------------------------------------------------------------


@mcp.tool(
    name="sec_check_secrets",
    description="Escanea un archivo en busca de secrets expuestos (API keys, tokens, private keys). Parametros: filename.",
)
def tool_check_secrets(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("sec_check_secrets llamado", file=filename)
    return _handle(check_secrets, file_path)


@mcp.tool(
    name="sec_scan_dependencies",
    description="Escanea dependencias del proyecto buscando vulnerabilidades conocidas.",
)
def tool_scan_dependencies() -> dict[str, Any]:
    logger.info("sec_scan_dependencies llamado")
    return _handle(scan_dependencies, settings.project_path)


@mcp.tool(
    name="sec_generate_security_report",
    description="Genera un reporte de seguridad completo del proyecto.",
)
def tool_generate_security_report() -> dict[str, Any]:
    logger.info("sec_generate_security_report llamado")
    return _handle(generate_security_report, settings.project_path)


@mcp.tool(
    name="sec_check_owasp_top10",
    description="Verifica codigo contra OWASP Top 10. Parametros: filename.",
)
def tool_check_owasp_top10(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("sec_check_owasp_top10 llamado", file=filename)
    return _handle(check_owasp_top10, file_path)


@mcp.tool(
    name="sec_audit_project_security",
    description="Audita la seguridad de todo el proyecto.",
)
def tool_audit_project_security() -> dict[str, Any]:
    logger.info("sec_audit_project_security llamado")
    return _handle(audit_project_security, settings.project_path)


@mcp.tool(
    name="sec_generate_security_checklist",
    description="Genera un checklist de seguridad para el proyecto.",
)
def tool_generate_security_checklist() -> list[dict[str, str]]:
    logger.info("sec_generate_security_checklist llamado")
    return _handle(generate_security_checklist)


@mcp.tool(
    name="sec_check_https_usage",
    description="Verifica que el codigo use HTTPS en lugar de HTTP. Parametros: filename.",
)
def tool_check_https_usage(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("sec_check_https_usage llamado", file=filename)
    return _handle(check_https_usage, file_path)


@mcp.tool(
    name="sec_validate_input_handling",
    description="Valida el manejo de entradas en un archivo Python. Parametros: filename.",
)
def tool_validate_input_handling(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("sec_validate_input_handling llamado", file=filename)
    return _handle(validate_input_handling, file_path)


@mcp.tool(
    name="sec_generate_threat_model",
    description="Genera un modelo de amenazas basico. Parametros: project_name.",
)
def tool_generate_threat_model(project_name: str) -> dict[str, Any]:
    logger.info("sec_generate_threat_model llamado", project=project_name)
    return _handle(generate_threat_model, project_name)


@mcp.tool(
    name="sec_check_password_policy",
    description="Verifica politicas de contrasenas en el codigo. Parametros: filename.",
)
def tool_check_password_policy(filename: str) -> dict[str, Any]:
    file_path = settings.project_path / filename
    logger.info("sec_check_password_policy llamado", file=filename)
    return _handle(check_password_policy, file_path)


@mcp.tool(
    name="sec_export_security_findings",
    description="Exporta todos los hallazgos de seguridad del proyecto.",
)
def tool_export_security_findings() -> dict[str, Any]:
    logger.info("sec_export_security_findings llamado")
    return _handle(export_security_findings, settings.project_path)


@mcp.tool(
    name="sec_get_security_metrics",
    description="Retorna metricas de seguridad del proyecto.",
)
def tool_get_security_metrics() -> dict[str, Any]:
    logger.info("sec_get_security_metrics llamado")
    return _handle(get_security_metrics, settings.project_path)


@mcp.tool(
    name="sec_generate_security_policy",
    description="Genera una plantilla de politica de seguridad. Parametros: project_name.",
)
def tool_generate_security_policy(project_name: str) -> str:
    logger.info("sec_generate_security_policy llamado", project=project_name)
    return _handle(generate_security_policy, project_name)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("sec://configuration")
def res_config() -> str:
    return res.sec_configuration()


@mcp.resource("sec://owasp-top10")
def res_owasp() -> str:
    return res.sec_owasp_top10()


@mcp.resource("sec://pci-dss")
def res_pci() -> str:
    return res.sec_pci_dss()


@mcp.resource("sec://quick-reference")
def res_quick() -> str:
    return res.sec_quick_reference()


@mcp.resource("sec://error-codes")
def res_errors() -> str:
    return res.sec_error_codes()


@mcp.resource("sec://troubleshooting")
def res_trouble() -> str:
    return res.sec_troubleshooting()


@mcp.resource("sec://examples")
def res_examples() -> str:
    return res.sec_examples()


@mcp.resource("sec://secure-coding")
def res_coding() -> str:
    return res.sec_secure_coding()


@mcp.resource("sec://threat-modeling")
def res_threat() -> str:
    return res.sec_threat_modeling()


@mcp.resource("sec://dependency-scanning")
def res_deps() -> str:
    return res.sec_dependency_scanning()


@mcp.resource("sec://secrets-management")
def res_secrets() -> str:
    return res.sec_secrets_management()


@mcp.resource("sec://api-security")
def res_api() -> str:
    return res.sec_api_security()


@mcp.resource("sec://container-security")
def res_container() -> str:
    return res.sec_container_security()


@mcp.resource("sec://incident-response")
def res_incident() -> str:
    return res.sec_incident_response()


@mcp.resource("sec://compliance-frameworks")
def res_compliance() -> str:
    return res.sec_compliance_frameworks()


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
