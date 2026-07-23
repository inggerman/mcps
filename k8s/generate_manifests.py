#!/usr/bin/env python3
"""Generate Kubernetes manifests for all MCP servers."""
import yaml
import json

# All 35 MCPs with their configurations
MCPS = [
    {"name": "mcp-tabular", "port": 8001, "env": {"TABULAR_ALLOWED_ROOT": "/data"}, "volumes": [{"name": "mcp-data", "mountPath": "/data", "readOnly": True}]},
    {"name": "mcp-calendar", "port": 8002, "env": {}, "volumes": []},
    {"name": "mcp-markdown", "port": 8003, "env": {"MCP_MARKDOWN_ALLOWED_ROOT": "/data"}, "volumes": [{"name": "mcp-data", "mountPath": "/data", "readOnly": True}]},
    {"name": "mcp-prompt-engineer", "port": 8004, "env": {}, "volumes": []},
    {"name": "mcp-structured-output", "port": 8005, "env": {}, "volumes": []},
    {"name": "mcp-fetch", "port": 8006, "env": {}, "volumes": []},
    {"name": "mcp-docker", "port": 8007, "env": {}, "volumes": [], "privileged": True, "hostPath": "/var/run/docker.sock"},
    {"name": "mcp-kafka", "port": 8008, "env": {}, "volumes": []},
    {"name": "mcp-project-memory", "port": 8009, "env": {"MEMORY_DIR": "/app/.ai-memory", "MEMORY_FILE": "project_memory.json", "MEMORY_PROJECT_NAME": "mcps"}, "volumes": [{"name": "mcp-memory", "mountPath": "/app/.ai-memory", "readOnly": False}]},
    {"name": "mcp-llm-router", "port": 8010, "env": {"ROUTER_LMSTUDIO_BASE_URL": "http://host.docker.internal:1234/v1", "ROUTER_COMPLEXITY_THRESHOLD": "6", "ROUTER_MODEL_FAST": "qwen3-8b", "ROUTER_MODEL_CODE": "devstral-small-2507", "ROUTER_MODEL_REASON": "deepseek-r1-0528-qwen3-8b", "ROUTER_MODEL_LARGE": "qwen2.5-14b-instruct-1m"}, "volumes": []},
    {"name": "mcp-git", "port": 8011, "env": {"GIT_REPO_PATH": "/repo", "GIT_DEFAULT_BRANCH": "main", "GIT_ALLOW_FORCE_PUSH": "false"}, "volumes": []},
    {"name": "mcp-github", "port": 8012, "env": {}, "volumes": []},
    {"name": "mcp-code-quality", "port": 8013, "env": {"CQ_PROJECT_PATH": "/repo", "CQ_LINTER_CMD": "uv run ruff check", "CQ_FORMATTER_CMD": "uv run ruff format", "CQ_TEST_CMD": "uv run pytest"}, "volumes": []},
    {"name": "mcp-architecture", "port": 8014, "env": {"ARCH_PROJECT_PATH": "/repo"}, "volumes": []},
    {"name": "mcp-event-driven", "port": 8015, "env": {"EVENT_SCHEMAS_PATH": "/schemas"}, "volumes": []},
    {"name": "mcp-orchestrator", "port": 8016, "env": {"ORCH_DAGS_PATH": "/dags"}, "volumes": []},
    {"name": "mcp-best-practices", "port": 8017, "env": {"BP_PROJECT_PATH": "/repo", "BP_DOCS_PATH": "/repo/docs"}, "volumes": []},
    {"name": "mcp-ci-cd", "port": 8018, "env": {"CICD_PROJECT_PATH": "/repo"}, "volumes": []},
    {"name": "mcp-design-patterns", "port": 8019, "env": {"DP_PROJECT_PATH": "/repo"}, "volumes": []},
    {"name": "mcp-security-champion", "port": 8020, "env": {"SEC_PROJECT_PATH": "/repo"}, "volumes": []},
    {"name": "mcp-database", "port": 8021, "env": {"DATABASE_URL": "sqlite:////data/database.db", "DATABASE_READ_ONLY": "true"}, "volumes": [{"name": "mcp-data", "mountPath": "/data", "readOnly": False}]},
    {"name": "mcp-filesystem", "port": 8022, "env": {"FILESYSTEM_ROOT": "/data", "FILESYSTEM_ALLOW_WRITE": "false"}, "volumes": [{"name": "mcp-data", "mountPath": "/data", "readOnly": True}]},
    {"name": "mcp-object-storage", "port": 8023, "env": {"OBJECT_STORAGE_ALLOW_WRITE": "false"}, "volumes": []},
    {"name": "mcp-openapi", "port": 8024, "env": {"OPENAPI_SPEC": "/data/openapi.yaml", "OPENAPI_ALLOWED_ROOT": "/data", "OPENAPI_ALLOW_INVOKE": "false"}, "volumes": [{"name": "mcp-data", "mountPath": "/data", "readOnly": True}]},
    {"name": "mcp-documents", "port": 8025, "env": {"DOCUMENTS_ROOT": "/data"}, "volumes": [{"name": "mcp-data", "mountPath": "/data", "readOnly": True}]},
    {"name": "mcp-browser", "port": 8026, "env": {"BROWSER_HEADLESS": "true", "BROWSER_OUTPUT_DIR": "/data/browser"}, "volumes": [{"name": "mcp-data", "mountPath": "/data", "readOnly": False}]},
    {"name": "mcp-kubernetes", "port": 8027, "env": {"KUBERNETES_ALLOW_WRITE": "false"}, "volumes": []},
    {"name": "mcp-observability", "port": 8028, "env": {}, "volumes": []},
    {"name": "mcp-terraform", "port": 8029, "env": {"TERRAFORM_ROOT": "/workspace", "TERRAFORM_ALLOW_APPLY": "false"}, "volumes": []},
    {"name": "mcp-snyk", "port": 8030, "env": {"SNYK_PROJECT_PATH": "/repo"}, "volumes": []},
    {"name": "mcp-sonar", "port": 8031, "env": {"SONAR_PROJECT_PATH": "/repo"}, "volumes": []},
    {"name": "mcp-java-build", "port": 8032, "env": {"JAVA_PROJECT_PATH": "/repo"}, "volumes": []},
    {"name": "mcp-agent-runner", "port": 8033, "env": {"AGENT_PROJECT_PATH": "/repo", "AGENT_N8N_WEBHOOK_BASE_URL": "http://localhost:5678/webhook"}, "volumes": []},
    {"name": "mcp-personal-vault", "port": 8034, "env": {"PERSONAL_VAULT_DATABASE_PATH": "/vault/personal.db", "PERSONAL_VAULT_KEY_FILE": "/vault/vault.key", "PERSONAL_VAULT_ALLOW_WRITE": "true", "PERSONAL_VAULT_ALLOW_HIGHLY_SENSITIVE": "false", "PERSONAL_VAULT_ALLOW_SECRETS": "false"}, "volumes": [{"name": "mcp-personal-vault", "mountPath": "/vault", "readOnly": False}]},
    {"name": "mcp-gob-mexico", "port": 8035, "env": {"GOB_MX_HTTP_TIMEOUT": "30", "GOB_MX_MAX_RETRIES": "3", "GOB_MX_CACHE_TTL": "300"}, "volumes": []},
]

NAMESPACE = "mcps"
HARBOR_REGISTRY = "harbor.mrrobot.fs/ghl"

def generate_namespace():
    return {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {"name": NAMESPACE, "labels": {"istio-injection": "disabled"}}
    }

def generate_deployment(mcp):
    name = mcp["name"]
    port = mcp["port"]
    env = mcp.get("env", {})
    volumes = mcp.get("volumes", [])
    privileged = mcp.get("privileged", False)
    host_path = mcp.get("hostPath")
    
    env_list = [
        {"name": "MCP_TRANSPORT", "value": "streamable-http"},
        {"name": "MCP_HOST", "value": "0.0.0.0"},
        {"name": "MCP_PORT", "value": str(port)},
    ]
    for k, v in env.items():
        env_list.append({"name": k, "value": v})
    
    container = {
        "name": name,
        "image": f"{HARBOR_REGISTRY}/{name}:latest",
        "imagePullPolicy": "IfNotPresent",
        "ports": [{"containerPort": port}],
        "env": env_list,
        "resources": {
            "requests": {"cpu": "50m", "memory": "64Mi"},
            "limits": {"cpu": "500m", "memory": "512Mi"},
        },
        "livenessProbe": {
            "tcpSocket": {"port": port},
            "initialDelaySeconds": 15,
            "periodSeconds": 30,
        },
        "readinessProbe": {
            "tcpSocket": {"port": port},
            "initialDelaySeconds": 5,
            "periodSeconds": 10,
        },
    }
    
    if privileged:
        container["securityContext"] = {"privileged": True}
    
    pod_volumes = []
    for v in volumes:
        vol_name = v["name"]
        pod_volumes.append({
            "name": vol_name,
            "persistentVolumeClaim": {"claimName": vol_name}
        })
        container["volumeMounts"] = container.get("volumeMounts", [])
        container["volumeMounts"].append({
            "name": vol_name,
            "mountPath": v["mountPath"],
            "readOnly": v.get("readOnly", False),
        })
    
    if host_path:
        pod_volumes.append({
            "name": "docker-sock",
            "hostPath": {"path": host_path, "type": "Socket"}
        })
        container["volumeMounts"] = container.get("volumeMounts", [])
        container["volumeMounts"].append({
            "name": "docker-sock",
            "mountPath": host_path,
        })
    
    spec = {
        "replicas": 1,
        "selector": {"matchLabels": {"app": name}},
        "template": {
            "metadata": {"labels": {"app": name}},
            "spec": {
                "containers": [container],
                "restartPolicy": "Always",
            }
        }
    }
    
    if pod_volumes:
        spec["template"]["spec"]["volumes"] = pod_volumes
    
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "namespace": NAMESPACE,
            "labels": {"app": name},
        },
        "spec": spec,
    }

def generate_service(mcp):
    name = mcp["name"]
    port = mcp["port"]
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "namespace": NAMESPACE,
            "labels": {"app": name},
        },
        "spec": {
            "selector": {"app": name},
            "ports": [{"port": port, "targetPort": port, "name": "http"}],
            "type": "ClusterIP",
        },
    }

def generate_pvcs():
    pvcs = []
    for pvc_name, size in [("mcp-data", "5Gi"), ("mcp-memory", "1Gi"), ("mcp-personal-vault", "1Gi")]:
        pvcs.append({
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {"name": pvc_name, "namespace": NAMESPACE},
            "spec": {
                "accessModes": ["ReadWriteMany"],
                "resources": {"requests": {"storage": size}},
                "storageClassName": "nfs-storage",
            },
        })
    return pvcs

def generate_ingress():
    rules = []
    for mcp in MCPS:
        name = mcp["name"]
        port = mcp["port"]
        # Subdomain: mcp-tabular.mrrobot.fs -> mcp-tabular:8001
        short_name = name.replace("mcp-", "")
        rules.append({
            "host": f"mcp-{short_name}.mrrobot.fs",
            "http": {
                "paths": [{
                    "path": "/",
                    "pathType": "Prefix",
                    "backend": {
                        "service": {"name": name, "port": {"number": port}}
                    },
                }]
            },
        })
    
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": "mcps-ingress",
            "namespace": NAMESPACE,
            "annotations": {
                "konghq.com/strip-path": "false",
                "kubernetes.io/ingress.class": "kong",
            },
        },
        "spec": {"rules": rules},
    }

def main():
    docs = []
    docs.append(generate_namespace())
    docs.extend(generate_pvcs())
    for mcp in MCPS:
        docs.append(generate_deployment(mcp))
        docs.append(generate_service(mcp))
    docs.append(generate_ingress())
    
    with open("k8s/all-mcps.yaml", "w") as f:
        yaml.dump_all(docs, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated {len(docs)} resources for {len(MCPS)} MCPs")
    print(f"  - 1 Namespace")
    print(f"  - 3 PVCs")
    print(f"  - {len(MCPS)} Deployments")
    print(f"  - {len(MCPS)} Services")
    print(f"  - 1 Ingress ({len(MCPS)} subdomain rules)")

if __name__ == "__main__":
    main()
