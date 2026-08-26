#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. DELETE APP ==="
kubectl delete application mcp-services -n argocd 2>&1
echo ""

echo "=== 2. WAIT 5s ==="
sleep 5
echo ""

echo "=== 3. RECREATE APP ==="
cat <<'EOF' | kubectl apply -f - 2>&1
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: mcp-services
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "3"
  labels:
    app.kubernetes.io/name: mcp-services
    app.kubernetes.io/part-of: ghl-platform
spec:
  project: services
  destination:
    server: https://kubernetes.default.svc
    namespace: mcps
  source:
    repoURL: http://gitea-http-fixed.gitea.svc.cluster.local:3000/ghl/platform.git
    targetRevision: main
    path: gitops/apps/mcp-services
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF
echo ""

echo "=== 4. WAIT 90s ==="
sleep 90
echo ""

echo "=== 5. STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 6. OPERATION STATE ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.operationState}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'  phase: {data.get(\"phase\")}')
msg = data.get('message','')
print(f'  message: {msg[:300]}')
" 2>&1
echo ""

echo "=== 7. ALL APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 8. MCP PODS ==="
kubectl get pods -n mcps 2>&1 | head -15
echo ""

echo "=== 9. MCP SERVICES ==="
kubectl get svc -n mcps 2>&1 | head -10
echo ""

echo "DONE"
