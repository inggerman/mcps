#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK APP CONDITIONS ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.conditions}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for c in data:
    print(f'  {c.get(\"type\")}: {c.get(\"message\")}')
" 2>&1
echo ""

echo "=== 2. CHECK SYNC STATUS DETAIL ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.sync}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  status: {data.get(\"status\")}')
print(f'  revision: {data.get(\"revision\")}')
revisions = data.get('revisions', [])
print(f'  revisions: {revisions}')
" 2>&1
echo ""

echo "=== 3. CHECK IF GITEA REPO HAS THE CHANGES ==="
# Check if the Gitea repo has the mcp-services directory
kubectl exec -n argocd deploy/argocd-repo-server -- ls -la /tmp/ 2>&1 | head -5
echo ""

echo "=== 4. TRY MANUAL SYNC ==="
kubectl exec -n argocd deploy/argocd-server -- argocd app sync mcp-services --server localhost:8080 --plaintext 2>&1 || echo "  Manual sync via CLI failed, trying API..."
echo ""

echo "=== 5. FORCE REFRESH ==="
kubectl patch application mcp-services -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== 6. WAIT 15s ==="
sleep 15
echo ""

echo "=== 7. CHECK STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 8. CONDITIONS ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.conditions}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for c in data:
    print(f'  {c.get(\"type\")}: {c.get(\"message\")}')
" 2>&1
echo ""

echo "DONE"
