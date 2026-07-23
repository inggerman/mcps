#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

GITEA_POD_IP=$(k3s kubectl get pod -n gitea -l app.kubernetes.io/name=gitea -o jsonpath='{.items[0].status.podIP}' 2>/dev/null)
GITEA_URL="http://${GITEA_POD_IP}:3000"
GITEA_USER="ghl-admin"
GITEA_PASS="ChangeMe123!"

echo "=== 1. SET SECRETS VIA GITEA API (correct format) ==="

# Gitea API for secrets uses POST with data field
set_secret() {
  NAME=$1
  VALUE=$2
  RESULT=$(curl -s -X PUT -u "${GITEA_USER}:${GITEA_PASS}" \
    -H "Content-Type: application/json" \
    -d "{\"data\":\"${VALUE}\"}" \
    "${GITEA_URL}/api/v1/repos/ghl-admin/mcps/actions/secrets/${NAME}" 2>&1)
  echo "  ${NAME}: ${RESULT}"
}

set_secret "HARBOR_USERNAME" "admin"
set_secret "HARBOR_PASSWORD" "Harbor12345"
set_secret "GITOPS_TOKEN" "ChangeMe123!"

KUBECONFIG_B64=$(base64 -w0 /home/german/.kube/config 2>/dev/null || cat /home/german/.kube/config | base64 | tr -d '\n')
set_secret "KUBECONFIG_B64" "${KUBECONFIG_B64}"
echo ""

echo "=== 2. LIST SECRETS ==="
curl -s -u "${GITEA_USER}:${GITEA_PASS}" \
  "${GITEA_URL}/api/v1/repos/ghl-admin/mcps/actions/secrets" 2>&1
echo ""
echo ""

echo "=== 3. VERIFY MCP PODS STILL RUNNING ==="
k3s kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l | xargs echo "  Total pods:"
k3s kubectl get pods -n mcps --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | xargs echo "  Running:"
echo ""

echo "=== 4. TEST MCP ACCESS FROM INSIDE CLUSTER ==="
# Test mcp-tabular
TABULAR_IP=$(k3s kubectl get svc mcp-tabular -n mcps -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "  mcp-tabular (${TABULAR_IP}:8001):"
curl -s --connect-timeout 5 -X POST "http://${TABULAR_IP}:8001/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>&1 | head -3
echo ""

# Test mcp-calendar
CALENDAR_IP=$(k3s kubectl get svc mcp-calendar -n mcps -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "  mcp-calendar (${CALENDAR_IP}:8002):"
curl -s --connect-timeout 5 -X POST "http://${CALENDAR_IP}:8002/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>&1 | head -3
echo ""

echo "=== 5. TEST MCP ACCESS VIA INGRESS ==="
# Test via Kong ingress
curl -s --connect-timeout 5 -X POST "http://mcp-tabular.mrrobot.fs/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Host: mcp-tabular.mrrobot.fs" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>&1 | head -3
echo ""

echo "=== 6. INGRESS STATUS ==="
k3s kubectl get ingress -n mcps 2>&1
echo ""

echo "=== 7. KONG PROXY IP ==="
k3s kubectl get svc -n kong kong-proxy -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "  Not found"
k3s kubectl get svc -n kong kong-proxy -o jsonpath='{.spec.externalIPs}' 2>/dev/null || echo ""
echo ""

echo "DONE"
