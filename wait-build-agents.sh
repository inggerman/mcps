#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== WAITING FOR JOB TO COMPLETE (up to 10min) ==="
kubectl wait job/build-agents-platform -n agents-platform --for=condition=complete --timeout=600s 2>&1 &
WAIT_PID=$!

# Poll every 30s
for i in $(seq 1 20); do
  sleep 30
  STATUS=$(kubectl get job build-agents-platform -n agents-platform -o jsonpath='{.status.conditions[0].type}' 2>/dev/null)
  echo "  Check $i: $STATUS"
  if [ "$STATUS" = "Complete" ] || [ "$STATUS" = "Failed" ]; then
    break
  fi
  # Show latest log line
  kubectl logs -n agents-platform -l job-name=build-agents-platform --tail=3 2>&1
  echo ""
done

echo ""
echo "=== JOB STATUS ==="
kubectl get job build-agents-platform -n agents-platform 2>&1
echo ""

echo "=== FULL LOGS ==="
kubectl logs -n agents-platform -l job-name=build-agents-platform --tail=50 2>&1
echo ""

echo "=== VERIFY IMAGES IN HARBOR ==="
# Check via crane
POD=$(kubectl get pods -n agents-platform -l job-name=build-agents-platform -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$POD" ]; then
  kubectl exec -n agents-platform $POD -- crane ls harbor.mrrobot.fs/ghl/agents-platform-api 2>&1 || echo "  Could not verify (pod may be terminated)"
  kubectl exec -n agents-platform $POD -- crane ls harbor.mrrobot.fs/ghl/agents-platform-worker 2>&1 || echo "  Could not verify (pod may be terminated)"
fi
echo ""

echo "=== RESTART ARGO CD SYNC ==="
kubectl patch application agents-platform-prod -n argocd --type=merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}' 2>&1
echo ""

echo "DONE"
