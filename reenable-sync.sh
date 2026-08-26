#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== Re-enable Argo CD auto-sync ==="
kubectl patch application agents-platform-prod -n argocd --type=merge -p '{"spec":{"syncPolicy":{"automated":{"prune":true,"selfHeal":true}}}}' 2>&1
echo ""

echo "=== Force refresh ==="
kubectl patch application agents-platform-prod -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "=== Wait 30s ==="
sleep 30
echo ""

echo "=== Check pods ==="
kubectl get pods -n agents-platform 2>&1
echo ""

echo "=== Argo CD status ==="
kubectl get applications -A 2>&1
echo ""

echo "DONE"
