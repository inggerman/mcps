#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK SYNC RESULT FOR agents-platform-prod ==="
kubectl get application agents-platform-prod -n argocd -o jsonpath='{.status.operationState.syncResult.resources}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data[:10]:
    print(f'  {r.get(\"kind\")}/{r.get(\"name\")}: status={r.get(\"status\")} message={r.get(\"message\",\"\")}')
" 2>&1
echo ""

echo "=== 2. CHECK SYNC RESULT FOR agents-platform-qa ==="
kubectl get application agents-platform-qa -n argocd -o jsonpath='{.status.operationState.syncResult.resources}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data[:10]:
    print(f'  {r.get(\"kind\")}/{r.get(\"name\")}: status={r.get(\"status\")} message={r.get(\"message\",\"\")}')
" 2>&1
echo ""

echo "=== 3. CHECK APP PROJECT ==="
kubectl get appproject services -n argocd -o yaml 2>&1 | grep -A5 "clusterResourceBlack\|clusterResourceWhite\|namespaceResourceBlack"
echo ""

echo "DONE"
