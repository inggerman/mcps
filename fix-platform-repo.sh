#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

GITEA_IP=$(kubectl get svc gitea-http-fixed -n gitea -o jsonpath='{.spec.clusterIP}' 2>/dev/null)

cd /tmp/platform-repo

echo "=== 1. FIX MERGE CONFLICT IN application-set-multi-env.yaml ==="
cat > gitops/apps/application-set-multi-env.yaml << 'YAMLEOF'
# =============================================================================
# ApplicationSet — Servicios de usuario multi-entorno (qa, stg, prod)
# =============================================================================
# Genera aplicaciones Argo CD para cada servicio en cada entorno.
# Los entornos se definen como overlays Kustomize en gitops/apps/<service>/overlays/.
# Estructura: gitops/apps/<service>/overlays/{qa,stg,prod}/
#
# Cada entorno despliega desde su rama correspondiente:
#   qa   ← rama dev
#   stg  ← rama qa
#   prod ← rama prod
# =============================================================================
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: user-services-multi-env
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - service: demo-service
            env: qa
            branch: dev
            namespace: demo-service-qa
            host: demo-qa.mrrobot.fs
          - service: demo-service
            env: stg
            branch: qa
            namespace: demo-service-stg
            host: demo-stg.mrrobot.fs
          - service: demo-service
            env: prod
            branch: prod
            namespace: demo-service-prod
            host: demo.mrrobot.fs
          - service: agents-platform
            env: qa
            branch: dev
            namespace: agents-platform-qa
            host: agents-qa.mrrobot.fs
          - service: agents-platform
            env: prod
            branch: prod
            namespace: agents-platform
            host: agents.mrrobot.fs
  template:
    metadata:
      name: '{{service}}-{{env}}'
      annotations:
        argocd.argoproj.io/sync-wave: "5"
      labels:
        app.kubernetes.io/name: '{{service}}'
        app.kubernetes.io/part-of: '{{service}}'
        env: '{{env}}'
    spec:
      project: services
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      source:
        repoURL: http://gitea-http-fixed.gitea.svc.cluster.local:3000/ghl/platform.git
        targetRevision: '{{branch}}'
        path: 'gitops/apps/{{service}}/overlays/{{env}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
YAMLEOF
echo "  Fixed"
echo ""

echo "=== 2. CHECK FOR OTHER MERGE CONFLICTS ==="
grep -rl "<<<<<<< HEAD" . 2>/dev/null || echo "  No other conflicts"
echo ""

echo "=== 3. COMMIT AND PUSH TO main ==="
git config user.name "GHL Admin"
git config user.email "admin@mrrobot.fs"
git add -A
git commit -m "fix: resolve merge conflict in application-set-multi-env.yaml, add agents-platform to ArgoCD"
git push origin main 2>&1 | tail -5
echo ""

echo "=== 4. CHECK dev BRANCH ==="
git checkout dev 2>&1 | tail -3
grep -c "agents-platform" gitops/apps/application-set-multi-env.yaml 2>&1 || echo "  agents-platform not in dev branch"
echo ""

echo "=== 5. MERGE main INTO dev AND PUSH ==="
git merge main --no-edit 2>&1 | tail -5
git push origin dev 2>&1 | tail -3
echo ""

echo "=== 6. CHECK prod BRANCH ==="
git checkout prod 2>&1 | tail -3
grep -c "agents-platform" gitops/apps/application-set-multi-env.yaml 2>&1 || echo "  agents-platform not in prod branch"
echo ""

echo "=== 7. MERGE main INTO prod AND PUSH ==="
git merge main --no-edit 2>&1 | tail -5
git push origin prod 2>&1 | tail -3
echo ""

echo "=== 8. BACK TO main ==="
git checkout main 2>&1
echo ""

echo "DONE"
