#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== WORKER PODS ==="
kubectl get pods -n agents-platform -l app.kubernetes.io/name=agents-platform-worker 2>&1
echo ""

echo "=== WORKER LOGS (pod 1) ==="
kubectl logs -n agents-platform agents-platform-worker-76df9545b4-s4vxg --tail=30 2>&1
echo ""

echo "=== WORKER LOGS (pod 2) ==="
kubectl logs -n agents-platform agents-platform-worker-76df9545b4-tcv4m --tail=30 2>&1
echo ""

echo "=== DESCRIBE WORKER POD ==="
kubectl describe pod -n agents-platform agents-platform-worker-76df9545b4-s4vxg 2>&1 | tail -30
echo ""

echo "DONE"
