"""Tools de health monitoring: probes, HPA, endpoints, unhealthy pods."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config

from mcp_health_monitor.config import settings
from mcp_shared.errors import McpError, NotFoundError


def _load_config() -> None:
    try:
        if settings.kubeconfig_path:
            config.load_kube_config(config_file=settings.kubeconfig_path)
        else:
            config.load_incluster_config()
    except Exception as exc:
        raise McpError(f"Error cargando kubeconfig: {exc}") from exc


def get_probe_status(namespace: str | None = None) -> list[dict[str, Any]]:
    """Obtiene el estado de readiness/liveness probes de los pods."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        if namespace:
            pods = v1.list_namespaced_pod(namespace)
        else:
            pods = v1.list_pod_for_all_namespaces()
        result: list[dict[str, Any]] = []
        for pod in pods.items:
            for cs in pod.status.container_statuses or []:
                probes: dict[str, Any] = {}
                for container in pod.spec.containers or []:
                    if container.name == cs.name:
                        if container.readiness_probe:
                            probes["readiness"] = {
                                "type": _probe_type(container.readiness_probe),
                                "delay": container.readiness_probe.initial_delay_seconds or 0,
                                "period": container.readiness_probe.period_seconds or 0,
                                "timeout": container.readiness_probe.timeout_seconds or 0,
                            }
                        if container.liveness_probe:
                            probes["liveness"] = {
                                "type": _probe_type(container.liveness_probe),
                                "delay": container.liveness_probe.initial_delay_seconds or 0,
                                "period": container.liveness_probe.period_seconds or 0,
                                "timeout": container.liveness_probe.timeout_seconds or 0,
                            }
                        break
                result.append({
                    "pod": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "container": cs.name,
                    "ready": cs.ready,
                    "restart_count": cs.restart_count,
                    "probes": probes,
                })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_hpa_status(namespace: str | None = None) -> list[dict[str, Any]]:
    """Obtiene el estado de los HorizontalPodAutoscalers."""
    _load_config()
    try:
        autoscaling = client.AutoscalingV2Api()
        if namespace:
            hpas = autoscaling.list_namespaced_horizontal_pod_autoscaler(namespace)
        else:
            hpas = autoscaling.list_horizontal_pod_autoscaler_for_all_namespaces()
        result: list[dict[str, Any]] = []
        for hpa in hpas.items:
            metrics: list[dict[str, Any]] = []
            for m in hpa.status.current_metrics or []:
                if m.resource:
                    metrics.append({
                        "type": "Resource",
                        "name": m.resource.name,
                        "current": str(m.resource.current.average_utilization or m.resource.current.average_value or ""),
                    })
            result.append({
                "name": hpa.metadata.name,
                "namespace": hpa.metadata.namespace,
                "target": hpa.spec.scale_target_ref.name,
                "min_replicas": hpa.spec.min_replicas or 1,
                "max_replicas": hpa.spec.max_replicas,
                "current_replicas": hpa.status.current_replicas or 0,
                "desired_replicas": hpa.status.desired_replicas or 0,
                "scaling_active": hpa.status.conditions and any(c.type == "ScalingActive" and c.status == "True" for c in hpa.status.conditions),
                "metrics": metrics,
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def check_endpoint_health(namespace: str) -> list[dict[str, Any]]:
    """Verifica la salud de los Endpoints/EndpointSlices en un namespace."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        endpoints = v1.list_namespaced_endpoints(namespace)
        result: list[dict[str, Any]] = []
        for ep in endpoints.items:
            ready_addrs: list[str] = []
            not_ready_addrs: list[str] = []
            for subset in ep.subsets or []:
                for addr in subset.addresses or []:
                    ready_addrs.append(addr.ip)
                for addr in subset.not_ready_addresses or []:
                    not_ready_addrs.append(addr.ip)
            result.append({
                "name": ep.metadata.name,
                "namespace": ep.metadata.namespace,
                "ready_addresses": ready_addrs,
                "not_ready_addresses": not_ready_addrs,
                "ready_count": len(ready_addrs),
                "not_ready_count": len(not_ready_addrs),
                "healthy": len(not_ready_addrs) == 0 and len(ready_addrs) > 0,
            })
        return result
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="namespace", identifier=namespace) from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_unhealthy_pods(namespace: str | None = None) -> list[dict[str, Any]]:
    """Obtiene los pods que no están en estado Running o que tienen restarts altos."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        if namespace:
            pods = v1.list_namespaced_pod(namespace)
        else:
            pods = v1.list_pod_for_all_namespaces()
        result: list[dict[str, Any]] = []
        for pod in pods.items:
            phase = pod.status.phase or "Unknown"
            restarts = sum(cs.restart_count for cs in pod.status.container_statuses or [])
            not_ready = [cs.name for cs in pod.status.container_statuses or [] if not cs.ready]
            if phase != "Running" or restarts > 5 or not_ready:
                result.append({
                    "pod": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "phase": phase,
                    "restarts": restarts,
                    "not_ready_containers": not_ready,
                    "node": pod.spec.node_name or "",
                })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def _probe_type(probe: Any) -> str:
    if probe.http_get:
        return f"http_get:{probe.http_get.path}"
    if probe.tcp_socket:
        return f"tcp_socket:{probe.tcp_socket.port}"
    if probe.exec:
        return "exec"
    return "unknown"
