#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. POD LABELS ==="
kubectl get pods -n argo-workflows --show-labels 2>&1
echo ""

echo "=== 2. NEW POD LOGS ==="
NEW_POD=$(kubectl get pods -n argo-workflows -l app.kubernetes.io/component=server -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
echo "  Pod: $NEW_POD"
kubectl logs -n argo-workflows $NEW_POD --tail=20 2>&1
echo ""

echo "=== 3. TEST FROM WSL ==="
curl -s http://workflows.mrrobot.fs/api/v1/info 2>&1
echo ""

echo "=== 4. TEST MAIN ==="
curl -sI http://workflows.mrrobot.fs/ 2>&1 | head -5
echo ""

echo "DONE"
