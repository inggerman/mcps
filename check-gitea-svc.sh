#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. GITEA SVC ==="
kubectl get svc -n gitea 2>&1
echo ""

echo "=== 2. GITEA HTTP SVC DETAILS ==="
kubectl get svc -n gitea -o wide 2>&1
echo ""

echo "=== 3. CHECK IF gitea-http-fixed EXISTS ==="
kubectl get svc gitea-http-fixed -n gitea 2>&1
echo ""

echo "=== 4. CHECK N8N APP REPO URL (working) ==="
kubectl get application n8n -n argocd -o jsonpath='{.spec.source.repoURL}' 2>&1
echo ""

echo "=== 5. CHECK MCP APP REPO URL ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.spec.source.repoURL}' 2>&1
echo ""

echo "DONE"
