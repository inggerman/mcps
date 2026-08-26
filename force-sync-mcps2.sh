#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. LOGIN TO ARGOCD ==="
ARGOCD_POD=$(kubectl get pod -n argocd -l app.kubernetes.io/component=server -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
kubectl exec -n argocd $ARGOCD_POD -- argocd account bcrypt-password 2>&1 | head -3
echo ""

echo "=== 2. TRY SYNC WITH TOKEN ==="
# First login
TOKEN=$(kubectl exec -n argocd $ARGOCD_POD -- sh -c 'ARGOCD_SERVER=localhost:8080 argocd account generate-token --account admin 2>/dev/null' 2>&1)
echo "  Token: ${TOKEN:0:20}..."
echo ""

echo "=== 3. SYNC VIA ARGOCD API ==="
kubectl exec -n argocd $ARGOCD_POD -- sh -c "argocd app sync mcp-services --server localhost:8080 --plaintext --auth-token $TOKEN" 2>&1 | head -30
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

echo "DONE"
