#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. WORKFLOW STATUS ==="
kubectl get wf -n argo-workflows 2>&1
echo ""

echo "=== 2. PODS ==="
kubectl get pods -n argo-workflows 2>&1
echo ""

echo "=== 3. MAIN CONTAINER LOGS ==="
kubectl logs hello-world -n argo-workflows -c main 2>&1
echo ""

echo "=== 4. EVENTS ==="
kubectl get events -n argo-workflows --sort-by=.lastTimestamp 2>&1 | tail -10
echo ""

echo "DONE"
