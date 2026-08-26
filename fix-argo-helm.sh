#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. HELM UPGRADE WITH PROPER AUTH CONFIG ==="
helm upgrade argo-workflows argo/argo-workflows -n argo-workflows \
  --reuse-values \
  --set server.deploymentAnnotations."konghq\.com/plugins"="" \
  --set server.extraArgs='{--auth-mode=server}' \
  --set server.secure=false 2>&1
echo ""

echo "=== 2. WAIT FOR ROLLOUT ==="
kubectl rollout status deploy -n argo-workflows argo-workflows-server --timeout=90s 2>&1
echo ""

echo "=== 3. PODS ==="
kubectl get pods -n argo-workflows 2>&1
echo ""

echo "=== 4. LOGS ==="
kubectl logs -n argo-workflows -l app.kubernetes.io/component=server --tail=15 2>&1
echo ""

echo "=== 5. TEST API ==="
curl -s http://workflows.mrrobot.fs/api/v1/info 2>&1
echo ""

echo "DONE"
