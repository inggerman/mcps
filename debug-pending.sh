#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. CHECK require-env-label POLICY DETAILS ==="
k3s kubectl get cpol require-env-label -o yaml 2>&1 | head -60
echo ""

echo "=== 2. CHECK EVENTS FOR PENDING PODS ==="
k3s kubectl get events -n mcps --sort-by=.lastTimestamp 2>&1 | tail -30
echo ""

echo "=== 3. DESCRIBE A PENDING POD ==="
PENDING_POD=$(k3s kubectl get pods -n mcps --field-selector=status.phase=Pending 2>/dev/null | head -2 | tail -1 | awk '{print $1}')
echo "Pod: $PENDING_POD"
k3s kubectl describe pod $PENDING_POD -n mcps 2>&1 | tail -25
echo ""

echo "DONE"
