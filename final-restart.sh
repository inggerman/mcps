#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ROLLOUT RESTART ALL DEPLOYMENTS ==="
kubectl rollout restart deployment/agents-platform-api -n agents-platform 2>&1
kubectl rollout restart deployment/agents-platform-worker -n agents-platform 2>&1
kubectl rollout restart deployment/agents-platform-daemon -n agents-platform 2>&1
kubectl rollout restart deployment/mcp-web-search -n agents-platform 2>&1
kubectl rollout restart deployment/mcp-source-validator -n agents-platform 2>&1
echo ""

echo "=== 2. FORCE ARGO CD REFRESH ==="
kubectl patch application agents-platform-prod -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== 3. WAIT 45s ==="
sleep 45
echo ""

echo "=== 4. CHECK PODS ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 5. CHECK CRASH LOGS ==="
for pod in $(kubectl get pods -n agents-platform -o jsonpath='{.items[?(@.status.phase!="Running")].metadata.name}' 2>/dev/null); do
  echo "--- $pod ---"
  kubectl logs -n agents-platform $pod --tail=10 2>&1
  echo ""
done

echo "=== 6. ARGO CD STATUS ==="
kubectl get applications -A 2>&1
echo ""

echo "DONE"
