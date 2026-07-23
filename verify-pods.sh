#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. WAIT 60s FOR READINESS ==="
sleep 60
echo ""

echo "=== 2. FULL POD STATUS ==="
k3s kubectl get pods -n mcps -o wide 2>&1
echo ""

RUNNING=$(k3s kubectl get pods -n mcps --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
READY=$(k3s kubectl get pods -n mcps -o jsonpath='{.items[*].status.containerStatuses[*].ready}' 2>/dev/null | tr ' ' '\n' | grep -c true 2>/dev/null || echo 0)
TOTAL=$(k3s kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l)
echo "  Running: ${RUNNING}/${TOTAL}"
echo "  Ready: ${READY}/${TOTAL}"
echo ""

echo "=== 3. FIX mcp-docker (remove docker socket, use containerd) ==="
k3s kubectl patch deploy mcp-docker -n mcps --type=json -p='[{"op":"remove","path":"/spec/template/spec/volumes"}]' 2>/dev/null
k3s kubectl patch deploy mcp-docker -n mcps --type=json -p='[{"op":"remove","path":"/spec/template/spec/containers/0/volumeMounts"}]' 2>/dev/null
echo ""

echo "=== 4. CHECK mcp-github ERROR ==="
k3s kubectl logs mcp-github-5c8dbb467-x8srp -n mcps --tail=20 2>&1
echo ""

echo "=== 5. CHECK mcp-prompt-engineer ==="
k3s kubectl logs -n mcps -l app=mcp-prompt-engineer --tail=10 2>&1
echo ""

echo "=== 6. SERVICES ==="
k3s kubectl get svc -n mcps 2>&1 | wc -l | xargs echo "  Services:"
echo ""

echo "=== 7. INGRESS ==="
k3s kubectl get ingress -n mcps 2>&1
echo ""

echo "=== 8. TEST CONNECTIVITY TO A RUNNING MCP ==="
# Get the ClusterIP of mcp-tabular
TABULAR_IP=$(k3s kubectl get svc mcp-tabular -n mcps -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "  mcp-tabular ClusterIP: $TABULAR_IP"
curl -s --connect-timeout 5 "http://${TABULAR_IP}:8001/mcp" 2>&1 | head -5
echo ""
echo "  (testing with streamable-http)"
curl -s --connect-timeout 5 -X POST "http://${TABULAR_IP}:8001/mcp" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"initialize","id":1}' 2>&1 | head -5
echo ""

echo "DONE"
