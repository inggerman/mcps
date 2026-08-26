#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ARGO WORKFLOWS PODS ==="
kubectl get pods -n argo-workflows 2>&1
echo ""

echo "=== 2. EVENTS ==="
kubectl get events -n argo-workflows --sort-by=.lastTimestamp 2>&1 | tail -15
echo ""

echo "=== 3. ROLLOUT STATUS ==="
kubectl rollout status deploy -n argo-workflows argo-workflows-server --timeout=30s 2>&1
echo ""

echo "=== 4. TEST ==="
curl -sI http://workflows.mrrobot.fs/ 2>&1 | head -5
echo ""

echo "DONE"
