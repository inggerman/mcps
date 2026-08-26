#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CLONE ghl/platform REPO ==="
cd /tmp
rm -rf platform-repo 2>/dev/null
git clone "http://10.43.200.50:3000/ghl/platform.git" platform-repo 2>&1 | tail -3
echo ""

echo "=== 2. CHECK CURRENT VALUES ==="
grep "namespace:" platform-repo/gitops/apps/mcp-services/values.yaml 2>&1
echo ""

echo "=== 3. CHECK IF app.yaml EXISTS ==="
ls -la platform-repo/gitops/apps/mcp-services/app.yaml 2>&1
echo ""

echo "=== 4. CHECK GIT LOG ==="
cd platform-repo
git log --oneline -5 2>&1
echo ""

echo "=== 5. CHECK REMOTES ==="
git remote -v 2>&1
echo ""

echo "=== 6. CLEANUP ==="
cd /tmp
rm -rf platform-repo 2>/dev/null

echo "DONE"
