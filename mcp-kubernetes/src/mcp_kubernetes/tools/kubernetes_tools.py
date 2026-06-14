from __future__ import annotations

from typing import Any

from mcp_shared.errors import ValidationError


def list_namespaces(core_api: Any) -> list[dict[str, Any]]:
    response = core_api.list_namespace()
    return [{"name": item.metadata.name, "status": item.status.phase} for item in response.items]


def list_pods(core_api: Any, namespace: str, label_selector: str = "") -> list[dict[str, Any]]:
    response = core_api.list_namespaced_pod(namespace, label_selector=label_selector)
    return [
        {
            "name": item.metadata.name,
            "namespace": item.metadata.namespace,
            "phase": item.status.phase,
            "node": item.spec.node_name,
            "containers": [container.name for container in item.spec.containers],
        }
        for item in response.items
    ]


def list_deployments(apps_api: Any, namespace: str) -> list[dict[str, Any]]:
    response = apps_api.list_namespaced_deployment(namespace)
    return [
        {
            "name": item.metadata.name,
            "replicas": item.spec.replicas,
            "available_replicas": item.status.available_replicas or 0,
            "ready_replicas": item.status.ready_replicas or 0,
        }
        for item in response.items
    ]


def pod_logs(
    core_api: Any,
    namespace: str,
    pod: str,
    container: str | None,
    tail_lines: int,
) -> str:
    if not pod.strip():
        raise ValidationError(field="pod", message="El pod no puede estar vacío.")
    return core_api.read_namespaced_pod_log(
        name=pod,
        namespace=namespace,
        container=container,
        tail_lines=tail_lines,
        timestamps=True,
    )


def scale_deployment(
    apps_api: Any,
    namespace: str,
    deployment: str,
    replicas: int,
    allow_write: bool,
) -> dict[str, Any]:
    if not allow_write:
        raise ValidationError(field="write", message="KUBERNETES_ALLOW_WRITE está desactivado.")
    if replicas < 0 or replicas > 1000:
        raise ValidationError(field="replicas", message="Replicas debe estar entre 0 y 1000.")
    response = apps_api.patch_namespaced_deployment_scale(
        name=deployment,
        namespace=namespace,
        body={"spec": {"replicas": replicas}},
    )
    return {"deployment": deployment, "namespace": namespace, "replicas": response.spec.replicas}
