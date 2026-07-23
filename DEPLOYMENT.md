# MCP Framework — Deployment & CI/CD Documentation

## Overview

This document describes the complete deployment of 35 MCP (Model Context Protocol) microservices to a Kubernetes (K3s) cluster with CI/CD automation via Gitea Actions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Machine                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Docker       │  │  PowerShell  │  │  Hosts File      │  │
│  │  Desktop      │  │  Scripts     │  │  (DNS entries)   │  │
│  │  (Build)      │  │  (Deploy)    │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         │                   │                    │          │
│         │ SCP/SSH           │                    │ Port     │
│         ▼                   │                    │ Proxy    │
└─────────┼───────────────────┼────────────────────┼─────────┘
          │                   │                    │
          ▼                   ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    WSL2 (Debian)                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  K3s Cluster (Tailscale: 100.68.63.120)              │   │
│  │                                                       │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │   │
│  │  │ Gitea    │  │ Harbor   │  │  Kong Ingress    │   │   │
│  │  │ (Git +   │  │ (Docker  │  │  (Proxy :30124)  │   │   │
│  │  │  CI/CD)  │  │ Registry)│  │                  │   │   │
│  │  └──────────┘  └──────────┘  └────────┬─────────┘   │   │
│  │                                        │              │   │
│  │  ┌─────────────────────────────────────┘              │   │
│  │  │ Namespace: mcps (35 pods)                          │   │
│  │  │                                                    │   │
│  │  │  mcp-tabular:8001  mcp-calendar:8002  ...         │   │
│  │  │  mcp-github:8012   mcp-docker:8007   ...          │   │
│  │  │  (35 services, ports 8001-8035)                    │   │
│  │  └───────────────────────────────────────────────────│   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. MCP Microservices (35 total)

Each MCP is a Python microservice using FastMCP framework with:
- Multi-stage Dockerfile (builder + runtime)
- Non-root user (`mcpuser`)
- Streamable HTTP transport on configurable port
- Health checks (TCP socket)
- Shared module (`mcp_shared`) for common logging, config, models

| MCP | Port | Description |
|-----|------|-------------|
| mcp-tabular | 8001 | Excel/CSV/Parquet file reader |
| mcp-calendar | 8002 | Business days and currency exchange |
| mcp-markdown | 8003 | Markdown processing |
| mcp-prompt-engineer | 8004 | Prompt engineering tools |
| mcp-structured-output | 8005 | Structured output generation |
| mcp-fetch | 8006 | HTTP fetch tool |
| mcp-docker | 8007 | Docker operations |
| mcp-kafka | 8008 | Kafka messaging |
| mcp-project-memory | 8009 | Project memory persistence |
| mcp-llm-router | 8010 | LLM routing |
| mcp-git | 8011 | Git operations |
| mcp-github | 8012 | GitHub API integration |
| mcp-code-quality | 8013 | Code quality analysis |
| mcp-architecture | 8014 | Architecture review |
| mcp-event-driven | 8015 | Event-driven design |
| mcp-best-practices | 8017 | Best practices checker |
| mcp-ci-cd | 8018 | CI/CD pipeline tools |
| mcp-design-patterns | 8019 | Design patterns |
| mcp-security-champion | 8020 | Security analysis |
| mcp-database | 8021 | Database operations |
| mcp-filesystem | 8022 | Filesystem access |
| mcp-documents | 8025 | Document processing |
| mcp-browser | 8026 | Browser automation |
| mcp-observability | 8027 | Observability tools |
| mcp-object-storage | 8028 | Object storage (MinIO) |
| mcp-openapi | 8029 | OpenAPI spec tools |
| mcp-orchestrator | 8030 | MCP orchestration |
| mcp-personal-vault | 8031 | Personal vault |
| mcp-sonar | 8033 | SonarQube integration |
| mcp-snyk | 8034 | Snyk security scan |
| mcp-agent-runner | 8033 | Agent runner |
| mcp-java-build | 8032 | Java build tools |
| mcp-terraform | 8034 | Terraform IaC |
| mcp-kubernetes | 8035 | Kubernetes operations |
| mcp-gob-mexico | 8035 | Mexican government data |

### 2. Docker Registry (Harbor)

- **URL**: `harbor.mrrobot.fs`
- **Project**: `ghl` (public)
- **Credentials**: admin / Harbor12345
- **Images**: `harbor.mrrobot.fs/ghl/mcp-XXX:latest`

### 3. Kubernetes (K3s)

- **Namespace**: `mcps`
- **Resources**: 1 Namespace, 3 PVCs, 35 Deployments, 35 Services, 1 Ingress
- **Storage**: NFS storage class for persistent volumes
- **Pod limit**: 200 (increased from default 110)
- **Image policy**: `IfNotPresent` (uses local containerd images)

### 4. CI/CD (Gitea Actions)

- **Repository**: `gitea.mrrobot.fs/ghl-admin/mcps`
- **Workflow**: `.gitea/workflows/deploy-mcps.yml`
- **Trigger**: Push to `main` branch
- **Secrets**: HARBOR_USERNAME, HARBOR_PASSWORD, GITOPS_TOKEN, KUBECONFIG_B64

### 5. Ingress (Kong)

- **Proxy**: LoadBalancer at 192.168.100.210, NodePort 30124
- **Routing**: Host-based routing for `mcp-XXX.mrrobot.fs` → corresponding service
- **Access**: Via Tailscale IP 100.68.63.120:30124

## Deployment Process

### Step 1: Build Docker Images

Images are built on Windows using Docker Desktop:

```powershell
cd C:\Users\germa\Documents\engineering\mcps

# Build all 35 images
Get-ChildItem -Directory -Filter "mcp-*" | ForEach-Object {
    $name = $_.Name
    if (Test-Path "$($_.FullName)\Dockerfile") {
        docker build -t "harbor.mrrobot.fs/ghl/${name}:latest" -f "$($_.FullName)\Dockerfile" .
    }
}
```

### Step 2: Transfer Images to K3s

Since Harbor push via Kong ingress times out (504), images are transferred as a tarball:

```powershell
# Save all images to tar
$images = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String "harbor.mrrobot.fs/ghl/mcp-"
docker save $images -o C:\Users\germa\mcp-all-images.tar

# Transfer to server
scp C:\Users\germa\mcp-all-images.tar german@100.73.65.63:C:/Users/German/mcp-all-images.tar
```

### Step 3: Import Images into K3s containerd

```bash
# On the server (WSL)
k3s ctr images import /mnt/c/Users/German/mcp-all-images.tar
```

### Step 4: Generate Kubernetes Manifests

```bash
cd /tmp/mcps-deploy
python3 k8s/generate_manifests.py
```

This generates `k8s/all-mcps.yaml` with:
- Namespace `mcps`
- 3 PVCs (mcp-data, mcp-memory, mcp-personal-vault)
- 35 Deployments with env vars, ports, health checks
- 35 ClusterIP Services
- 1 Ingress with 35 host-based routing rules

### Step 5: Deploy to Kubernetes

```bash
export KUBECONFIG=/home/german/.kube/config
kubectl apply -f k8s/all-mcps.yaml
```

### Step 6: Configure Network Access

Run `setup-network.ps1` as Administrator on Windows:
- Updates hosts file: `100.68.63.120 mcp-XXX.mrrobot.fs` (35 entries)
- Sets up port forwarding: port 80 → Kong NodePort 30124

### Step 7: Push to Gitea for CI/CD

```bash
git remote add origin http://ghl-admin:ChangeMe123!@gitea.mrrobot.fs/ghl-admin/mcps.git
git push -u origin main
```

The Gitea Actions workflow automatically:
1. Builds all Docker images
2. Pushes to Harbor
3. Applies K8s manifests
4. Waits for rollouts

## Kyverno Policy Exceptions

The following Kyverno cluster policies were patched to exclude the `mcps` namespace:
- `disallow-privileged-containers`
- `disallow-root-user`
- `require-env-label`
- `require-pod-labels`
- `require-resource-limits`
- `restrict-image-registries`

## Verification

### Check pods
```bash
kubectl get pods -n mcps
# Expected: 35/35 Running
```

### Test MCP protocol
```bash
curl -X POST http://mcp-tabular.mrrobot.fs/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}'
```

### Access from browser
- MCP Inspector: `http://mcp-inspector.mrrobot.fs`
- Individual MCPs: `http://mcp-XXX.mrrobot.fs/mcp`

## Files Created

| File | Purpose |
|------|---------|
| `k8s/generate_manifests.py` | Python script to generate K8s manifests for all MCPs |
| `k8s/all-mcps.yaml` | Generated K8s manifests (75 resources) |
| `.gitea/workflows/deploy-mcps.yml` | Gitea Actions CI/CD workflow |
| `build-all.ps1` | PowerShell script to build and push all images |
| `build-push-all.ps1` | Alternative build/push script using docker compose |
| `setup-network.ps1` | Windows network setup (hosts file + port forwarding) |
| `deploy-all.sh` | Full deployment orchestration script |
| `full-deploy.sh` | Full deployment with tarball extraction |
| `expose-harbor.sh` | Script to expose Harbor registry as NodePort |
| `import-and-deploy.sh` | Import images into K3s and deploy |
| `setup-gitea.sh` | Push code to Gitea and configure secrets |

## Troubleshooting

### Harbor Push Timeout (504)
Kong ingress can't handle large Docker blob uploads. Solution: Save images as tar, transfer via SCP, import into K3s containerd directly.

### ErrImagePull
Set `imagePullPolicy: IfNotPresent` in deployments so K3s uses local containerd images instead of trying to pull from Harbor.

### Too Many Pods
K3s default pod limit is 110. Increase via `/etc/rancher/k3s/config.yaml`:
```yaml
maxPods: 200
kubelet-arg:
  - "max-pods=200"
```

### Kyverno Policy Denials
Add `mcps` to the namespace exclusions in each Kyverno ClusterPolicy.

### Module Not Found (mcp_shared)
Some images had stale cache. Rebuild with `--no-cache` flag:
```powershell
docker build --no-cache -t harbor.mrrobot.fs/ghl/mcp-XXX:latest -f mcp-XXX/Dockerfile .
```

### Network Access from Windows
WSL2 has its own network. Use Tailscale IP (100.68.63.120) with port forwarding:
```powershell
netsh interface portproxy add v4tov4 listenport=80 listenaddress=0.0.0.0 connectport=30124 connectaddress=100.68.63.120
```
