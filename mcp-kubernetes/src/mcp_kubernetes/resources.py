"""Resources de solo lectura para mcp-kubernetes."""

from __future__ import annotations

import json


def kubernetes_configuration() -> str:
    return json.dumps(
        {
            "server_name": "mcp-kubernetes",
            "version": "1.0.0",
            "namespace": "default",
            "allow_write": False,
            "in_cluster": False,
        },
        indent=2,
        ensure_ascii=False,
    )


def kubernetes_basics() -> str:
    return (
        "# Kubernetes Basics\n\n"
        "## Conceptos\n"
        "- Pod: unidad minima desplegable\n"
        "- Deployment: gestiona replicas de pods\n"
        "- Service: expone pods en red\n"
        "- ConfigMap: configuracion no sensible\n"
        "- Secret: datos sensibles\n"
        "- Namespace: aislamiento logico\n"
        "- Node: maquina del cluster\n\n"
        "## Arquitectura\n"
        "- Control Plane: API server, scheduler, controller manager, etcd\n"
        "- Worker Nodes: kubelet, kube-proxy, container runtime\n"
        "- CNI: red de pods\n"
        "- CSI: almacenamiento\n"
        "- CRI: container runtime"
    )


def kubernetes_best_practices() -> str:
    return (
        "# Kubernetes Best Practices\n\n"
        "## Pods\n"
        "- Un proceso principal por pod\n"
        "- Usar liveness y readiness probes\n"
        "- Definir resource requests y limits\n"
        "- Usar configmaps y secrets, no hardcodear\n\n"
        "## Deployments\n"
        "- Usar RollingUpdate strategy\n"
        "- Definir PDB (PodDisruptionBudget)\n"
        "- Usar HPA (HorizontalPodAutoscaler)\n"
        "- Versionar imagenes con tags especificos\n\n"
        "## Seguridad\n"
        "- RBAC: least privilege\n"
        "- ServiceAccounts dedicados\n"
        "- NetworkPolicies para aislar trafico\n"
        "- SecurityContext: runAsNonRoot, readOnlyRootFS\n"
        "- Usar secrets en variables de entorno\n\n"
        "## Observabilidad\n"
        "- Labels consistentes\n"
        "- Annotations para metadata\n"
        "- Logs estructurados a stdout\n"
        "- Metrics con Prometheus"
    )


def kubernetes_quick_reference() -> str:
    return (
        "# Referencia rapida\n\n"
        "## Tools\n"
        "- kubernetes_list_namespaces()\n"
        "- kubernetes_list_pods(namespace)\n"
        "- kubernetes_list_deployments(namespace)\n"
        "- kubernetes_pod_logs(pod, namespace)\n"
        "- kubernetes_scale_deployment(deployment, replicas)\n"
        "- kubernetes_list_services(namespace)\n"
        "- kubernetes_list_configmaps(namespace)\n"
        "- kubernetes_list_secrets(namespace)\n"
        "- kubernetes_get_pod(pod, namespace)\n"
        "- kubernetes_deployment_status(deployment)\n"
        "- kubernetes_list_events(namespace)\n"
        "- kubernetes_list_nodes()\n"
        "- kubernetes_cluster_info()\n"
        "- kubernetes_restart_deployment(deployment)\n"
        "- kubernetes_resource_quotas(namespace)\n\n"
        "## Variables .env\n"
        "- KUBERNETES_CONTEXT\n"
        "- KUBERNETES_NAMESPACE\n"
        "- KUBERNETES_ALLOW_WRITE\n"
        "- KUBERNETES_IN_CLUSTER"
    )


def kubernetes_error_codes() -> str:
    return json.dumps(
        {
            "errors": [
                {"code": -32000, "description": "Error de validacion"},
                {"code": -32603, "description": "Error interno del servidor"},
                {"code": -32001, "description": "ValidationError: campo invalido"},
                {"code": -32002, "description": "Write no permitido (ALLOW_WRITE=false)"},
                {"code": -32003, "description": "Recurso no encontrado"},
                {"code": -32004, "description": "Error de conexion con cluster"},
            ]
        },
        indent=2,
        ensure_ascii=False,
    )


def kubernetes_troubleshooting() -> str:
    return (
        "# Troubleshooting\n\n"
        "## No se puede conectar al cluster\n"
        "- Verificar kubeconfig\n"
        "- Verificar KUBERNETES_CONTEXT\n"
        "- Verificar conectividad de red\n"
        "- Verificar permisos RBAC\n\n"
        "## Pod en estado Pending\n"
        "- Verificar recursos disponibles en nodos\n"
        "- Verificar PersistentVolumeClaims\n"
        "- Verificar node selectors y taints\n"
        "- Verificar ResourceQuotas\n\n"
        "## Pod en estado CrashLoopBackOff\n"
        "- Revisar logs: kubernetes_pod_logs\n"
        "- Verificar imagen y tag\n"
        "- Verificar variables de entorno\n"
        "- Verificar liveness probe\n\n"
        "## Deployment no escala\n"
        "- Verificar KUBERNETES_ALLOW_WRITE=true\n"
        "- Verificar permisos RBAC\n"
        "- Verificar ResourceQuotas\n"
        "- Verificar PDB"
    )


def kubernetes_examples() -> str:
    return (
        "# Ejemplos\n\n"
        "## Listar namespaces\n"
        "kubernetes_list_namespaces()\n\n"
        "## Listar pods\n"
        'kubernetes_list_pods(namespace="default")\n\n'
        "## Logs de un pod\n"
        'kubernetes_pod_logs(pod="api-xxx", namespace="default")\n\n'
        "## Escalar deployment\n"
        'kubernetes_scale_deployment(deployment="api", replicas=3)\n\n'
        "## Info del cluster\n"
        "kubernetes_cluster_info()"
    )


def kubernetes_rbac() -> str:
    return (
        "# RBAC (Role-Based Access Control)\n\n"
        "## Componentes\n"
        "- Role: permisos dentro de un namespace\n"
        "- ClusterRole: permisos a nivel cluster\n"
        "- RoleBinding: vincula Role con ServiceAccount\n"
        "- ClusterRoleBinding: vincula ClusterRole con ServiceAccount\n\n"
        "## Verbos comunes\n"
        "- get, list, watch: lectura\n"
        "- create, update, patch, delete: escritura\n"
        "- *: todos los verbos\n\n"
        "## Mejores practicas\n"
        "- Least privilege: solo los permisos necesarios\n"
        "- ServiceAccounts dedicados por aplicacion\n"
        "- No usar cluster-admin para apps\n"
        "- Auditar bindings regularmente\n"
        "- Usar namespaces para aislar permisos\n\n"
        "## Ejemplo\n"
        "```yaml\n"
        "apiVersion: rbac.authorization.k8s.io/v1\n"
        "kind: Role\n"
        "metadata:\n"
        "  name: pod-reader\n"
        "rules:\n"
        "- apiGroups: [\"\"]\n"
        "  resources: [\"pods\"]\n"
        "  verbs: [\"get\", \"list\"]\n"
        "```"
    )


def kubernetes_networking() -> str:
    return (
        "# Kubernetes Networking\n\n"
        "## Service Types\n"
        "- ClusterIP: interno al cluster (default)\n"
        "- NodePort: expone en puerto del nodo\n"
        "- LoadBalancer: cloud provider LB\n"
        "- ExternalName: DNS CNAME\n\n"
        "## Ingress\n"
        "- HTTP/L7 routing\n"
        "- TLS termination\n"
        "- Name-based virtual hosting\n"
        "- Path-based routing\n\n"
        "## NetworkPolicies\n"
        "- Control de trafico entre pods\n"
        "- Ingress y egress rules\n"
        "- Label selectors\n"
        "- Namespace selectors\n\n"
        "## DNS\n"
        "- CoreDNS: servicio de DNS del cluster\n"
        "- service.namespace.svc.cluster.local\n"
        "- pod-ip-dashed.namespace.pod.cluster.local\n\n"
        "## CNI Plugins\n"
        "- Calico: networking + security\n"
        "- Cilium: eBPF-based\n"
        "- Flannel: simple overlay\n"
        "- Weave: mesh networking"
    )


def kubernetes_storage() -> str:
    return (
        "# Kubernetes Storage\n\n"
        "## Conceptos\n"
        "- PV (PersistentVolume): almacenamiento del cluster\n"
        "- PVC (PersistentVolumeClaim): solicitud de PV\n"
        "- StorageClass: provisionamiento dinamico\n"
        "- Volume: almacenamiento efimero\n\n"
        "## Tipos de volumen\n"
        "- emptyDir: efimero, compartido entre contenedores\n"
        "- configMap/secret: montar configuracion\n"
        "- persistentVolumeClaim: almacenamiento persistente\n"
        "- hostPath: directorio del nodo (no recomendado)\n\n"
        "## Access Modes\n"
        "- ReadWriteOnce (RWO): un nodo\n"
        "- ReadOnlyMany (ROX): multiples nodos lectura\n"
        "- ReadWriteMany (RWX): multiples nodos escritura\n\n"
        "## Reclaim Policies\n"
        "- Retain: mantener PV despues de PVC delete\n"
        "- Delete: eliminar PV y storage\n"
        "- Recycle: limpiar (deprecated)\n\n"
        "## Mejores practicas\n"
        "- Usar StorageClass para provisionamiento dinamico\n"
        "- Definir requests de almacenamiento\n"
        "- Usar volume snapshots para backups\n"
        "- Considerar CSI drivers"
    )


def kubernetes_security() -> str:
    return (
        "# Kubernetes Security\n\n"
        "## Pod Security\n"
        "- SecurityContext: runAsNonRoot, runAsUser\n"
        "- readOnlyRootFilesystem: FS inmutable\n"
        "- allowPrivilegeEscalation: false\n"
        "- capabilities: drop ALL\n"
        "- seccompProfile: RuntimeDefault\n\n"
        "## Secret Management\n"
        "- kubectl create secret\n"
        "- External secrets: Vault, AWS SM\n"
        "- Sealed Secrets: gitops\n"
        "- SOPS: encrypted secrets in git\n\n"
        "## Network Security\n"
        "- NetworkPolicies: default deny\n"
        "- Service Mesh: mTLS (Istio, Linkerd)\n"
        "- Ingress TLS\n"
        "- Egress control\n\n"
        "## RBAC\n"
        "- Least privilege\n"
        "- ServiceAccounts dedicados\n"
        "- Auditar accesos\n"
        "- OIDC integration\n\n"
        "## Image Security\n"
        "- Usar imagenes privadas\n"
        "- Image scanning (Trivy, Snyk)\n"
        "- ImagePullSecrets\n"
        "- No usar :latest tag"
    )


def kubernetes_helm() -> str:
    return (
        "# Helm Charts\n\n"
        "## Conceptos\n"
        "- Chart: paquete de recursos Kubernetes\n"
        "- Release: instancia de un chart\n"
        "- Values: configuracion del chart\n"
        "- Templates: plantillas Go\n\n"
        "## Comandos\n"
        "- helm install: instalar chart\n"
        "- helm upgrade: actualizar release\n"
        "- helm rollback: revertir release\n"
        "- helm uninstall: eliminar release\n"
        "- helm list: listar releases\n\n"
        "## Mejores practicas\n"
        "- Versionar charts con semver\n"
        "- Usar values.yaml para defaults\n"
        "- Usar values por entorno\n"
        "- Lint charts: helm lint\n"
        "- Test charts: helm test\n\n"
        "## Estructura\n"
        "```\n"
        "mychart/\n"
        "  Chart.yaml\n"
        "  values.yaml\n"
        "  templates/\n"
        "    deployment.yaml\n"
        "    service.yaml\n"
        "  charts/  # dependencies\n"
        "```"
    )


def kubernetes_health_checks() -> str:
    return (
        "# Health Checks\n\n"
        "## Tipos de probes\n"
        "- livenessProbe: el pod esta vivo?\n"
        "- readinessProbe: el pod esta listo para servir?\n"
        "- startupProbe: el pod ha iniciado?\n\n"
        "## Tipos de probe\n"
        "- HTTP GET: status code 200-399\n"
        "- TCP socket: conexion exitosa\n"
        "- exec: comando retorna 0\n\n"
        "## Configuracion\n"
        "```yaml\n"
        "livenessProbe:\n"
        "  httpGet:\n"
        "    path: /health\n"
        "    port: 8080\n"
        "  initialDelaySeconds: 30\n"
        "  periodSeconds: 10\n"
        "  failureThreshold: 3\n"
        "```\n\n"
        "## Mejores practicas\n"
        "- Usar readiness antes que liveness\n"
        "- initialDelaySeconds suficiente para startup\n"
        "- No hacer liveness demasiado agresivo\n"
        "- Usar startupProbe para apps lentas\n"
        "- Endpoint dedicado /health o /ready"
    )


def kubernetes_autoscaling() -> str:
    return (
        "# Kubernetes Autoscaling\n\n"
        "## HPA (HorizontalPodAutoscaler)\n"
        "- Escala pods basado en metricas\n"
        "- CPU, memoria, custom metrics\n"
        "- Min y max replicas\n"
        "- Target utilization\n\n"
        "## VPA (VerticalPodAutoscaler)\n"
        "- Ajusta requests y limits\n"
        "- Modos: Auto, Recreate, Off\n"
        "- No compatible con HPA (mismas metricas)\n\n"
        "## Cluster Autoscaler\n"
        "- Agrega/remueve nodos\n"
        "- Cloud provider integration\n"
        "- Scale down con grace period\n\n"
        "## KEDA\n"
        "- Event-driven autoscaling\n"
        "- Scale to zero\n"
        "- Scalers: Kafka, RabbitMQ, AWS SQS\n"
        "- Custom metrics\n\n"
        "## Configuracion HPA\n"
        "```yaml\n"
        "apiVersion: autoscaling/v2\n"
        "kind: HorizontalPodAutoscaler\n"
        "spec:\n"
        "  minReplicas: 2\n"
        "  maxReplicas: 10\n"
        "  metrics:\n"
        "  - type: Resource\n"
        "    resource:\n"
        "      name: cpu\n"
        "      target:\n"
        "        type: Utilization\n"
        "        averageUtilization: 70\n"
        "```"
    )


def kubernetes_gitops() -> str:
    return (
        "# GitOps\n\n"
        "## Conceptos\n"
        "- Git como source of truth\n"
        "- Declarative infrastructure\n"
        "- Continuous deployment via pull\n"
        "- Reconciliation loop\n\n"
        "## Tools\n"
        "- ArgoCD: pull-based, UI rica\n"
        "- Flux: pull-based, lightweight\n"
        "- Jenkins X: CI/CD + GitOps\n\n"
        "## ArgoCD\n"
        "- Aplicaciones declarativas\n"
        "- Sync automatico o manual\n"
        "- Health assessment\n"
        "- Multi-cluster\n"
        "- SSO integration\n\n"
        "## Flux\n"
        "- GitRepository source\n"
        "- Kustomize/Helm reconciliation\n"
        "- Notification controllers\n"
        "- Image automation\n\n"
        "## Mejores practicas\n"
        "- Un repo por entorno o monorepo\n"
        "- PR-based deployments\n"
        "- Drift detection\n"
        "- Rollback via git revert\n"
        "- Secrets con Sealed Secrets o SOPS"
    )
