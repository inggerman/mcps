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
    get_cluster_info,
    get_deployment_status,
    get_pod_details,
    get_resource_quotas,
    list_configmaps,
    list_deployments,
    list_events,
    list_namespaces,
    list_nodes,
    list_pods,
    list_secrets,
    list_services,
    pod_logs,
    restart_deployment,
    scale_deployment,
)
from mcp_kubernetes import resources as res

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


@mcp.tool(name="kubernetes_list_services")
def tool_services(namespace: str | None = None) -> list[dict[str, Any]]:
    core, _ = _get_apis()
    return _handle(list_services, core, namespace or settings.namespace)


@mcp.tool(name="kubernetes_list_configmaps")
def tool_configmaps(namespace: str | None = None) -> list[dict[str, Any]]:
    core, _ = _get_apis()
    return _handle(list_configmaps, core, namespace or settings.namespace)


@mcp.tool(name="kubernetes_list_secrets")
def tool_secrets(namespace: str | None = None) -> list[dict[str, Any]]:
    core, _ = _get_apis()
    return _handle(list_secrets, core, namespace or settings.namespace)


@mcp.tool(name="kubernetes_get_pod")
def tool_get_pod(pod: str, namespace: str | None = None) -> dict[str, Any]:
    core, _ = _get_apis()
    return _handle(get_pod_details, core, namespace or settings.namespace, pod)


@mcp.tool(name="kubernetes_deployment_status")
def tool_deployment_status(deployment: str, namespace: str | None = None) -> dict[str, Any]:
    _, apps = _get_apis()
    return _handle(get_deployment_status, apps, namespace or settings.namespace, deployment)


@mcp.tool(name="kubernetes_list_events")
def tool_events(namespace: str | None = None) -> list[dict[str, Any]]:
    core, _ = _get_apis()
    return _handle(list_events, core, namespace or settings.namespace)


@mcp.tool(name="kubernetes_list_nodes")
def tool_nodes() -> list[dict[str, Any]]:
    core, _ = _get_apis()
    return _handle(list_nodes, core)


@mcp.tool(name="kubernetes_cluster_info")
def tool_cluster_info() -> dict[str, Any]:
    core, apps = _get_apis()
    return _handle(get_cluster_info, core, apps)


@mcp.tool(name="kubernetes_restart_deployment")
def tool_restart(deployment: str, namespace: str | None = None) -> dict[str, Any]:
    _, apps = _get_apis()
    return _handle(restart_deployment, apps, namespace or settings.namespace, deployment, settings.allow_write)


@mcp.tool(name="kubernetes_resource_quotas")
def tool_quotas(namespace: str | None = None) -> list[dict[str, Any]]:
    core, _ = _get_apis()
    return _handle(get_resource_quotas, core, namespace or settings.namespace)


# ---------------------------------------------------------------------------
# Resources estaticos
# ---------------------------------------------------------------------------


@mcp.resource("kubernetes://configuration")
def res_config() -> str:
    return res.kubernetes_configuration()


@mcp.resource("kubernetes://basics")
def res_basics() -> str:
    return res.kubernetes_basics()


@mcp.resource("kubernetes://best-practices")
def res_best() -> str:
    return res.kubernetes_best_practices()


@mcp.resource("kubernetes://quick-reference")
def res_quick() -> str:
    return res.kubernetes_quick_reference()


@mcp.resource("kubernetes://error-codes")
def res_errors() -> str:
    return res.kubernetes_error_codes()


@mcp.resource("kubernetes://troubleshooting")
def res_trouble() -> str:
    return res.kubernetes_troubleshooting()


@mcp.resource("kubernetes://examples")
def res_examples() -> str:
    return res.kubernetes_examples()


@mcp.resource("kubernetes://rbac")
def res_rbac() -> str:
    return res.kubernetes_rbac()


@mcp.resource("kubernetes://networking")
def res_networking() -> str:
    return res.kubernetes_networking()


@mcp.resource("kubernetes://storage")
def res_storage() -> str:
    return res.kubernetes_storage()


@mcp.resource("kubernetes://security")
def res_security() -> str:
    return res.kubernetes_security()


@mcp.resource("kubernetes://helm")
def res_helm() -> str:
    return res.kubernetes_helm()


@mcp.resource("kubernetes://health-checks")
def res_health() -> str:
    return res.kubernetes_health_checks()


@mcp.resource("kubernetes://autoscaling")
def res_autoscaling() -> str:
    return res.kubernetes_autoscaling()


@mcp.resource("kubernetes://gitops")
def res_gitops() -> str:
    return res.kubernetes_gitops()


if __name__ == "__main__":
    if settings.mcp_transport == "streamable-http":
        mcp.run(transport="streamable-http", host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="stdio")
