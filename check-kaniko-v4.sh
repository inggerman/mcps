#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK POD STATUS ==="
kubectl get pods -n harbor -l job-name=build-agents-platform 2>&1
echo ""

echo "=== 2. CHECK JOB STATUS ==="
kubectl get job build-agents-platform -n harbor 2>&1
echo ""

echo "=== 3. CHECK ALL LOGS ==="
POD=$(kubectl get pods -n harbor -l job-name=build-agents-platform -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
echo "Pod: $POD"
echo ""

echo "=== INIT CONTAINER ==="
kubectl logs -n harbor $POD -c clone 2>&1
echo ""

echo "=== KANIKO-API ==="
kubectl logs -n harbor $POD -c kaniko-api --tail=30 2>&1
echo ""

echo "=== KANIKO-WORKER ==="
kubectl logs -n harbor $POD -c kaniko-worker --tail=30 2>&1
echo ""

echo "DONE"
