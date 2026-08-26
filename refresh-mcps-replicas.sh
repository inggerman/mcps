#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. FORCE REFRESH ==="
kubectl patch application mcp-services -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== 2. WAIT 60s ==="
sleep 60
echo ""

echo "=== 3. STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 4. ALL APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 5. MCP PODS ==="
kubectl get pods -n mcps 2>&1 | head -15
echo ""

echo "=== 6. MCP DEPLOYMENTS ==="
kubectl get deploy -n mcps 2>&1
echo ""

echo "DONE"
