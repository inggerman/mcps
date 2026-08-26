#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. APPLY MCP-SERVICES APPLICATION TO ARGOCD ==="
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

echo "=== 2. CHECK APPLICATION ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "=== 3. WAIT 10s FOR SYNC ==="
sleep 10
echo ""

echo "=== 4. CHECK STATUS ==="
kubectl get application mcp-services -n argocd -o jsonpath='{.status.sync.status}{" "}{.status.health.status}' 2>&1
echo ""
echo ""

echo "=== 5. ALL ARGOCD APPS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 6. MCP PODS STILL RUNNING ==="
kubectl get pods -n mcps 2>&1 | head -10
echo ""

echo "DONE"
