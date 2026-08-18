"""Tools de node ops: list, details, cordon, uncordon, drain, taints, labels."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config

from mcp_node_ops.config import settings
from mcp_shared.errors import McpError, NotFoundError


def _load_config() -> None:
    try:
        if settings.kubeconfig_path:
            config.load_kube_config(config_file=settings.kubeconfig_path)
        else:
            config.load_incluster_config()
    except Exception as exc:
        raise McpError(f"Error cargando kubeconfig: {exc}") from exc


def _check_write() -> None:
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece NODE_OPS_ALLOW_WRITE=true.")


def list_nodes() -> list[dict[str, Any]]:
    """Lista todos los nodos con info resumida."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        result: list[dict[str, Any]] = []
        for node in nodes.items:
            conditions = {c.type: c.status for c in node.status.conditions or []}
            result.append({
                "name": node.metadata.name,
                "ready": conditions.get("Ready", "Unknown") == "True",
                "unschedulable": node.spec.unschedulable or False,
                "roles": [k.replace("node-role.kubernetes.io/", "") for k in (node.metadata.labels or {}) if k.startswith("node-role.kubernetes.io/")],
                "version": node.status.node_info.kubelet_version if node.status.node_info else "",
                "internal_ip": next((a.address for a in node.status.addresses or [] if a.type == "InternalIP"), ""),
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_node_details(node_name: str) -> dict[str, Any]:
    """Obtiene detalles completos de un nodo."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        node = v1.read_node(node_name)
        conditions = {c.type: c.status for c in node.status.conditions or []}
        return {
            "name": node.metadata.name,
            "labels": node.metadata.labels or {},
            "annotations": node.metadata.annotations or {},
            "unschedulable": node.spec.unschedulable or False,
            "taints": [
                {"key": t.key, "value": t.value, "effect": t.effect}
                for t in (node.spec.taints or [])
            ],
            "conditions": conditions,
            "addresses": {a.type: a.address for a in node.status.addresses or []},
            "capacity": dict(node.status.capacity or {}),
            "allocatable": dict(node.status.allocatable or {}),
            "node_info": {
                "kernel": node.status.node_info.kernel_version if node.status.node_info else "",
                "kubelet": node.status.node_info.kubelet_version if node.status.node_info else "",
                "os": node.status.node_info.os_image if node.status.node_info else "",
                "arch": node.status.node_info.architecture if node.status.node_info else "",
            } if node.status.node_info else {},
        }
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="node", identifier=node_name) from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def cordon_node(node_name: str) -> dict[str, Any]:
    """Marca un nodo como no programable (cordon)."""
    _check_write()
    _load_config()
    try:
        v1 = client.CoreV1Api()
        body = {"spec": {"unschedulable": True}}
        v1.patch_node(node_name, body)
        return {"node": node_name, "unschedulable": True, "status": "cordoned"}
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="node", identifier=node_name) from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def uncordon_node(node_name: str) -> dict[str, Any]:
    """Marca un nodo como programable (uncordon)."""
    _check_write()
    _load_config()
    try:
        v1 = client.CoreV1Api()
        body = {"spec": {"unschedulable": False}}
        v1.patch_node(node_name, body)
        return {"node": node_name, "unschedulable": False, "status": "uncordoned"}
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="node", identifier=node_name) from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def drain_node(node_name: str, force: bool = False, ignore_daemonsets: bool = True) -> dict[str, Any]:
    """Drena un nodo (evict pods). Requiere cordon primero."""
    _check_write()
    _load_config()
    try:
        v1 = client.CoreV1Api()
        body = {"spec": {"unschedulable": True}}
        v1.patch_node(node_name, body)
        pods = v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node_name}")
        evicted = 0
        skipped = 0
        for pod in pods.items:
            if pod.metadata.namespace == "kube-system" and not force:
                skipped += 1
                continue
            owner_refs = pod.metadata.owner_references or []
            if any(ref.kind == "DaemonSet" for ref in owner_refs) and ignore_daemonsets:
                skipped += 1
                continue
            try:
                v1.create_namespaced_pod_eviction(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    body=client.V1Eviction(
                        metadata=client.V1ObjectMeta(name=pod.metadata.name, namespace=pod.metadata.namespace),
                    ),
                )
                evicted += 1
            except client.ApiException:
                skipped += 1
        return {"node": node_name, "evicted": evicted, "skipped": skipped, "status": "drained"}
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="node", identifier=node_name) from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_node_taints(node_name: str) -> list[dict[str, Any]]:
    """Obtiene los taints de un nodo."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        node = v1.read_node(node_name)
        return [
            {"key": t.key, "value": t.value, "effect": t.effect}
            for t in (node.spec.taints or [])
        ]
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="node", identifier=node_name) from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def set_node_label(node_name: str, key: str, value: str) -> dict[str, Any]:
    """Establece un label en un nodo."""
    _check_write()
    _load_config()
    try:
        v1 = client.CoreV1Api()
        body = {"metadata": {"labels": {key: value}}}
        v1.patch_node(node_name, body)
        return {"node": node_name, "label": key, "value": value, "status": "set"}
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="node", identifier=node_name) from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc
