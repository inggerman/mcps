#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. WAIT 90s MORE ==="
sleep 90
echo ""

echo "=== 2. STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 3. OPERATION STATE ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.operationState}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  phase: {data.get(\"phase\")}')
msg = data.get('message','')
print(f'  message: {msg[:200]}')
" 2>&1
echo ""

echo "=== 4. ALL APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 5. MCP PODS ==="
kubectl get pods -n mcps 2>&1 | head -10
echo ""

echo "DONE"
