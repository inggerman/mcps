#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK HARBOR PULL SECRET IN MCPS ==="
kubectl get secret harbor-pull-secret -n mcps 2>&1
echo ""

echo "=== 2. CHECK EXISTING PVCS IN MCPS ==="
kubectl get pvc -n mcps 2>&1
echo ""

echo "=== 3. CHECK EXISTING SERVICE ACCOUNTS ==="
kubectl get sa -n mcps 2>&1
echo ""

echo "=== 4. CHECK EXISTING CONFIGMAPS ==="
kubectl get cm -n mcps 2>&1
echo ""

echo "=== 5. CHECK EXISTING INGRESSES ==="
kubectl get ingress -n mcps 2>&1 | head -10
echo ""

echo "=== 6. CHECK APP PROJECT ==="
kubectl get appproject services -n argocd -o yaml 2>&1 | grep -A5 "clusterResourceBlack\|namespaceResourceBlack\|roles"
echo ""

echo "=== 7. CHECK SYNC OPERATION ERROR DETAIL ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.operationState}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  phase: {data.get(\"phase\")}')
print(f'  message: {data.get(\"message\")}')
print(f'  startedAt: {data.get(\"startedAt\")}')
" 2>&1
echo ""

echo "=== 8. CHECK SYNC RESULT ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.operationState.syncResult.resources}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data[:5]:
    print(f'  {r.get(\"kind\")}/{r.get(\"name\")}: status={r.get(\"status\")} message={r.get(\"message\",\"\")}')
" 2>&1
echo ""

echo "DONE"
