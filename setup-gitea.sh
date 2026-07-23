#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

GITEA_POD_IP=$(k3s kubectl get pod -n gitea -l app.kubernetes.io/name=gitea -o jsonpath='{.items[0].status.podIP}' 2>/dev/null)
GITEA_URL="http://${GITEA_POD_IP}:3000"
GITEA_USER="ghl-admin"
GITEA_PASS="ChangeMe123!"

echo "=== 1. PUSH CODE TO GITEA ==="
cd /tmp/mcps-deploy
git config --global --add safe.directory /tmp/mcps-deploy
git config user.name "GHL Admin"
git config user.email "admin@mrrobot.fs"
git remote remove origin 2>/dev/null || true
git remote add origin "http://${GITEA_USER}:${GITEA_PASS}@${GITEA_POD_IP}:3000/ghl-admin/mcps.git"
git add -A
git commit -m "feat: MCP framework with K8s deployment and CI/CD" 2>/dev/null || echo "  Nothing new to commit"
git branch -M main
git push -u origin main --force 2>&1 | tail -5
echo ""

echo "=== 2. CONFIGURE SECRETS ==="
# HARBOR_USERNAME
curl -s -X PUT -u "${GITEA_USER}:${GITEA_PASS}" \
  -H "Content-Type: application/json" \
  -d '{"value":"admin"}' \
  "${GITEA_URL}/api/v1/repos/ghl-admin/mcps/actions/secrets/HARBOR_USERNAME" 2>/dev/null
echo "  HARBOR_USERNAME: set"

# HARBOR_PASSWORD
curl -s -X PUT -u "${GITEA_USER}:${GITEA_PASS}" \
  -H "Content-Type: application/json" \
  -d '{"value":"Harbor12345"}' \
  "${GITEA_URL}/api/v1/repos/ghl-admin/mcps/actions/secrets/HARBOR_PASSWORD" 2>/dev/null
echo "  HARBOR_PASSWORD: set"

# GITOPS_TOKEN
curl -s -X PUT -u "${GITEA_USER}:${GITEA_PASS}" \
  -H "Content-Type: application/json" \
  -d '{"value":"ChangeMe123!"}' \
  "${GITEA_URL}/api/v1/repos/ghl-admin/mcps/actions/secrets/GITOPS_TOKEN" 2>/dev/null
echo "  GITOPS_TOKEN: set"

# KUBECONFIG_B64
KUBECONFIG_B64=$(base64 -w0 /home/german/.kube/config 2>/dev/null || base64 /home/german/.kube/config 2>/dev/null | tr -d '\n')
curl -s -X PUT -u "${GITEA_USER}:${GITEA_PASS}" \
  -H "Content-Type: application/json" \
  -d "{\"value\":\"${KUBECONFIG_B64}\"}" \
  "${GITEA_URL}/api/v1/repos/ghl-admin/mcps/actions/secrets/KUBECONFIG_B64" 2>/dev/null
echo "  KUBECONFIG_B64: set"
echo ""

echo "=== 3. VERIFY REPO ==="
curl -s -u "${GITEA_USER}:${GITEA_PASS}" "${GITEA_URL}/api/v1/repos/ghl-admin/mcps" 2>/dev/null | python3 -c "import json,sys; r=json.load(sys.stdin); print(f'  Repo: {r[\"full_name\"]}'); print(f'  URL: {r[\"html_url\"]}'); print(f'  Default branch: {r[\"default_branch\"]}')" 2>/dev/null
echo ""

echo "=== 4. VERIFY SECRETS ==="
curl -s -u "${GITEA_USER}:${GITEA_PASS}" "${GITEA_URL}/api/v1/repos/ghl-admin/mcps/actions/secrets" 2>/dev/null | python3 -c "import json,sys; secrets=json.load(sys.stdin); [print(f'  {s[\"name\"]}') for s in secrets]" 2>/dev/null || echo "  Could not list secrets"
echo ""

echo "=== 5. ENABLE ACTIONS ==="
curl -s -X PUT -u "${GITEA_USER}:${GITEA_PASS}" \
  -H "Content-Type: application/json" \
  -d '{"enable_actions":true}' \
  "${GITEA_URL}/api/v1/repos/ghl-admin/mcps" 2>/dev/null | head -c 100
echo ""
echo ""

echo "DONE"
