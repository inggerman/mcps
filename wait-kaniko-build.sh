#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== WAITING 3min FOR KANIKO BUILD ==="
sleep 180
echo ""

echo "=== 1. POD STATUS ==="
kubectl get pods -n gitea-runner -l job-name=build-agents-platform 2>&1
echo ""

echo "=== 2. JOB STATUS ==="
kubectl get job build-agents-platform -n gitea-runner 2>&1
echo ""

echo "=== 3. LOGS ==="
POD=$(kubectl get pods -n gitea-runner -l job-name=build-agents-platform -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
echo "Pod: $POD"
echo ""
echo "--- KANIKO-API ---"
kubectl logs -n gitea-runner $POD -c kaniko-api --tail=30 2>&1
echo ""
echo "--- KANIKO-WORKER ---"
kubectl logs -n gitea-runner $POD -c kaniko-worker --tail=30 2>&1
echo ""

echo "=== 4. CHECK HARBOR REPOS ==="
curl -s "http://harbor-core.harbor.svc.cluster.local/api/v2.0/projects/ghl/repositories" -u "admin:Harbor12345" 2>&1 | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for r in data:
        name = r.get('name','')
        if 'agent' in name:
            print(f'  FOUND: {name}')
    print(f'  Total repos: {len(data)}')
except Exception as e:
    print(f'  Error: {e}')
" 2>&1
echo ""

echo "DONE"
