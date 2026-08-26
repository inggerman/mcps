#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

GITEA_IP=$(kubectl get svc gitea-http-fixed -n gitea -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
echo "Gitea IP: $GITEA_IP"

echo "=== 1. CLONE ghl/platform REPO ==="
cd /tmp
rm -rf platform-repo 2>/dev/null
git clone "http://ghl-admin:ChangeMe123!@$GITEA_IP:3000/ghl/platform.git" platform-repo 2>&1 | tail -3
echo ""

echo "=== 2. CHECK EXISTING STRUCTURE ==="
ls -la platform-repo/gitops/apps/agents-platform/ 2>&1
echo ""

echo "=== 3. CHECK BRANCHES ==="
cd platform-repo
git branch -a 2>&1
echo ""

echo "=== 4. CHECK CURRENT main BRANCH ==="
git log --oneline -3 2>&1
echo ""

echo "=== 5. CHECK IF agents-platform EXISTS ON main ==="
ls -la gitops/apps/agents-platform/base/ 2>&1
ls -la gitops/apps/agents-platform/overlays/qa/ 2>&1
ls -la gitops/apps/agents-platform/overlays/prod/ 2>&1
echo ""

echo "=== 6. CHECK APPLICATIONSET ==="
cat gitops/apps/application-set-multi-env.yaml 2>&1 | head -50
echo ""

echo "DONE"
