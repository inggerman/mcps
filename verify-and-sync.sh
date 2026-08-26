#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. VERIFY IMAGES IN HARBOR ==="
# Use the copy-python-base pod which has crane
POD=$(kubectl get pods -n gitea-runner -l job-name=copy-python-base -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$POD" ]; then
  echo "Using pod $POD to verify images"
  kubectl exec -n gitea-runner $POD -- crane ls harbor-registry.harbor.svc.cluster.local:5000/ghl/agents-platform-api --insecure 2>&1
  kubectl exec -n gitea-runner $POD -- crane ls harbor-registry.harbor.svc.cluster.local:5000/ghl/agents-platform-worker --insecure 2>&1
else
  echo "No crane pod available, checking via API"
  curl -s "http://harbor-registry.harbor.svc.cluster.local:5000/v2/ghl/agents-platform-api/tags/list" 2>&1
  curl -s "http://harbor-registry.harbor.svc.cluster.local:5000/v2/ghl/agents-platform-worker/tags/list" 2>&1
fi
echo ""

echo "=== 2. CHECK CURRENT DEPLOYMENT IMAGES ==="
kubectl get deployments -n agents-platform -o jsonpath='{range .items[*]}{.metadata.name}{"  "}{.spec.template.spec.containers[0].image}{"\n"}{end}' 2>&1
echo ""

echo "=== 3. FORCE ARGO CD REFRESH ==="
kubectl patch application agents-platform-prod -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== 4. WAIT 30s ==="
sleep 30
echo ""

echo "=== 5. CHECK ARGO CD STATUS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 6. CHECK PODS ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 7. CHECK POD EVENTS (if any ImagePullBackOff) ==="
for pod in $(kubectl get pods -n agents-platform -o jsonpath='{.items[?(@.status.phase!="Running")].metadata.name}' 2>/dev/null); do
  echo "Pod: $pod"
  kubectl describe pod -n agents-platform $pod 2>&1 | grep -A5 "Events:" | head -10
  echo ""
done

echo "DONE"
