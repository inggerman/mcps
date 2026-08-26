#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== WORKER PODS ==="
kubectl get pods -n agents-platform -l app.kubernetes.io/name=agents-platform-worker 2>&1
echo ""

echo "=== WORKER (running) LOGS ==="
kubectl logs -n agents-platform agents-platform-worker-5cc44b648d-fpnxl --tail=30 2>&1
echo ""

echo "=== DAEMON LOGS ==="
kubectl logs -n agents-platform agents-platform-daemon-78cdd649b4-cnxds --tail=15 2>&1
echo ""

echo "=== DAEMON ENV ==="
kubectl exec -n agents-platform agents-platform-daemon-78cdd649b4-cnxds -- env 2>&1 | grep -E "REDIS|RABBIT|IMAP"
echo ""

echo "=== WORKER ENV ==="
kubectl exec -n agents-platform agents-platform-worker-5cc44b648d-fpnxl -- env 2>&1 | grep -E "REDIS|RABBIT"
echo ""

echo "DONE"
