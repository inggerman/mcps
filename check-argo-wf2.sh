#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. SERVER POD LOGS ==="
kubectl logs -n argo-workflows argo-workflows-server-6456d798f8-5qjnj --tail=50 2>&1
echo ""

echo "=== 2. HELM VALUES ==="
helm get values argo-workflows -n argo-workflows 2>&1
echo ""

echo "=== 3. TEST FROM INSIDE CLUSTER ==="
kubectl exec -n argo-workflows argo-workflows-server-6456d798f8-5qjnj -- curl -sI http://localhost:2746/ 2>&1 | head -10
echo ""

echo "=== 4. TEST OAUTH ENDPOINT ==="
kubectl exec -n argo-workflows argo-workflows-server-6456d798f8-5qjnj -- curl -sI http://localhost:2746/oauth2/redirect 2>&1 | head -10
echo ""

echo "=== 5. CHECK SERVER ARGS ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o jsonpath='{.spec.template.spec.containers[0].args}' 2>&1
echo ""
echo ""

echo "=== 6. CHECK SERVER ENV ==="
kubectl get deploy -n argo-workflows argo-workflows-server -o jsonpath='{.spec.template.spec.containers[0].env}' 2>&1
echo ""

echo "DONE"
