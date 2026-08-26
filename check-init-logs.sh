#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== INIT CONTAINER LOGS ==="
POD=$(kubectl get pods -n gitea-runner -l job-name=build-agents-platform -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
echo "Pod: $POD"
kubectl logs -n gitea-runner $POD -c clone 2>&1
echo ""

echo "DONE"
