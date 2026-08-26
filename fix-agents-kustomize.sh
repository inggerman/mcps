#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

GITEA_IP=$(kubectl get svc gitea-http-fixed -n gitea -o jsonpath='{.spec.clusterIP}' 2>/dev/null)

cd /tmp/platform-repo

echo "=== 1. PULL LATEST main ==="
git checkout main 2>&1
git pull origin main 2>&1 | tail -3
echo ""

echo "=== 2. FIX kustomization.yaml - remove namespace.yaml ==="
cat > gitops/apps/agents-platform/base/kustomization.yaml << 'YAMLEOF'
# =============================================================================
# Base — agents-platform (API + Worker + Daemon + MCPs)
# =============================================================================
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - platform-deployment.yaml

images:
  - name: harbor.mrrobot.fs/ghl/agents-platform-api
    newTag: latest
  - name: harbor.mrrobot.fs/ghl/agents-platform-worker
    newTag: latest
  - name: harbor.mrrobot.fs/ghl/mcp-web-search
    newTag: latest
  - name: harbor.mrrobot.fs/ghl/mcp-source-validator
    newTag: latest
YAMLEOF
echo "  Fixed"
echo ""

echo "=== 3. COMMIT AND PUSH main ==="
git add gitops/apps/agents-platform/base/kustomization.yaml
git commit -m "fix: remove namespace.yaml from base (AppProject blacklists Namespace)"
git push origin main 2>&1 | tail -3
echo ""

echo "=== 4. MERGE TO dev ==="
git checkout dev 2>&1 | tail -1
git merge main --no-edit 2>&1 | tail -3
git push origin dev 2>&1 | tail -3
echo ""

echo "=== 5. MERGE TO prod ==="
git checkout prod 2>&1 | tail -1
git merge main --no-edit 2>&1 | tail -3
git push origin prod 2>&1 | tail -3
echo ""

echo "=== 6. BACK TO main ==="
git checkout main 2>&1
echo ""

echo "=== 7. DELETE AND RECREATE APPS IN ARGOCD ==="
kubectl delete application agents-platform-qa -n argocd 2>&1
kubectl delete application agents-platform-prod -n argocd 2>&1
echo ""

echo "=== 8. WAIT 10s FOR APPSET TO RECREATE ==="
sleep 10
echo ""

echo "=== 9. CHECK APPLICATIONS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 10. WAIT 30s FOR SYNC ==="
sleep 30
echo ""

echo "=== 11. CHECK STATUS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 12. CHECK PODS ==="
kubectl get pods -n agents-platform 2>&1
kubectl get pods -n agents-platform-qa 2>&1
echo ""

echo "DONE"
