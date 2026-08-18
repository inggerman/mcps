"""Tools de network diagnostics: services, endpoints, ingress, network policies."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config

from mcp_network_doctor.config import settings
from mcp_shared.errors import McpError, NotFoundError


def _load_config() -> None:
    try:
        if settings.kubeconfig_path:
            config.load_kube_config(config_file=settings.kubeconfig_path)
        else:
            config.load_incluster_config()
    except Exception as exc:
        raise McpError(f"Error cargando kubeconfig: {exc}") from exc


def list_services(namespace: str) -> list[dict[str, Any]]:
    """Lista los Services en un namespace."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        svcs = v1.list_namespaced_service(namespace)
        result: list[dict[str, Any]] = []
        for svc in svcs.items:
            ports = [
                {
                    "name": p.name or "",
                    "port": p.port,
                    "target_port": str(p.target_port) if p.target_port else "",
                    "protocol": p.protocol or "TCP",
                }
                for p in svc.spec.ports or []
            ]
            result.append({
                "name": svc.metadata.name,
                "namespace": svc.metadata.namespace,
                "type": svc.spec.type or "ClusterIP",
                "cluster_ip": svc.spec.cluster_ip or "",
                "external_ips": svc.spec.external_ips or [],
                "ports": ports,
                "selector": svc.spec.selector or {},
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_service_endpoints(namespace: str, service_name: str) -> dict[str, Any]:
    """Obtiene los endpoints de un Service específico."""
    _load_config()
    try:
        v1 = client.CoreV1Api()
        svc = v1.read_namespaced_service(name=service_name, namespace=namespace)
        try:
            ep = v1.read_namespaced_endpoints(name=service_name, namespace=namespace)
            ready: list[str] = []
            not_ready: list[str] = []
            for subset in ep.subsets or []:
                for addr in subset.addresses or []:
                    ready.append(addr.ip)
                for addr in subset.not_ready_addresses or []:
                    not_ready.append(addr.ip)
        except client.ApiException:
            ready, not_ready = [], []
        return {
            "service": service_name,
            "namespace": namespace,
            "type": svc.spec.type or "ClusterIP",
            "cluster_ip": svc.spec.cluster_ip or "",
            "ready_endpoints": ready,
            "not_ready_endpoints": not_ready,
            "ready_count": len(ready),
            "has_endpoints": len(ready) > 0,
        }
    except client.ApiException as exc:
        if exc.status == 404:
            raise NotFoundError(resource="service", identifier=f"{namespace}/{service_name}") from exc
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_ingress_status(namespace: str | None = None) -> list[dict[str, Any]]:
    """Obtiene el estado de los Ingress en un namespace."""
    _load_config()
    try:
        net_v1 = client.NetworkingV1Api()
        if namespace:
            ingresses = net_v1.list_namespaced_ingress(namespace)
        else:
            ingresses = net_v1.list_ingress_for_all_namespaces()
        result: list[dict[str, Any]] = []
        for ing in ingresses.items:
            rules: list[dict[str, Any]] = []
            for rule in ing.spec.rules or []:
                paths = [
                    {"path": p.path, "service": p.backend.service.name if p.backend.service else "", "port": p.backend.service.port.number if p.backend.service and p.backend.service.port else 0}
                    for p in rule.http.paths if rule.http
                ] if rule.http else []
                rules.append({"host": rule.host or "", "paths": paths})
            tls_hosts = []
            for tls in ing.spec.tls or []:
                tls_hosts.extend(tls.hosts or [])
            result.append({
                "name": ing.metadata.name,
                "namespace": ing.metadata.namespace,
                "rules": rules,
                "tls_hosts": tls_hosts,
                "ingress_class": ing.spec.ingress_class_name or "",
                "load_balancer": ing.status.load_balancer.ingress[0].ip if ing.status.load_balancer and ing.status.load_balancer.ingress else "",
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc


def get_network_policies(namespace: str | None = None) -> list[dict[str, Any]]:
    """Obtiene las NetworkPolicies en un namespace."""
    _load_config()
    try:
        net_v1 = client.NetworkingV1Api()
        if namespace:
            nps = net_v1.list_namespaced_network_policy(namespace)
        else:
            nps = net_v1.list_network_policy_for_all_namespaces()
        result: list[dict[str, Any]] = []
        for np in nps.items:
            result.append({
                "name": np.metadata.name,
                "namespace": np.metadata.namespace,
                "pod_selector": dict(np.spec.pod_selector.match_labels or {}) if np.spec.pod_selector else {},
                "policy_types": list(np.spec.policy_types or []),
                "ingress_rules": len(np.spec.ingress or []),
                "egress_rules": len(np.spec.egress or []),
            })
        return result
    except client.ApiException as exc:
        raise McpError(f"K8s API error: {exc}") from exc
    except McpError:
        raise
    except Exception as exc:
        raise McpError(f"Error: {exc}") from exc
