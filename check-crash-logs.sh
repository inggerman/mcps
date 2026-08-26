#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. API CRASH LOGS ==="
kubectl logs -n agents-platform agents-platform-api-7f5d68c5f5-mh54q --tail=20 2>&1
echo ""

echo "=== 2. WORKER CRASH LOGS ==="
kubectl logs -n agents-platform agents-platform-worker-778846697b-hz6d4 --tail=20 2>&1
echo ""

echo "=== 3. DAEMON CRASH LOGS ==="
kubectl logs -n agents-platform agents-platform-daemon-69b776f8cb-tw5f7 --tail=20 2>&1
echo ""

echo "=== 4. CHECK agents-platform REPO FOR MCP DOCKERFILES ==="
# Clone locally to check
cd /tmp
rm -rf agents-platform-check 2>/dev/null
git clone "http://ghl-admin:ChangeMe123!@gitea-http-fixed.gitea.svc.cluster.local:3000/ghl/agents-platform.git" agents-platform-check 2>&1 | tail -3
echo ""
echo "=== Files in repo ==="
ls -la agents-platform-check/ 2>&1
echo ""
echo "=== Dockerfiles ==="
find agents-platform-check -name "Dockerfile*" -o -name "docker-compose*" 2>&1
echo ""
echo "=== MCP dirs ==="
ls -la agents-platform-check/mcp* 2>&1 || echo "No mcp dirs"
echo ""

echo "DONE"
