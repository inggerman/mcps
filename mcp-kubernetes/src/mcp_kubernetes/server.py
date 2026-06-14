from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from kubernetes import client, config
from mcp.shared.exceptions import McpError as SdkMcpError
from mcp.types import ErrorData
from mcp_shared.errors import McpError
from mcp_shared.logging import get_logger, setup_logging

from mcp_kubernetes.config import settings
from mcp_kubernetes.tools import (
    list_deployments,
    list_namespaces,
    list_pods,
    pod_logs,
    scale_deployment,
)

setup_logging(
    log_level=settings.log_level, log_format=settings.log_format, server_name="mcp-kubernetes"
)
logger = get_logger(__name__)
_apis: tuple[Any, Any] | None = None
mcp = FastMCP(name="mcp-kubernetes", instructions="Kubernetes en modo lectura por defecto.")


def _get_apis() -> tuple[Any, Any]:
    global _apis
    if _apis is None:
        if settings.in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config(context=settings.context)
        _apis = client.CoreV1Api(), client.AppsV1Api()
    return _apis


def _handle(fn: Any, *args: Any) -> Any:
    try:
        return fn(*args)
    except McpError as exc:
        raise SdkMcpError(ErrorData(code=-32000, message=str(exc))) from exc
    except Exception as exc:
        logger.exception("Error inesperado", tool=fn.__name__)
        raise SdkMcpError(ErrorData(code=-32603, message="Error interno del servidor.")) from exc


@mcp.tool(name="kubernetes_list_namespaces")
def tool_namespaces() -> list[dict[str, Any]]:
    core, _ = _get_apis()
    return _handle(list_namespaces, core)


@mcp.tool(name="kubernetes_list_pods")
def tool_pods(namespace: str | None = None, label_selector: str = "") -> list[dict[str, Any]]:
    core, _ = _get_apis()
    return _handle(list_pods, core, namespace or settings.namespace, label_selector)


@mcp.tool(name="kubernetes_list_deployments")
def tool_deployments(namespace: str | None = None) -> list[dict[str, Any]]:
    _, apps = _get_apis()
    return _handle(list_deployments, apps, namespace or settings.namespace)


@mcp.tool(name="kubernetes_pod_logs")
def tool_logs(pod: str, namespace: str | None = None, container: str | None = None) -> str:
    core, _ = _get_apis()
    return _handle(
        pod_logs,
        core,
        namespace or settings.namespace,
        pod,
        container,
        settings.log_tail_lines,
    )


@mcp.tool(name="kubernetes_scale_deployment")
def tool_scale(deployment: str, replicas: int, namespace: str | None = None) -> dict[str, Any]:
    _, apps = _get_apis()
    return _handle(
        scale_deployment,
        apps,
        namespace or settings.namespace,
        deployment,
        replicas,
        settings.allow_write,
    )


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
