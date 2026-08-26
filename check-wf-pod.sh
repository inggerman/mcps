#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. DESCRIBE POD ==="
kubectl describe pod hello-world -n argo-workflows 2>&1 | tail -40
echo ""

echo "=== 2. EVENTS ==="
kubectl get events -n argo-workflows --sort-by=.lastTimestamp 2>&1 | tail -15
echo ""

echo "=== 3. POD LOGS ==="
kubectl logs hello-world -n argo-workflows --all-containers 2>&1 | tail -20
echo ""

echo "=== 4. INIT CONTAINER LOGS ==="
kubectl logs hello-world -n argo-workflows -c init 2>&1 | tail -10
echo ""

echo "DONE"
