#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK GITEA REPO - VALUES.YAML ==="
# Clone the repo to check
cd /tmp
rm -rf platform-check 2>/dev/null
git clone http://gitea-http-fixed.gitea.svc.cluster.local:3000/ghl/platform.git platform-check 2>&1 | tail -3
echo ""

echo "=== 2. CHECK NAMESPACE IN VALUES ==="
grep "namespace:" platform-check/gitops/apps/mcp-services/values.yaml 2>&1
echo ""

echo "=== 3. CHECK GIT LOG ==="
cd platform-check
git log --oneline -3 2>&1
echo ""

echo "=== 4. CLEANUP ==="
cd /tmp
rm -rf platform-check 2>/dev/null

echo "DONE"
