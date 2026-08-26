#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. DELETE ALL MCP DEPLOYMENTS (Argo CD will recreate them) ==="
kubectl delete deploy -n mcps --all 2>&1
echo ""

echo "=== 2. DELETE OLD INGRESSES ==="
kubectl delete ingress -n mcps --all 2>&1
echo ""

echo "=== 3. DELETE OLD SERVICES (Argo CD will recreate) ==="
kubectl delete svc -n mcps --all 2>&1
echo ""

echo "=== 4. FORCE REFRESH ==="
kubectl patch application mcp-services -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== 5. WAIT 60s ==="
sleep 60
echo ""

echo "=== 6. STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 7. ALL APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 8. MCP PODS ==="
kubectl get pods -n mcps 2>&1 | head -15
echo ""

echo "DONE"
