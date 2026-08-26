#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== NODES ==="
kubectl get nodes 2>&1
echo ""

echo "=== NOT RUNNING PODS ==="
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "=== PODS WITH RESTARTS ==="
kubectl get pods -A 2>&1 | awk 'NR>1 && $5+0 > 0 {print $1, $2, $3, $5}'
echo ""

echo "=== K3S SERVICE ==="
systemctl status k3s 2>&1 | head -15
echo ""

echo "=== CRITICAL NAMESPACES ==="
for ns in argocd gitea mcps n8n kong harbor databases; do
  echo "--- $ns ---"
  kubectl get pods -n $ns 2>&1 | head -10
  echo ""
done

echo "DONE"
