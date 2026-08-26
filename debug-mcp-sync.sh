#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ARGOCD APPLICATION CONTROLLER LOGS ==="
kubectl logs -n argocd argocd-application-controller-0 --tail=30 2>&1 | grep -i "mcp\|error\|fail" | head -15
echo ""

echo "=== 2. REPO SERVER LOGS ==="
kubectl logs -n argocd -l app.kubernetes.io/component=repo-server --tail=20 2>&1 | grep -i "mcp\|error\|fail" | head -10
echo ""

echo "=== 3. CHECK IF ARGOCD CAN RENDER THE CHART ==="
kubectl exec -n argocd $(kubectl get pod -n argocd -l app.kubernetes.io/component=repo-server -o jsonpath='{.items[0].metadata.name}') -- helm template /tmp/_argocd-repo/gitops/apps/mcp-services 2>&1 | head -20
echo ""

echo "=== 4. CHECK APP OPERATION STATE ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.operationState}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  phase: {data.get(\"phase\")}')
print(f'  message: {data.get(\"message\")}')
" 2>&1
echo ""

echo "=== 5. CHECK CONDITIONS ==="
kubectl get application mcp-services -n argocd -o yaml 2>&1 | grep -A5 "conditions:" | head -15
echo ""

echo "DONE"
