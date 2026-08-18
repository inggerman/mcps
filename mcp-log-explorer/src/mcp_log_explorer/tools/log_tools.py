"""Tools de log exploration: pod logs, tail, multi-pod search."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config

from mcp_log_explorer.config import settings
from mcp_shared.errors import McpError, NotFoundError


def _load_config() -> None:
    try:
        if settings.kubeconfig_path:
            config.load_kube_config(config_file=settings.kubeconfig_path)
        else:
            config.load_incluster_config()
    except Exception as exc:
        raise McpError(f"Error cargando kubeconfig: {exc}") from exc


def get_pod_logs(
    pod_name: str,
    namespace: str | None = None,
    container: str | None = None,
    tail_lines: int = 100,
    previous: bool = False,
) -> dict[str, Any]:
    """Obtiene los logs de un pod específico."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        ns = namespace or settings.default_namespace
        kwargs: dict[str, Any] = {"tail_lines": min(tail_lines, settings.max_lines)}
        if container:
            kwargs["container"] = container
        if previous:
            kwargs["previous"] = True
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=ns, **kwargs)
        lines = logs.split("\n") if logs else []
        return {
            "pod": pod_name,
            "namespace": ns,
            "container": container or "default",
            "line_count": len(lines),
            "logs": lines,
        }
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="pod", identifier=f"{ns}/{pod_name}") from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def tail_pod_logs(
    pod_name: str,
    namespace: str | None = None,
    container: str | None = None,
    lines: int = 50,
) -> dict[str, Any]:
    """Obtiene las últimas N líneas de logs de un pod."""
    return get_pod_logs(
        pod_name=pod_name,
        namespace=namespace,
        container=container,
        tail_lines=lines,
        previous=False,
    )


def search_logs_across_pods(
    namespace: str | None = None,
    pattern: str = "",
    label_selector: str = "",
    tail_lines: int = 50,
) -> list[dict[str, Any]]:
    """Busca un patrón en los logs de todos los pods que coinciden."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        ns = namespace or settings.default_namespace
        if label_selector:
            pods = v1.list_namespaced_pod(ns, label_selector=label_selector)
        else:
            pods = v1.list_namespaced_pod(ns)
        results: list[dict[str, Any]] = []
        for pod in pods.items:
            pod_name = pod.metadata.name
            containers = [c.name for c in pod.spec.containers]
            for c_name in containers:
                try:
                    logs = v1.read_namespaced_pod_log(
                        name=pod_name,
                        namespace=ns,
                        container=c_name,
                        tail_lines=min(tail_lines, settings.max_lines),
                    )
                    if not logs:
                        continue
                    matching_lines = [
                        line for line in logs.split("\n")
                        if pattern.lower() in line.lower()
                    ] if pattern else logs.split("\n")
                    if matching_lines:
                        results.append({
                            "pod": pod_name,
                            "namespace": ns,
                            "container": c_name,
                            "matches": len(matching_lines),
                            "lines": matching_lines[:50],
                        })
                except client.ApiException:
                    continue
        return results
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc
