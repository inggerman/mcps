#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK POD STATUS ==="
kubectl get pods -n argocd -l job-name=build-agents-platform 2>&1
echo ""

echo "=== 2. CHECK RUNNING POD LOGS ==="
POD=$(kubectl get pods -n argocd -l job-name=build-agents-platform --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -z "$POD" ]; then
  POD=$(kubectl get pods -n argocd -l job-name=build-agents-platform -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
fi
echo "Pod: $POD"
echo ""

echo "=== 3. KANIKO-API LOGS ==="
kubectl logs -n argocd $POD -c kaniko-api --tail=20 2>&1
echo ""

echo "=== 4. KANIKO-WORKER LOGS ==="
kubectl logs -n argocd $POD -c kaniko-worker --tail=20 2>&1
echo ""

echo "=== 5. JOB STATUS ==="
kubectl get job build-agents-platform -n argocd 2>&1
echo ""

echo "DONE"
