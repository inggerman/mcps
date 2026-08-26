#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. LOGIN VIA API ==="
TOKEN=$(curl -s -k -X POST http://localhost:38080/api/v1/session -d '{"username":"admin","password":"UUaTUAE6RhTE3-3G"}' -H "Content-Type: application/json" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)

# Port forward to argocd server
kubectl port-forward -n argocd svc/argocd-server 38080:80 &
PF_PID=$!
sleep 3

TOKEN=$(curl -s -X POST http://localhost:38080/api/v1/session -d '{"username":"admin","password":"UUaTUAE6RhTE3-3G"}' -H "Content-Type: application/json" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('token',''))" 2>/dev/null)
echo "  Token: ${TOKEN:0:20}..."
echo ""

echo "=== 2. FORCE SYNC VIA API ==="
curl -s -X POST http://localhost:38080/api/v1/applications/mcp-services/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  status: {data.get(\"status\",{}).get(\"sync\",{}).get(\"status\",\"unknown\")}')
print(f'  operation: {data.get(\"operation\",{}).get(\"sync\",{}).get(\"revision\",\"unknown\")}')
" 2>&1
echo ""

echo "=== 3. WAIT 30s ==="
sleep 30
echo ""

echo "=== 4. CHECK STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 5. ALL APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 6. MCP PODS ==="
kubectl get pods -n mcps 2>&1 | head -5
echo ""

# Kill port-forward
kill $PF_PID 2>/dev/null

echo "DONE"
