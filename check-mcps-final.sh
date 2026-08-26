#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. DEPLOYMENTS ==="
kubectl get deploy -n mcps 2>&1
echo ""

echo "=== 2. PODS ==="
kubectl get pods -n mcps 2>&1
echo ""

echo "=== 3. EVENTS ==="
kubectl get events -n mcps --sort-by=.lastTimestamp 2>&1 | tail -15
echo ""

echo "DONE"
