#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. REBUILD MCP-GOB-MEXICO IMAGE ==="
cd /mnt/c/Users/German/Documents/engineering/mcps
docker build --no-cache -t harbor.mrrobot.fs/ghl/mcp-gob-mexico:latest -f mcp-gob-mexico/Dockerfile . 2>&1 | tail -10

echo ""
echo "=== 2. SAVE AND IMPORT TO K3S ==="
docker save harbor.mrrobot.fs/ghl/mcp-gob-mexico:latest -o /tmp/mcp-gob-mexico.tar
sudo k3s ctr images import /tmp/mcp-gob-mexico.tar 2>&1 | tail -3

echo ""
echo "=== 3. RESTART DEPLOYMENT ==="
kubectl rollout restart deploy/mcp-gob-mexico -n mcps
sleep 10
kubectl get pod -n mcps -l app.kubernetes.io/name=mcp-gob-mexico 2>&1

echo ""
echo "=== 4. WAIT FOR ROLLOUT ==="
kubectl rollout status deploy/mcp-gob-mexico -n mcps --timeout=120s 2>&1

echo ""
echo "=== 5. CHECK LOGS ==="
kubectl logs -n mcps deploy/mcp-gob-mexico --tail=15 2>&1

echo ""
echo "=== 6. TEST MCP PROTOCOL ==="
SVC_IP=$(kubectl get svc -n mcps mcp-gob-mexico -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
SVC_PORT=$(kubectl get svc -n mcps mcp-gob-mexico -o jsonpath='{.spec.ports[0].port}' 2>/dev/null)
echo "Testing http://${SVC_IP}:${SVC_PORT}/mcp ..."
kubectl run -n mcps test-gob --rm -i --restart=Never --image=curlimages/curl:8.12.0 --timeout=30s -- \
  curl -s --connect-timeout 5 -X POST "http://${SVC_IP}:${SVC_PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>&1 | head -5

echo ""
echo "DONE"
