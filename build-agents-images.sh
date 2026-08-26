#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

HARBOR="harbor.mrrobot.fs"
HARBOR_USER="admin"
HARBOR_PASS="Harbor12345"

echo "=== 1. LOGIN TO HARBOR ==="
crane auth login "$HARBOR" -u "$HARBOR_USER" -p "$HARBOR_PASS" 2>&1
echo ""

echo "=== 2. COPY agents-platform SOURCE TO NODE ==="
# Source is already on the node via /mnt/c
APPSRC="/mnt/c/Users/germa/Documents/engineering/agents-platform"
ls -la "$APPSRC/Dockerfile.api" 2>&1
ls -la "$APPSRC/Dockerfile.worker" 2>&1
ls -la "$APPSRC/pyproject.toml" 2>&1
echo ""

echo "=== 3. BUILD API IMAGE ==="
cd "$APPSRC"
docker build -f Dockerfile.api -t "$HARBOR/ghl/agents-platform-api:latest" . 2>&1 | tail -10
echo ""

echo "=== 4. BUILD WORKER IMAGE ==="
docker build -f Dockerfile.worker -t "$HARBOR/ghl/agents-platform-worker:latest" . 2>&1 | tail -10
echo ""

echo "=== 5. PUSH API IMAGE ==="
docker push "$HARBOR/ghl/agents-platform-api:latest" 2>&1 | tail -5
echo ""

echo "=== 6. PUSH WORKER IMAGE ==="
docker push "$HARBOR/ghl/agents-platform-worker:latest" 2>&1 | tail -5
echo ""

echo "=== 7. CHECK MCP WEB-SEARCH AND SOURCE-VALIDATOR ==="
# These are in the mcps repo
MCPSRC="/mnt/c/Users/germa/Documents/engineering/mcps"
ls -la "$MCPSRC/mcp-web-search/" 2>&1 | head -5
ls -la "$MCPSRC/mcp-source-validator/" 2>&1 | head -5
echo ""

echo "DONE"
