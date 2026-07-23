#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK MCP-GOB-MEXICO LOGS ==="
kubectl logs -n mcps deploy/mcp-gob-mexico --tail=30 2>&1

echo ""
echo "=== 2. CHECK GITEA ACTIONS RUNNER STATUS ==="
kubectl get pods -n gitea-runner -o wide 2>&1
kubectl logs -n gitea-runner deploy/act-runner --tail=20 2>&1

echo ""
echo "=== 3. CHECK GITEA REPO ACTIONS ==="
# Use Gitea API to check if actions are enabled
curl -s -u "ghl-admin:ChangeMe123!" "http://10.0.0.79:3000/api/v1/repos/ghl-admin/mcps/actions/tasks" 2>&1 | head -20

echo ""
echo "=== 4. CHECK GITEA REPO WORKFLOWS ==="
curl -s -u "ghl-admin:ChangeMe123!" "http://10.0.0.79:3000/api/v1/repos/ghl-admin/mcps/contents/.gitea/workflows" 2>&1 | head -20

echo ""
echo "=== 5. ALL PODS WITH RESTARTS ==="
kubectl get pods -n mcps --field-selector=status.phase=Running 2>/dev/null | awk 'NR>1 && $4>0 {print $1, $4, $5}'

echo "DONE"
