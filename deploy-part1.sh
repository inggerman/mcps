#!/bin/bash
# Part 1: Push code to Gitea and build images
export KUBECONFIG=/home/german/.kube/config

GITEA_POD_IP=$(k3s kubectl get pod -n gitea -l app.kubernetes.io/name=gitea -o jsonpath='{.items[0].status.podIP}' 2>/dev/null)
GITEA_URL="http://${GITEA_POD_IP}:3000"
GITEA_USER="ghl-admin"
GITEA_PASS="ChangeMe123!"
HARBOR_REGISTRY="harbor.mrrobot.fs"
HARBOR_PROJECT="ghl"

echo "=== STEP 1: Extract MCP code ==="
rm -rf /tmp/mcps-deploy
mkdir -p /tmp/mcps-deploy
cd /tmp/mcps-deploy
tar -xzf /mnt/c/Users/German/mcps-deploy.tar.gz
echo "  Extracted $(ls -d mcp-*/ 2>/dev/null | wc -l) MCP directories"
echo ""

echo "=== STEP 2: Generate K8s manifests ==="
pip install pyyaml -q 2>/dev/null
python3 k8s/generate_manifests.py 2>&1
echo ""

echo "=== STEP 3: Push code to Gitea ==="
git init
git config user.name "GHL Admin"
git config user.email "admin@mrrobot.fs"
git remote add origin "http://${GITEA_USER}:${GITEA_PASS}@${GITEA_POD_IP}:3000/ghl-admin/mcps.git"
git add -A
git commit -m "feat: initial MCP framework with K8s deployment and CI/CD"
git branch -M main
git push -u origin main --force 2>&1 | tail -5
echo ""

echo "=== STEP 4: Login to Harbor ==="
echo "Harbor12345" | docker login ${HARBOR_REGISTRY} -u admin --password-stdin 2>/dev/null
echo ""

echo "=== STEP 5: Build and push all images ==="
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
  
  echo -n "  [$CURRENT/$TOTAL] $mcp_name... "
  
  if docker build -t "${HARBOR_REGISTRY}/${HARBOR_PROJECT}/${mcp_name}:latest" \
    -f "$mcp_dir/Dockerfile" . > /tmp/mcp-build.log 2>&1; then
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
    tail -3 /tmp/mcp-build.log 2>/dev/null
  fi
done

echo ""
echo "  Build: ${SUCCEEDED}/${TOTAL} OK, ${FAILED} failed"
echo ""
echo "DONE_PART1"
