#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. WAIT 30s ==="
sleep 30
echo ""

echo "=== 2. PVC STATUS ==="
kubectl get pvc -n mcps 2>&1
echo ""

echo "=== 3. MCP PODS ==="
kubectl get pods -n mcps 2>&1
echo ""

echo "=== 4. ARGOCD STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 5. ALL APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "DONE"
