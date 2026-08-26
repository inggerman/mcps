#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. FORCE REFRESH ==="
kubectl patch application mcp-services -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== 2. WAIT 30s ==="
sleep 30
echo ""

echo "=== 3. STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 4. OPERATION STATE ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.operationState}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  phase: {data.get(\"phase\")}')
print(f'  message: {data.get(\"message\",\"\")}')
" 2>&1
echo ""

echo "=== 5. ALL APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "DONE"
