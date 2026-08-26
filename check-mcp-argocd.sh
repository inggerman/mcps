#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ALL ARGOCD APPLICATIONS (detailed) ==="
kubectl get applications -A -o yaml 2>&1 | grep -E "name:|path:|namespace:|repoURL:" | head -30
echo ""

echo "=== 2. APPLICATIONSET STATUS ==="
kubectl get applicationset user-services -n argocd -o yaml 2>&1 | head -50
echo ""

echo "=== 3. CHECK IF mcp-services APP EXISTS IN ARGOCD ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 4. CURRENT MCP NAMESPACE ==="
kubectl get ns mcps 2>&1
kubectl get ns mcp-services 2>&1
echo ""

echo "=== 5. CHECK GIT REPO ==="
kubectl get applicationset user-services -n argocd -o jsonpath='{.spec.generators[0].git.repoURL}' 2>&1
echo ""
kubectl get applicationset user-services -n argocd -o jsonpath='{.spec.generators[0].git.directories}' 2>&1
echo ""

echo "DONE"
