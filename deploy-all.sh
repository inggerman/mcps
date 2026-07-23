#!/bin/bash
set -e
export KUBECONFIG=/home/german/.kube/config

GITEA_POD_IP=$(k3s kubectl get pod -n gitea -l app.kubernetes.io/name=gitea -o jsonpath='{.items[0].status.podIP}' 2>/dev/null)
GITEA_URL="http://${GITEA_POD_IP}:3000"
GITEA_USER="ghl-admin"
GITEA_PASS="ChangeMe123!"
HARBOR_REGISTRY="harbor.mrrobot.fs"
HARBOR_PROJECT="ghl"

echo "============================================"
echo "  MCP DEPLOYMENT SCRIPT"
echo "============================================"
echo ""

# Step 1: Create Gitea repo
echo "=== STEP 1: Create Gitea repo ==="
REPO_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" -u "${GITEA_USER}:${GITEA_PASS}" "${GITEA_URL}/api/v1/repos/ghl-admin/mcps" 2>/dev/null)
if [ "$REPO_EXISTS" = "200" ]; then
  echo "  Repo already exists"
else
  curl -s -X POST -u "${GITEA_USER}:${GITEA_PASS}" \
    -H "Content-Type: application/json" \
    -d '{"name":"mcps","description":"MCP Framework - 35 MCP servers","private":false,"auto_init":false}' \
    "${GITEA_URL}/api/v1/user/repos" 2>/dev/null | python3 -c "import json,sys; r=json.load(sys.stdin); print(f'  Created: {r[\"full_name\"]}')" 2>/dev/null
  echo "  Repo created"
fi
echo ""

# Step 2: Generate K8s manifests
echo "=== STEP 2: Generate K8s manifests ==="
cd /tmp/mcps-deploy
pip install pyyaml -q 2>/dev/null || true
python3 k8s/generate_manifests.py 2>&1
echo ""

# Step 3: Build and push all images to Harbor
echo "=== STEP 3: Build and push images to Harbor ==="
MCPS=$(find . -maxdepth 1 -type d -name "mcp-*" | sort)
TOTAL=$(echo "$MCPS" | wc -l)
CURRENT=0
FAILED=0
SUCCEEDED=0

for mcp_dir in $MCPS; do
  mcp_name=$(basename $mcp_dir)
  CURRENT=$((CURRENT + 1))
  
  if [ ! -f "$mcp_dir/Dockerfile" ]; then
    echo "  [$CURRENT/$TOTAL] SKIP $mcp_name (no Dockerfile)"
    continue
  fi
  
  echo -n "  [$CURRENT/$TOTAL] Building $mcp_name... "
  
  # Build image
  if docker build -t "${HARBOR_REGISTRY}/${HARBOR_PROJECT}/${mcp_name}:latest" \
    -f "$mcp_dir/Dockerfile" . > /tmp/mcp-build.log 2>&1; then
    
    # Push image
    if docker push "${HARBOR_REGISTRY}/${HARBOR_PROJECT}/${mcp_name}:latest" > /tmp/mcp-push.log 2>&1; then
      echo "OK"
      SUCCEEDED=$((SUCCEEDED + 1))
    else
      echo "PUSH FAILED"
      FAILED=$((FAILED + 1))
    fi
  else
    echo "BUILD FAILED"
    FAILED=$((FAILED + 1))
    # Show last 5 lines of build log
    tail -5 /tmp/mcp-build.log 2>/dev/null | sed 's/^/    /'
  fi
done

echo ""
echo "  Build complete: ${SUCCEEDED}/${TOTAL} succeeded, ${FAILED} failed"
echo ""

# Step 4: Create namespace and deploy
echo "=== STEP 4: Deploy to K3s ==="
k3s kubectl apply -f k8s/all-mcps.yaml 2>&1 | head -50
echo ""

# Step 5: Wait for pods to be ready
echo "=== STEP 5: Wait for pods ==="
sleep 30
echo "Pod status:"
k3s kubectl get pods -n mcps 2>&1
echo ""

# Step 6: Add DNS entries
echo "=== STEP 6: DNS configuration ==="
# Get Kong ingress IP
INGRESS_IP=$(k3s kubectl get svc -n kong kong-proxy -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "192.168.100.71")
echo "  Ingress IP: $INGRESS_IP"
echo "  DNS entries needed for *.mrrobot.fs"
echo ""

# Step 7: Show status
echo "=== STEP 7: Final status ==="
echo ""
echo "Pods:"
k3s kubectl get pods -n mcps -o wide 2>&1
echo ""
echo "Services:"
k3s kubectl get svc -n mcps 2>&1
echo ""
echo "Ingress:"
k3s kubectl get ingress -n mcps 2>&1
echo ""

echo "============================================"
echo "  DEPLOYMENT COMPLETE"
echo "============================================"
echo "  MCPs accessible at: http://mcp-XXX.mrrobot.fs/mcp"
echo "  Images in Harbor: ${HARBOR_REGISTRY}/${HARBOR_PROJECT}/mcp-*:latest"
echo "============================================"
