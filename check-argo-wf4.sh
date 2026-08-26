#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. NEW POD LOGS ==="
kubectl logs -n argo-workflows argo-workflows-server-5bb4465fb9-dpl6j --tail=30 2>&1
echo ""

echo "=== 2. CHECK CONFIGMAP ==="
kubectl get cm argo-workflows-workflow-controller-configmap -n argo-workflows -o yaml 2>&1
echo ""

echo "=== 3. CHECK HELM VALUES FOR SSO ==="
helm get values argo-workflows -n argo-workflows -o yaml 2>&1 | grep -i -A5 "sso\|auth\|login" || echo "  No SSO/auth config found"
echo ""

echo "=== 4. TEST API INFO ==="
curl -s http://workflows.mrrobot.fs/api/v1/info 2>&1
echo ""

echo "DONE"
