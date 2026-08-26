#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. ARGOCD APPLICATIONS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 2. APPLICATIONSETS ==="
kubectl get applicationsets -A 2>&1
echo ""

echo "=== 3. APPSET DETAILS (agents-platform entries) ==="
kubectl get applicationset user-services-multi-env -n argocd -o jsonpath='{.spec.generators[0].list.elements}' 2>&1 | python3 -c "
import json, sys
data = json.load(sys.stdin)
for e in data:
    if 'agents' in e.get('service',''):
        print(f'  {e}')
" 2>&1
echo ""

echo "=== 4. AGENTS-PLATFORM NAMESPACES ==="
kubectl get ns agents-platform 2>&1
kubectl get ns agents-platform-qa 2>&1
echo ""

echo "=== 5. AGENTS-PLATFORM DEPLOYMENTS ==="
kubectl get deploy -n agents-platform 2>&1
kubectl get deploy -n agents-platform-qa 2>&1
echo ""

echo "=== 6. CHECK GITEA REPO FOR agents-platform ==="
GITEA_IP=$(kubectl get svc gitea-http-fixed -n gitea -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
cd /tmp
rm -rf platform-check 2>/dev/null
git clone "http://$GITEA_IP:3000/ghl/platform.git" platform-check 2>&1 | tail -3
echo ""

echo "=== 7. CHECK gitops/apps/agents-platform ==="
ls -la platform-check/gitops/apps/agents-platform/ 2>&1
echo ""

echo "=== 8. CHECK OVERLAYS ==="
ls -la platform-check/gitops/apps/agents-platform/overlays/ 2>&1
echo ""

echo "=== 9. CLEANUP ==="
cd /tmp
rm -rf platform-check 2>/dev/null

echo "DONE"
