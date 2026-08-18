"""Tools de config sync: list/get ConfigMaps & Secrets, compare, sync."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config

from mcp_config_sync.config import settings
from mcp_shared.errors import McpError, NotFoundError


def _load_config() -> None:
    try:
        if settings.kubeconfig_path:
            config.load_kube_config(config_file=settings.kubeconfig_path)
        else:
            config.load_incluster_config()
    except Exception as exc:
        raise McpError(f"Error cargando kubeconfig: {exc}") from exc


def list_configmaps(namespace: str) -> list[dict[str, Any]]:
    """Lista los ConfigMaps en un namespace."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        cms = v1.list_namespaced_config_map(namespace)
        return [
            {
                "name": cm.metadata.name,
                "namespace": cm.metadata.namespace,
                "data_keys": list((cm.data or {}).keys()),
                "key_count": len(cm.data or {}),
                "labels": cm.metadata.labels or {},
                "created": cm.metadata.creation_timestamp.isoformat() if cm.metadata.creation_timestamp else "",
            }
            for cm in cms.items
        ]
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_configmap(name: str, namespace: str) -> dict[str, Any]:
    """Obtiene el contenido de un ConfigMap."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        cm = v1.read_namespaced_config_map(name=name, namespace=namespace)
        return {
            "name": cm.metadata.name,
            "namespace": cm.metadata.namespace,
            "data": cm.data or {},
            "binary_data_keys": list((cm.binary_data or {}).keys()) if cm.binary_data else [],
            "labels": cm.metadata.labels or {},
            "annotations": cm.metadata.annotations or {},
        }
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="configmap", identifier=f"{namespace}/{name}") from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def list_secrets(namespace: str) -> list[dict[str, Any]]:
    """Lista los Secrets en un namespace (sin exponer valores)."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        secs = v1.list_namespaced_secret(namespace)
        return [
            {
                "name": s.metadata.name,
                "namespace": s.metadata.namespace,
                "type": s.type or "",
                "key_count": len(s.data or {}),
                "data_keys": list((s.data or {}).keys()),
                "labels": s.metadata.labels or {},
                "created": s.metadata.creation_timestamp.isoformat() if s.metadata.creation_timestamp else "",
            }
            for s in secs.items
        ]
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def compare_configmaps(name: str, namespace_a: str, namespace_b: str) -> dict[str, Any]:
    """Compara un ConfigMap entre dos namespaces."""
    cm_a = get_configmap(name=name, namespace=namespace_a)
    cm_b = get_configmap(name=name, namespace=namespace_b)
    keys_a = set(cm_a["data"].keys())
    keys_b = set(cm_b["data"].keys())
    only_in_a = keys_a - keys_b
    only_in_b = keys_b - keys_a
    common_keys = keys_a & keys_b
    different_values: list[str] = []
    for key in common_keys:
        if cm_a["data"][key] != cm_b["data"][key]:
            different_values.append(key)
    return {
        "configmap": name,
        "namespace_a": namespace_a,
        "namespace_b": namespace_b,
        "only_in_a": list(only_in_a),
        "only_in_b": list(only_in_b),
        "different_values": different_values,
        "identical": len(only_in_a) == 0 and len(only_in_b) == 0 and len(different_values) == 0,
    }


def sync_configmap(name: str, source_namespace: str, target_namespace: str) -> dict[str, Any]:
    """Copia un ConfigMap de un namespace a otro."""
    if not settings.allow_write:
        raise McpError("Escritura no permitida. Establece CONFIG_SYNC_ALLOW_WRITE=true.")
    _load_config()
    try:
        v1 = client.CoreV1Api()
        source_cm = v1.read_namespaced_config_map(name=name, namespace=source_namespace)
        new_cm = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=target_namespace,
                labels=source_cm.metadata.labels,
                annotations=source_cm.metadata.annotations,
            ),
            data=source_cm.data,
            binary_data=source_cm.binary_data,
        )
        try:
            v1.read_namespaced_config_map(name=name, namespace=target_namespace)
            v1.replace_namespaced_config_map(name=name, namespace=target_namespace, body=new_cm)
            action = "updated"
        except client.ApiException as exc:
            if exc.status == 404:
                v1.create_namespaced_config_map(namespace=target_namespace, body=new_cm)
                action = "created"
            else:
                raise
        return {
            "configmap": name,
            "source": source_namespace,
            "target": target_namespace,
            "action": action,
            "status": "synced",
        }
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="configmap", identifier=f"{source_namespace}/{name}") from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc
