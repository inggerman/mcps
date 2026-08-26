#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. K3S SERVICE ==="
systemctl is-active k3s 2>&1
echo ""

echo "=== 2. NODES ==="
kubectl get nodes 2>&1
echo ""

echo "=== 3. NOT RUNNING PODS ==="
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "=== 4. TOTAL PODS ==="
TOTAL=$(kubectl get pods -A --no-headers 2>/dev/null | wc -l)
RUNNING=$(kubectl get pods -A --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
echo "  Total: $TOTAL  Running: $RUNNING"
echo ""

echo "=== 5. CRITICAL NAMESPACES ==="
for NS in harbor gitea databases argocd n8n mcps kong minio rabbitmq; do
  echo "--- $NS ---"
  kubectl get pods -n $NS 2>&1
  echo ""
done

echo "=== 6. TAILSCALE ==="
tailscale status 2>&1 | head -5
echo ""

echo "=== 7. KONG LB ==="
kubectl get svc kong-kong-proxy -n kong 2>&1
echo ""

echo "DONE"
