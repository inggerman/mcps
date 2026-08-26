#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PUSH FIXED DOCKERFILES TO GITEA ==="
cd /tmp
rm -rf agents-platform-push 2>/dev/null
git clone "http://ghl-admin:ChangeMe123!@gitea-http-fixed.gitea.svc.cluster.local:3000/ghl/agents-platform.git" agents-platform-push 2>&1 | tail -3
cd agents-platform-push

echo "=== 2. CHECK REPO STRUCTURE ==="
ls -la Dockerfile.api Dockerfile.worker pyproject.toml 2>&1
echo ""

echo "=== 3. CHECK FOR MCP DOCKERFILES ==="
find . -name "Dockerfile*" 2>&1
echo ""
ls -la mcp* 2>&1 || echo "No mcp dirs at root"
echo ""
find . -type d -name "mcp*" 2>&1
echo ""

echo "=== 4. CHECK agents_platform MODULE ==="
ls -la agents_platform/ 2>&1 || echo "No agents_platform dir"
echo ""
ls agents_platform/__init__.py 2>&1 || echo "No __init__.py"
echo ""

echo "DONE"
