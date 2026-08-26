#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. APPLY UPDATED APPLICATIONSET ==="
cat <<'EOF' | kubectl apply -f - 2>&1
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
EOF
echo ""

echo "=== 2. WAIT 15s ==="
sleep 15
echo ""

echo "=== 3. CHECK ALL APPLICATIONS ==="
kubectl get applications -A 2>&1
echo ""

echo "=== 4. CHECK APPLICATIONSET ==="
kubectl get applicationset user-services-multi-env -n argocd 2>&1
echo ""

echo "=== 5. CHECK agents-platform APPS ==="
kubectl get application agents-platform-qa -n argocd 2>&1
kubectl get application agents-platform-prod -n argocd 2>&1
echo ""

echo "DONE"
