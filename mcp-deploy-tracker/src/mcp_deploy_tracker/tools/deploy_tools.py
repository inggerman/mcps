"""Tools de deploy tracking: deployments, rollout status, replica set history."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config

from mcp_deploy_tracker.config import settings
from mcp_shared.errors import McpError, NotFoundError


def _load_config() -> None:
    try:
        if settings.kubeconfig_path:
            config.load_kube_config(config_file=settings.kubeconfig_path)
        else:
            config.load_incluster_config()
    except Exception as exc:
        raise McpError(f"Error cargando kubeconfig: {exc}") from exc


def list_deployments(namespace: str | None = None) -> list[dict[str, Any]]:
    """Lista los Deployments en un namespace."""
    _load_config()
    try:
        apps_v1 = client.AppsV1Api()
        ns = namespace or settings.default_namespace
        deps = apps_v1.list_namespaced_deployment(ns)
        result: list[dict[str, Any]] = []
        for dep in deps.items:
            result.append({
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas": dep.spec.replicas or 0,
                "ready_replicas": dep.status.ready_replicas or 0,
                "available_replicas": dep.status.available_replicas or 0,
                "updated_replicas": dep.status.updated_replicas or 0,
                "image": _get_container_image(dep),
                "strategy": dep.spec.strategy.type or "RollingUpdate",
                "created": dep.metadata.creation_timestamp.isoformat() if dep.metadata.creation_timestamp else "",
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_deployment_status(name: str, namespace: str | None = None) -> dict[str, Any]:
    """Obtiene el estado detallado de un Deployment."""
    _load_config()
    try:
        apps_v1 = client.AppsV1Api()
        ns = namespace or settings.default_namespace
        dep = apps_v1.read_namespaced_deployment(name=name, namespace=ns)
        conditions: list[dict[str, Any]] = []
        for cond in dep.status.conditions or []:
            conditions.append({
                "type": cond.type,
                "status": cond.status,
                "reason": cond.reason or "",
                "message": cond.message or "",
                "last_update": cond.last_update_time.isoformat() if cond.last_update_time else "",
            })
        return {
            "name": dep.metadata.name,
            "namespace": dep.metadata.namespace,
            "replicas": dep.spec.replicas or 0,
            "ready_replicas": dep.status.ready_replicas or 0,
            "available_replicas": dep.status.available_replicas or 0,
            "updated_replicas": dep.status.updated_replicas or 0,
            "unavailable_replicas": dep.status.unavailable_replicas or 0,
            "image": _get_container_image(dep),
            "strategy": dep.spec.strategy.type or "RollingUpdate",
            "conditions": conditions,
            "all_ready": (dep.status.ready_replicas or 0) == (dep.spec.replicas or 0),
        }
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="deployment", identifier=f"{ns}/{name}") from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_rollout_status(name: str, namespace: str | None = None) -> dict[str, Any]:
    """Obtiene el estado del rollout de un Deployment."""
    _load_config()
    try:
        apps_v1 = client.AppsV1Api()
        ns = namespace or settings.default_namespace
        dep = apps_v1.read_namespaced_deployment(name=name, namespace=ns)
        desired = dep.spec.replicas or 0
        updated = dep.status.updated_replicas or 0
        available = dep.status.available_replicas or 0
        if updated < desired:
            rollout_status = "Progressing"
            message = f"{updated}/{desired} replicas updated"
        elif available < desired:
            rollout_status = "Progressing"
            message = f"{available}/{desired} replicas available"
        else:
            rollout_status = "Complete"
            message = f"{desired}/{desired} replicas available"
        return {
            "name": dep.metadata.name,
            "namespace": dep.metadata.namespace,
            "rollout_status": rollout_status,
            "message": message,
            "desired": desired,
            "updated": updated,
            "available": available,
            "complete": rollout_status == "Complete",
        }
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="deployment", identifier=f"{ns}/{name}") from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_replica_set_history(name: str, namespace: str | None = None) -> list[dict[str, Any]]:
    """Obtiene el historial de ReplicaSets de un Deployment."""
    _load_config()
    try:
        apps_v1 = client.AppsV1Api()
        ns = namespace or settings.default_namespace
        dep = apps_v1.read_namespaced_deployment(name=name, namespace=ns)
        selector = dep.spec.selector.match_labels or {}
        label_selector = ",".join(f"{k}={v}" for k, v in selector.items())
        rsets = apps_v1.list_namespaced_replica_set(ns, label_selector=label_selector)
        result: list[dict[str, Any]] = []
        for rs in rsets.items:
            annotations = rs.metadata.annotations or {}
            revision = annotations.get("deployment.kubernetes.io/revision", "unknown")
            change_cause = annotations.get("deployment.kubernetes.io/change-cause", "")
            result.append({
                "name": rs.metadata.name,
                "namespace": rs.metadata.namespace,
                "revision": revision,
                "change_cause": change_cause,
                "replicas": rs.spec.replicas or 0,
                "available": rs.status.available_replicas or 0,
                "image": _get_rs_image(rs),
                "created": rs.metadata.creation_timestamp.isoformat() if rs.metadata.creation_timestamp else "",
            })
        result.sort(key=lambda x: x["revision"], reverse=True)
        return result
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="deployment", identifier=f"{ns}/{name}") from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def _get_container_image(dep: Any) -> str:
    if dep.spec.template.spec.containers:
        return dep.spec.template.spec.containers[0].image
    return ""


def _get_rs_image(rs: Any) -> str:
    if rs.spec.template.spec.containers:
        return rs.spec.template.spec.containers[0].image
    return ""
