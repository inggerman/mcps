#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PATCH APPPROJECT TO ALLOW ClusterRoleBinding ==="
kubectl patch appproject services -n argocd --type=merge -p '{"spec":{"clusterResourceWhitelist":[{"group":"rbac.authorization.k8s.io","kind":"ClusterRoleBinding"}]}}' 2>&1
echo ""

echo "=== 2. ALSO CREATE HARBOR PULL SECRET IN MCPS ==="
kubectl get secret harbor-pull-secret -n demo-service-qa -o yaml 2>/dev/null | sed 's/namespace: demo-service-qa/namespace: mcps/' | kubectl apply -f - 2>&1
echo ""

echo "=== 3. FORCE REFRESH ==="
kubectl patch application mcp-services -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== 4. WAIT 30s ==="
sleep 30
echo ""

echo "=== 5. CHECK STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 6. ALL APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 7. MCP PODS ==="
kubectl get pods -n mcps 2>&1 | head -5
echo ""

echo "DONE"
