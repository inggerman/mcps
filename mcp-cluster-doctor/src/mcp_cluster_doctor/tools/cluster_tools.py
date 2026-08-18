"""Tools de cluster diagnostics: node health, pod status, events, resource usage."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config

from mcp_cluster_doctor.config import settings
from mcp_shared.errors import McpError, NotFoundError


def _load_config() -> None:
    try:
        if settings.kubeconfig_path:
            config.load_kube_config(config_file=settings.kubeconfig_path)
        else:
            config.load_incluster_config()
    except Exception as exc:
        raise McpError(f"Error cargando kubeconfig: {exc}") from exc


def get_node_health() -> list[dict[str, Any]]:
    """Obtiene el estado de salud de todos los nodos del cluster."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        result: list[dict[str, Any]] = []
        for node in nodes.items:
            conditions = {c.type: c.status for c in node.status.conditions or []}
            result.append({
                "name": node.metadata.name,
                "ready": conditions.get("Ready", "Unknown"),
                "memory_pressure": conditions.get("MemoryPressure", "Unknown"),
                "disk_pressure": conditions.get("DiskPressure", "Unknown"),
                "pid_pressure": conditions.get("PIDPressure", "Unknown"),
                "network_unavailable": conditions.get("NetworkUnavailable", "Unknown"),
                "kernel_version": node.status.node_info.kernel_version if node.status.node_info else "",
                "kubelet_version": node.status.node_info.kubelet_version if node.status.node_info else "",
                "os": node.status.node_info.os_image if node.status.node_info else "",
                "arch": node.status.node_info.architecture if node.status.node_info else "",
                "addresses": {a.type: a.address for a in node.status.addresses or []},
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_pod_status(namespace: str | None = None) -> list[dict[str, Any]]:
    """Obtiene el estado de los pods en un namespace (o todos)."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        ns = namespace or settings.default_namespace
        if ns == "all":
            pods = v1.list_pod_for_all_namespaces()
        else:
            pods = v1.list_namespaced_pod(ns)
        result: list[dict[str, Any]] = []
        for pod in pods.items:
            result.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "pod_ip": pod.status.pod_ip,
                "node_name": pod.spec.node_name,
                "restart_count": sum(cs.restart_count for cs in pod.status.container_statuses or []),
                "ready": all(cs.ready for cs in pod.status.container_statuses or []),
                "containers": [
                    {
                        "name": cs.name,
                        "ready": cs.ready,
                        "restart_count": cs.restart_count,
                        "state": list(cs.state.keys())[0] if cs.state else "unknown",
                        "image": cs.image,
                    }
                    for cs in pod.status.container_statuses or []
                ],
                "start_time": pod.status.start_time.isoformat() if pod.status.start_time else "",
            })
        return result
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="namespace", identifier=namespace or "") from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_cluster_events(namespace: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Obtiene los eventos recientes del cluster."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        ns = namespace or settings.default_namespace
        if ns == "all":
            events = v1.list_event_for_all_namespaces(limit=limit)
        else:
            events = v1.list_namespaced_event(ns, limit=limit)
        result: list[dict[str, Any]] = []
        for event in events.items:
            result.append({
                "name": event.metadata.name,
                "namespace": event.metadata.namespace,
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "involved_object": f"{event.involved_object.kind}/{event.involved_object.name}",
                "count": event.count,
                "last_timestamp": event.last_timestamp.isoformat() if event.last_timestamp else "",
                "first_timestamp": event.first_timestamp.isoformat() if event.first_timestamp else "",
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_resource_usage(namespace: str | None = None) -> dict[str, Any]:
    """Obtiene el uso de recursos (requests/limits) por namespace."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        ns = namespace or settings.default_namespace
        if ns == "all":
            pods = v1.list_pod_for_all_namespaces()
        else:
            pods = v1.list_namespaced_pod(ns)
        total_requests = {"cpu": 0, "memory": 0}
        total_limits = {"cpu": 0, "memory": 0}
        pod_count = 0
        for pod in pods.items:
            for container in pod.spec.containers or []:
                pod_count += 1
                if container.resources:
                    if container.resources.requests:
                        total_requests["cpu"] += _parse_cpu(container.resources.requests.get("cpu", "0"))
                        total_requests["memory"] += _parse_memory(container.resources.requests.get("memory", "0"))
                    if container.resources.limits:
                        total_limits["cpu"] += _parse_cpu(container.resources.limits.get("cpu", "0"))
                        total_limits["memory"] += _parse_memory(container.resources.limits.get("memory", "0"))
        return {
            "namespace": ns,
            "pod_count": len(pods.items),
            "container_count": pod_count,
            "total_requests": {
                "cpu_millicores": int(total_requests["cpu"]),
                "memory_mi": int(total_requests["memory"]),
            },
            "total_limits": {
                "cpu_millicores": int(total_limits["cpu"]),
                "memory_mi": int(total_limits["memory"]),
            },
        }
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def _parse_cpu(value: str) -> float:
    if value.endswith("m"):
        return float(value[:-1])
    return float(value) * 1000


def _parse_memory(value: str) -> float:
    if value.endswith("Ki"):
        return float(value[:-2]) / 1024
    if value.endswith("Mi"):
        return float(value[:-2])
    if value.endswith("Gi"):
        return float(value[:-2]) * 1024
    return float(value) / (1024 * 1024)
