#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. DELETE AND RECREATE APP WITH FORCE ==="
kubectl delete application mcp-services -n argocd 2>&1
echo ""

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
      - Force=true
EOF
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
kubectl get pods -n mcps 2>&1 | head -10
echo ""

echo "DONE"
