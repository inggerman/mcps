#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. GET GITEA SERVICE IP ==="
GITEA_IP=$(kubectl get svc gitea-http -n gitea -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "  Gitea IP: $GITEA_IP"
echo ""

echo "=== 2. CLONE REPO ==="
cd /tmp
rm -rf platform-check 2>/dev/null
git clone "http://$GITEA_IP:3000/ghl/platform.git" platform-check 2>&1 | tail -3
echo ""

echo "=== 3. CHECK NAMESPACE IN VALUES ==="
grep "namespace:" platform-check/gitops/apps/mcp-services/values.yaml 2>&1
echo ""

echo "=== 4. CHECK GIT LOG ==="
cd platform-check
git log --oneline -5 2>&1
echo ""

echo "=== 5. CLEANUP ==="
cd /tmp
rm -rf platform-check 2>/dev/null

echo "DONE"
