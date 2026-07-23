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


# ---------------------------------------------------------------------------
# Tools nuevos
# ---------------------------------------------------------------------------


def list_services(core_api: Any, namespace: str) -> list[dict[str, Any]]:
    """Lista servicios en un namespace."""
    response = core_api.list_namespaced_service(namespace)
    return [
        {
            "name": item.metadata.name,
            "namespace": item.metadata.namespace,
            "type": item.spec.type,
            "cluster_ip": item.spec.cluster_ip,
            "ports": [{"port": p.port, "target_port": p.target_port, "protocol": p.protocol} for p in item.spec.ports or []],
        }
        for item in response.items
    ]


def list_configmaps(core_api: Any, namespace: str) -> list[dict[str, Any]]:
    """Lista ConfigMaps en un namespace."""
    response = core_api.list_namespaced_config_map(namespace)
    return [
        {
            "name": item.metadata.name,
            "namespace": item.metadata.namespace,
            "keys": list(item.data.keys()) if item.data else [],
        }
        for item in response.items
    ]


def list_secrets(core_api: Any, namespace: str) -> list[dict[str, Any]]:
    """Lista Secrets en un namespace (sin mostrar valores)."""
    response = core_api.list_namespaced_secret(namespace)
    return [
        {
            "name": item.metadata.name,
            "namespace": item.metadata.namespace,
            "type": item.type,
            "keys": list(item.data.keys()) if item.data else [],
        }
        for item in response.items
    ]


def get_pod_details(core_api: Any, namespace: str, pod: str) -> dict[str, Any]:
    """Obtiene detalles de un pod especifico."""
    if not pod.strip():
        raise ValidationError(field="pod", message="El pod no puede estar vacio.")
    response = core_api.read_namespaced_pod(name=pod, namespace=namespace)
    return {
        "name": response.metadata.name,
        "namespace": response.metadata.namespace,
        "phase": response.status.phase,
        "node": response.spec.node_name,
        "ip": response.status.pod_ip,
        "containers": [
            {
                "name": c.name,
                "image": c.image,
                "ready": True,
                "restarts": 0,
            }
            for c in response.spec.containers
        ],
        "labels": response.metadata.labels or {},
        "created": response.metadata.creation_timestamp,
    }


def get_deployment_status(apps_api: Any, namespace: str, deployment: str) -> dict[str, Any]:
    """Obtiene el estado de un deployment."""
    if not deployment.strip():
        raise ValidationError(field="deployment", message="El deployment no puede estar vacio.")
    response = apps_api.read_namespaced_deployment(name=deployment, namespace=namespace)
    return {
        "name": response.metadata.name,
        "namespace": response.metadata.namespace,
        "replicas": response.spec.replicas,
        "available_replicas": response.status.available_replicas or 0,
        "ready_replicas": response.status.ready_replicas or 0,
        "updated_replicas": response.status.updated_replicas or 0,
        "unavailable_replicas": response.status.unavailable_replicas or 0,
        "strategy": response.spec.strategy.type,
        "image": response.spec.template.spec.containers[0].image if response.spec.template.spec.containers else "",
    }


def list_events(core_api: Any, namespace: str) -> list[dict[str, Any]]:
    """Lista eventos en un namespace."""
    response = core_api.list_namespaced_event(namespace)
    return [
        {
            "name": item.metadata.name,
            "type": item.type,
            "reason": item.reason,
            "message": item.message,
            "involved_object": item.involved_object.name if item.involved_object else "",
            "count": item.count,
            "last_timestamp": item.last_timestamp,
        }
        for item in response.items[:100]
    ]


def list_nodes(core_api: Any) -> list[dict[str, Any]]:
    """Lista nodos del cluster."""
    response = core_api.list_node()
    return [
        {
            "name": item.metadata.name,
            "status": next((c.status for c in item.status.conditions if c.type == "Ready"), "Unknown"),
            "roles": [t.key for t in item.metadata.labels.items() if "node-role" in t.key] if item.metadata.labels else [],
            "version": item.status.node_info.kubelet_version if item.status.node_info else "",
            "addresses": {a.type: a.address for a in item.status.addresses} if item.status.addresses else {},
        }
        for item in response.items
    ]


def get_cluster_info(core_api: Any, apps_api: Any) -> dict[str, Any]:
    """Retorna informacion general del cluster."""
    nodes = list_nodes(core_api)
    namespaces = list_namespaces(core_api)

    return {
        "total_nodes": len(nodes),
        "ready_nodes": sum(1 for n in nodes if n["status"] == "True"),
        "total_namespaces": len(namespaces),
        "namespaces": [ns["name"] for ns in namespaces],
        "node_versions": list(set(n["version"] for n in nodes if n["version"])),
    }


def restart_deployment(apps_api: Any, namespace: str, deployment: str, allow_write: bool) -> dict[str, Any]:
    """Reinicia un deployment agregando un annotation de restart."""
    if not allow_write:
        raise ValidationError(field="write", message="KUBERNETES_ALLOW_WRITE esta desactivado.")
    if not deployment.strip():
        raise ValidationError(field="deployment", message="El deployment no puede estar vacio.")

    import datetime
    body = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "kubectl.kubernetes.io/restartedAt": datetime.datetime.now(datetime.timezone.utc).isoformat()
                    }
                }
            }
        }
    }
    apps_api.patch_namespaced_deployment(name=deployment, namespace=namespace, body=body)
    return {"deployment": deployment, "namespace": namespace, "status": "restarted"}


def get_resource_quotas(core_api: Any, namespace: str) -> list[dict[str, Any]]:
    """Lista ResourceQuotas en un namespace."""
    response = core_api.list_namespaced_resource_quota(namespace)
    return [
        {
            "name": item.metadata.name,
            "hard": item.status.hard if item.status.hard else {},
            "used": item.status.used if item.status.used else {},
        }
        for item in response.items
    ]
