#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK API LOGS ==="
kubectl logs -n agents-platform agents-platform-api-7f5d68c5f5-9xdbh --tail=15 2>&1
echo ""

echo "=== 2. CHECK WORKER LOGS ==="
kubectl logs -n agents-platform agents-platform-worker-778846697b-kj2d2 --tail=15 2>&1
echo ""

echo "=== 3. CHECK DAEMON LOGS ==="
kubectl logs -n agents-platform agents-platform-daemon-69b776f8cb-jhzbg --tail=15 2>&1
echo ""

echo "=== 4. FORCE ROLLOOUT RESTART ==="
kubectl rollout restart deployment/agents-platform-api -n agents-platform 2>&1
kubectl rollout restart deployment/agents-platform-worker -n agents-platform 2>&1
kubectl rollout restart deployment/agents-platform-daemon -n agents-platform 2>&1
echo ""

echo "=== 5. WAIT 30s ==="
sleep 30
echo ""

echo "=== 6. CHECK PODS ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 7. CHECK NEW POD LOGS ==="
for pod in $(kubectl get pods -n agents-platform -l app=agents-platform-api -o jsonpath='{.items[?(@.status.phase!="Running")].metadata.name}' 2>/dev/null); do
  echo "--- $pod ---"
  kubectl logs -n agents-platform $pod --tail=15 2>&1
done
echo ""

echo "DONE"
