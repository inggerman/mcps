"""Servidor FastMCP para mcp-network-doctor."""

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

from mcp_network_doctor.config import settings
from mcp_network_doctor.tools import (
    get_ingress_status,
    get_network_policies,
    get_service_endpoints,
    list_services,
)

setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    server_name="mcp-network-doctor",
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    structlog.contextvars.bind_contextvars(server_name="mcp-network-doctor")
    logger.info("Servidor iniciando", **settings.to_log_context())
    yield
    logger.info("Servidor detenido")
    structlog.contextvars.clear_contextvars()

mcp = FastMCP(
    name="mcp-network-doctor",
    instructions=(
        "Servidor MCP para diagnósticos de red en k8s. "
        "Herramientas: list_services, get_service_endpoints, "
        "get_ingress_status, get_network_policies."
    ),
    lifespan=lifespan,
)


@mcp.tool(name="list_services", description="Lista Services en un namespace. Parámetros: namespace (str). Retorna: lista de {name, type, cluster_ip, ports, selector}.")
def tool_list_services(namespace: str) -> list[dict[str, Any]]:
    logger.info("list_services llamado", namespace=namespace)
    try:
        return list_services(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en list_services", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_service_endpoints", description="Obtiene endpoints de un Service. Parámetros: namespace (str), service_name (str). Retorna: {service, type, cluster_ip, ready_endpoints, has_endpoints}.")
def tool_get_service_endpoints(namespace: str, service_name: str) -> dict[str, Any]:
    logger.info("get_service_endpoints llamado", namespace=namespace, service=service_name)
    try:
        return get_service_endpoints(namespace=namespace, service_name=service_name)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_service_endpoints", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_ingress_status", description="Obtiene estado de Ingress. Parámetros: namespace (str opcional). Retorna: lista de {name, rules, tls_hosts, ingress_class, load_balancer}.")
def tool_get_ingress_status(namespace: str | None = None) -> list[dict[str, Any]]:
    logger.info("get_ingress_status llamado", namespace=namespace)
    try:
        return get_ingress_status(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_ingress_status", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="get_network_policies", description="Obtiene NetworkPolicies. Parámetros: namespace (str opcional). Retorna: lista de {name, pod_selector, policy_types, ingress_rules, egress_rules}.")
def tool_get_network_policies(namespace: str | None = None) -> list[dict[str, Any]]:
    logger.info("get_network_policies llamado", namespace=namespace)
    try:
        return get_network_policies(namespace=namespace)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado en get_network_policies", exc_info=exc)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
