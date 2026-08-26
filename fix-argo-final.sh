#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PATCH DEPLOYMENT - auth-mode=server + secure=false ==="
kubectl patch deploy -n argo-workflows argo-workflows-server --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/args","value":["server","--configmap=argo-workflows-workflow-controller-configmap","--secure=false","--loglevel","info","--gloglevel","0","--log-format","text","--auth-mode=server"]}]' 2>&1
echo ""

echo "=== 2. WAIT FOR ROLLOUT ==="
kubectl rollout status deploy -n argo-workflows argo-workflows-server --timeout=90s 2>&1
echo ""

echo "=== 3. PODS ==="
kubectl get pods -n argo-workflows 2>&1
echo ""

echo "=== 4. WAIT 5s ==="
sleep 5
echo ""

echo "=== 5. LOGS ==="
kubectl logs -n argo-workflows -l app.kubernetes.io/component=server --tail=15 2>&1
echo ""

echo "=== 6. TEST NO-AUTH API ==="
curl -s http://workflows.mrrobot.fs/api/v1/info 2>&1
echo ""

echo "=== 7. TEST VERSION ==="
curl -s http://workflows.mrrobot.fs/api/v1/version 2>&1
echo ""

echo "DONE"
