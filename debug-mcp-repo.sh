#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK REPOSITORIES IN ARGOCD ==="
kubectl get repositories -A 2>&1
echo ""

echo "=== 2. CHECK APP SOURCE ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.spec.source}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data, indent=2))
" 2>&1
echo ""

echo "=== 3. CHECK WHAT REPOS ARGOCD KNOWS ==="
kubectl get appproject services -n argocd -o yaml 2>&1 | grep -A10 "sourceRepos"
echo ""

echo "=== 4. CHECK IF GITEA REPO IS ACCESSIBLE ==="
kubectl exec -n argocd $(kubectl get pod -n argocd -l app.kubernetes.io/component=repo-server -o jsonpath='{.items[0].metadata.name}') -- ls /tmp/_argocd-repo/ 2>&1
echo ""

echo "=== 5. CHECK HELM CHART FILES IN REPO ==="
kubectl exec -n argocd $(kubectl get pod -n argocd -l app.kubernetes.io/component=repo-server -o jsonpath='{.items[0].metadata.name}') -- find /tmp/_argocd-repo -name "Chart.yaml" 2>&1 | head -10
echo ""

echo "=== 6. CHECK N8N APP SOURCE (working one) ==="
kubectl get application n8n -n argocd -o jsonpath='{.spec.source}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data, indent=2))
" 2>&1
echo ""

echo "DONE"
