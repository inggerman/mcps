#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. WAIT 30s ==="
sleep 30
echo ""

echo "=== 2. ALL APPLICATIONS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 3. agents-platform-qa STATUS ==="
kubectl get application agents-platform-qa -n argocd -o jsonpath='{.status.operationState}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  phase: {data.get(\"phase\")}')
print(f'  message: {data.get(\"message\",\"\")}')
" 2>&1
echo ""

echo "=== 4. agents-platform-prod STATUS ==="
kubectl get application agents-platform-prod -n argocd -o jsonpath='{.status.operationState}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  phase: {data.get(\"phase\")}')
print(f'  message: {data.get(\"message\",\"\")}')
" 2>&1
echo ""

echo "=== 5. CHECK NAMESPACES ==="
kubectl get ns agents-platform 2>&1
kubectl get ns agents-platform-qa 2>&1
echo ""

echo "=== 6. CHECK PODS ==="
kubectl get pods -n agents-platform 2>&1
kubectl get pods -n agents-platform-qa 2>&1
echo ""

echo "DONE"
