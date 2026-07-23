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
echo "  MCP DEPLOYMENT - FULL PIPELINE"
echo "============================================"
echo ""

# Step 1: Extract code
echo "=== STEP 1: Extract MCP code ==="
rm -rf /tmp/mcps-deploy
mkdir -p /tmp/mcps-deploy
cd /tmp/mcps-deploy
tar -xzf /mnt/c/Users/German/mcps-deploy.tar.gz
echo "  Extracted to /tmp/mcps-deploy"
ls -d mcp-*/ | wc -l | xargs echo "  MCP directories found:"
echo ""

# Step 2: Create Gitea repo
echo "=== STEP 2: Create Gitea repo ==="
REPO_EXISTS=$(curl -s -o /dev/null -w "%{http_code}" -u "${GITEA_USER}:${GITEA_PASS}" "${GITEA_URL}/api/v1/repos/ghl-admin/mcps" 2>/dev/null)
if [ "$REPO_EXISTS" = "200" ]; then
  echo "  Repo already exists"
else
  curl -s -X POST -u "${GITEA_USER}:${GITEA_PASS}" \
    -H "Content-Type: application/json" \
    -d '{"name":"mcps","description":"MCP Framework - 35 MCP servers","private":false,"auto_init":false}' \
    "${GITEA_URL}/api/v1/user/repos" 2>/dev/null | python3 -c "import json,sys; r=json.load(sys.stdin); print(f'  Created: {r.get(\"full_name\",\"unknown\")}')" 2>/dev/null || echo "  Repo created"
fi
echo ""

# Step 3: Generate K8s manifests
echo "=== STEP 3: Generate K8s manifests ==="
pip install pyyaml -q 2>/dev/null || true
python3 k8s/generate_manifests.py 2>&1
echo ""

# Step 4: Initialize git and push to Gitea
echo "=== STEP 4: Push code to Gitea ==="
git init 2>/dev/null
git config user.name "GHL Admin"
git config user.email "admin@mrrobot.fs"
git remote remove origin 2>/dev/null || true
git remote add origin "http://${GITEA_USER}:${GITEA_PASS}@${GITEA_POD_IP}:3000/ghl-admin/mcps.git"
git add -A
git commit -m "feat: initial MCP framework with K8s deployment and CI/CD" 2>/dev/null || echo "  Nothing to commit"
git branch -M main
git push -u origin main --force 2>&1 | tail -5
echo ""

# Step 5: Build and push all images to Harbor
echo "=== STEP 5: Build and push images to Harbor ==="
echo "  Logging in to Harbor..."
echo "Harbor12345" | docker login ${HARBOR_REGISTRY} -u admin --password-stdin 2>/dev/null || true

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
      tail -3 /tmp/mcp-push.log 2>/dev/null | sed 's/^/    /'
    fi
  else
    echo "BUILD FAILED"
    FAILED=$((FAILED + 1))
    tail -5 /tmp/mcp-build.log 2>/dev/null | sed 's/^/    /'
  fi
done

echo ""
echo "  Build complete: ${SUCCEEDED}/${TOTAL} succeeded, ${FAILED} failed"
echo ""

# Step 6: Create namespace and deploy
echo "=== STEP 6: Deploy to K3s ==="
k3s kubectl apply -f k8s/all-mcps.yaml 2>&1 | grep -E "created|configured|unchanged|error" | head -40
echo ""

# Step 7: Wait for pods to be ready
echo "=== STEP 7: Wait for pods (60s) ==="
sleep 60
echo "Pod status:"
k3s kubectl get pods -n mcps 2>&1
echo ""

# Step 8: Check what's running
echo "=== STEP 8: Deployment status ==="
RUNNING=$(k3s kubectl get pods -n mcps --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
TOTAL_PODS=$(k3s kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l)
echo "  Running pods: ${RUNNING}/${TOTAL_PODS}"
echo ""

# Step 9: Show services and ingress
echo "=== STEP 9: Services ==="
k3s kubectl get svc -n mcps 2>&1
echo ""
echo "=== Ingress ==="
k3s kubectl get ingress -n mcps 2>&1
echo ""

echo "============================================"
echo "  DEPLOYMENT SUMMARY"
echo "============================================"
echo "  Images built: ${SUCCEEDED}/${TOTAL}"
echo "  Pods running: ${RUNNING}/${TOTAL_PODS}"
echo "  Namespace: mcps"
echo "  Harbor: ${HARBOR_REGISTRY}/${HARBOR_PROJECT}/mcp-*:latest"
echo "  Access: http://mcp-XXX.mrrobot.fs/mcp"
echo "============================================"
