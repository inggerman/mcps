#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PATCH DEPLOYMENT ENV VAR ==="
kubectl set env deploy/mcp-gob-mexico -n mcps MCP_TRANSPORT=streamable-http MCP_HOST=0.0.0.0 MCP_PORT=8035
echo "Patched env vars"

echo ""
echo "=== 2. ROLLOUT RESTART ==="
kubectl rollout restart deploy/mcp-gob-mexico -n mcps
sleep 15

echo ""
echo "=== 3. CHECK POD ==="
kubectl get pod -n mcps -l app.kubernetes.io/name=mcp-gob-mexico 2>&1

echo ""
echo "=== 4. WAIT ROLLOUT ==="
kubectl rollout status deploy/mcp-gob-mexico -n mcps --timeout=120s 2>&1

echo ""
echo "=== 5. LOGS ==="
kubectl logs -n mcps deploy/mcp-gob-mexico --tail=20 2>&1

echo ""
echo "=== 6. TEST PROTOCOL ==="
SVC_IP=$(kubectl get svc -n mcps mcp-gob-mexico -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
SVC_PORT=$(kubectl get svc -n mcps mcp-gob-mexico -o jsonpath='{.spec.ports[0].port}' 2>/dev/null)
echo "Testing http://${SVC_IP}:${SVC_PORT}/mcp ..."
kubectl run -n mcps test-gob2 --rm -i --restart=Never --image=curlimages/curl:8.12.0 --timeout=30s -- \
  curl -s --connect-timeout 5 -X POST "http://${SVC_IP}:${SVC_PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>&1 | head -5

echo ""
echo "DONE"
