#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. FORCE SYNC VIA API ==="
# Get Argo CD server pod name
ARGOCD_POD=$(kubectl get pod -n argocd -l app.kubernetes.io/component=server -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
echo "  Pod: $ARGOCD_POD"

# Use argocd CLI inside the pod
kubectl exec -n argocd $ARGOCD_POD -- argocd app sync mcp-services --server localhost:8080 --plaintext --username admin --password "UUaTUAE6RhTE3-3G" 2>&1 | head -20
echo ""

echo "=== 2. WAIT 30s ==="
sleep 30
echo ""

echo "=== 3. CHECK STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 4. ALL APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 5. MCP PODS ==="
kubectl get pods -n mcps 2>&1 | head -10
echo ""

echo "DONE"
