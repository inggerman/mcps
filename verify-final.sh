#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== Re-enable Argo CD self-heal ==="
kubectl patch application agents-platform-prod -n argocd --type=merge -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}' 2>&1
echo ""

echo "=== Force refresh ==="
kubectl patch application agents-platform-prod -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== Wait 60s ==="
sleep 60
echo ""

echo "=== Check pods ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== Worker logs ==="
for pod in $(kubectl get pods -n agents-platform -l app.kubernetes.io/name=agents-platform-worker -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
  echo "--- $pod ---"
  kubectl logs -n agents-platform $pod --tail=5 2>&1
  echo ""
done

echo "=== Argo CD status ==="
kubectl get applications -A 2>&1
echo ""

echo "DONE"
