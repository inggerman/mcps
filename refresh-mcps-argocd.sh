#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. FORCE HARD REFRESH ==="
kubectl patch application mcp-services -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== 2. WAIT 20s ==="
sleep 20
echo ""

echo "=== 3. CHECK STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 4. ALL APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 5. MCP PODS ==="
kubectl get pods -n mcps 2>&1 | head -10
echo ""

echo "=== 6. CHECK RESOURCES DIFF ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.resources}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data:
    print(f'  {r.get(\"kind\")}/{r.get(\"name\")}: sync={r.get(\"status\")} health={r.get(\"health\",{}).get(\"status\")}')
" 2>&1
echo ""

echo "DONE"
