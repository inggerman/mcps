"""Tools de storage diagnostics: PVs, PVCs, StorageClasses, volume mounts."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config

from mcp_shared.errors import McpError, NotFoundError
from mcp_storage_doctor.config import settings


def _load_config() -> None:
    try:
        if settings.kubeconfig_path:
            config.load_kube_config(config_file=settings.kubeconfig_path)
        else:
            config.load_incluster_config()
    except Exception as exc:
        raise McpError(f"Error cargando kubeconfig: {exc}") from exc


def list_persistent_volumes() -> list[dict[str, Any]]:
    """Lista todos los PersistentVolumes."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        pvs = v1.list_persistent_volume()
        result: list[dict[str, Any]] = []
        for pv in pvs.items:
            result.append({
                "name": pv.metadata.name,
                "capacity": pv.spec.capacity or {},
                "access_modes": list(pv.spec.access_modes or []),
                "phase": pv.status.phase or "Unknown",
                "storage_class": pv.spec.storage_class_name or "",
                "claim": f"{pv.spec.claim_ref.namespace}/{pv.spec.claim_ref.name}" if pv.spec.claim_ref else "",
                "reclaim_policy": pv.spec.persistent_volume_reclaim_policy or "",
                "volume_source": _pv_source(pv),
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def list_pvcs(namespace: str | None = None) -> list[dict[str, Any]]:
    """Lista los PersistentVolumeClaims."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        if namespace:
            pvcs = v1.list_namespaced_persistent_volume_claim(namespace)
        else:
            pvcs = v1.list_persistent_volume_claim_for_all_namespaces()
        result: list[dict[str, Any]] = []
        for pvc in pvcs.items:
            result.append({
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "phase": pvc.status.phase or "Unknown",
                "capacity": pvc.status.capacity or {},
                "requested": pvc.spec.resources.requests if pvc.spec.resources else {},
                "storage_class": pvc.spec.storage_class_name or "",
                "access_modes": list(pvc.spec.access_modes or []),
                "volume_name": pvc.spec.volume_name or "",
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_pvc_status(name: str, namespace: str) -> dict[str, Any]:
    """Obtiene el estado detallado de un PVC."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        pvc = v1.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)
        return {
            "name": pvc.metadata.name,
            "namespace": pvc.metadata.namespace,
            "phase": pvc.status.phase or "Unknown",
            "capacity": pvc.status.capacity or {},
            "requested": pvc.spec.resources.requests if pvc.spec.resources else {},
            "storage_class": pvc.spec.storage_class_name or "",
            "access_modes": list(pvc.spec.access_modes or []),
            "volume_name": pvc.spec.volume_name or "",
            "bound": pvc.status.phase == "Bound",
        }
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="pvc", identifier=f"{namespace}/{name}") from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def list_storage_classes() -> list[dict[str, Any]]:
    """Lista los StorageClasses disponibles."""
    _load_config()
    try:
        storage_v1 = client.StorageV1Api()
        scs = storage_v1.list_storage_class()
        result: list[dict[str, Any]] = []
        for sc in scs.items:
            result.append({
                "name": sc.metadata.name,
                "provisioner": sc.provisioner,
                "reclaim_policy": sc.reclaim_policy or "Delete",
                "volume_binding_mode": str(sc.volume_binding_mode) if sc.volume_binding_mode else "Immediate",
                "allow_volume_expansion": sc.allow_volume_expansion or False,
                "parameters": sc.parameters or {},
                "is_default": any(k == "storageclass.kubernetes.io/is-default-class" and v == "true" for k, v in (sc.metadata.annotations or {}).items()),
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_volume_mounts(namespace: str | None = None) -> list[dict[str, Any]]:
    """Obtiene los volume mounts de los pods."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        if namespace:
            pods = v1.list_namespaced_pod(namespace)
        else:
            pods = v1.list_pod_for_all_namespaces()
        result: list[dict[str, Any]] = []
        for pod in pods.items:
            mounts: list[dict[str, Any]] = []
            for container in pod.spec.containers or []:
                for vm in container.volume_mounts or []:
                    mounts.append({
                        "container": container.name,
                        "name": vm.name,
                        "mount_path": vm.mount_path,
                        "read_only": vm.read_only or False,
                    })
            if mounts:
                result.append({
                    "pod": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "mounts": mounts,
                })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def _pv_source(pv: Any) -> str:
    if pv.spec.persistent_volume_source.host_path:
        return f"hostPath:{pv.spec.persistent_volume_source.host_path.path}"
    if pv.spec.persistent_volume_source.nfs:
        return f"nfs:{pv.spec.persistent_volume_source.nfs.server}:{pv.spec.persistent_volume_source.nfs.path}"
    if pv.spec.persistent_volume_source.local:
        return f"local:{pv.spec.persistent_volume_source.local.path}"
    if pv.spec.csi:
        return f"csi:{pv.spec.csi.driver}"
    return "unknown"
