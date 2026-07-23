#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. IMPORT IMAGE TO K3S ==="
sudo k3s ctr images import /mnt/c/Users/German/mcp-gob-mexico.tar 2>&1 | tail -3

echo ""
echo "=== 2. RESTART DEPLOYMENT ==="
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
kubectl logs -n mcps deploy/mcp-gob-mexico --tail=15 2>&1

echo ""
echo "=== 6. TEST PROTOCOL ==="
SVC_IP=$(kubectl get svc -n mcps mcp-gob-mexico -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
SVC_PORT=$(kubectl get svc -n mcps mcp-gob-mexico -o jsonpath='{.spec.ports[0].port}' 2>/dev/null)
echo "Testing http://${SVC_IP}:${SVC_PORT}/mcp ..."
kubectl run -n mcps test-gob3 --rm -i --restart=Never --image=curlimages/curl:8.12.0 --timeout=30s -- \
  curl -s --connect-timeout 5 -X POST "http://${SVC_IP}:${SVC_PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>&1 | head -5

echo ""
echo "=== 7. ALL PODS STATUS ==="
kubectl get pods -n mcps --no-headers 2>/dev/null | awk '{print $1, $3, $4}'

echo "DONE"
