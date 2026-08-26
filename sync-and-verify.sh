#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. FORCE ARGO CD REFRESH ==="
kubectl patch application agents-platform-prod -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== 2. WAIT 30s ==="
sleep 30
echo ""

echo "=== 3. CHECK ARGO CD STATUS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 4. CHECK PODS ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 5. DELETE OLD PODS TO FORCE PULL NEW IMAGES ==="
kubectl delete pods -n agents-platform --all 2>&1
echo ""

echo "=== 6. WAIT 30s ==="
sleep 30
echo ""

echo "=== 7. CHECK PODS AGAIN ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== 8. CHECK CRASH LOGS IF ANY ==="
for pod in $(kubectl get pods -n agents-platform -o jsonpath='{.items[?(@.status.phase!="Running")].metadata.name}' 2>/dev/null); do
  echo "--- Pod: $pod ---"
  kubectl logs -n agents-platform $pod --tail=10 2>&1
  echo ""
done

echo "DONE"
