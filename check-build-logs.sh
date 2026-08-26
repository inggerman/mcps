#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. POD STATUS ==="
kubectl get pods -n agents-platform -l job-name=build-agents-platform 2>&1
echo ""

echo "=== 2. POD LOGS ==="
kubectl logs -n agents-platform build-agents-platform-thq2d 2>&1 | tail -30
echo ""

echo "=== 3. POD EVENTS ==="
kubectl describe pod -n agents-platform build-agents-platform-thq2d 2>&1 | grep -A10 "Events:" | head -15
echo ""

echo "DONE"
