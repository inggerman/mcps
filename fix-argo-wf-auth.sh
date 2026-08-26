#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CREATE SERVICE ACCOUNT ==="
kubectl create serviceaccount argo-admin -n argo-workflows 2>&1 || echo "  Already exists"
echo ""

echo "=== 2. CREATE CLUSTER ROLE BINDING ==="
kubectl create clusterrolebinding argo-admin-binding --clusterrole=cluster-admin --serviceaccount=argo-workflows:argo-admin 2>&1 || echo "  Already exists"
echo ""

echo "=== 3. GET TOKEN ==="
SECRET_NAME=$(kubectl get sa argo-admin -n argo-workflows -o jsonpath='{.secrets[0].name}' 2>/dev/null)
echo "  Secret: $SECRET_NAME"
if [ -n "$SECRET_NAME" ]; then
  TOKEN=$(kubectl get secret $SECRET_NAME -n argo-workflows -o jsonpath='{.data.token}' 2>/dev/null | base64 -d)
  echo "  Token: $TOKEN"
else
  echo "  No secret found, trying new K8s approach..."
  TOKEN=$(kubectl create token argo-admin -n argo-workflows 2>&1)
  echo "  Token: $TOKEN"
fi
echo ""

echo "=== 4. TEST WITH TOKEN ==="
curl -s -H "Authorization: Bearer $TOKEN" http://workflows.mrrobot.fs/api/v1/info 2>&1
echo ""

echo "DONE"
