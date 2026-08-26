#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CREATE LONG-LIVED SECRET TOKEN ==="
cat <<'EOF' | kubectl apply -f - 2>&1
apiVersion: v1
kind: Secret
metadata:
  name: argo-admin-token
  namespace: argo-workflows
  annotations:
    kubernetes.io/service-account.name: argo-admin
type: kubernetes.io/service-account-token
EOF
echo ""

echo "=== 2. WAIT FOR TOKEN ==="
sleep 3
echo ""

echo "=== 3. GET PERMANENT TOKEN ==="
TOKEN=$(kubectl get secret argo-admin-token -n argo-workflows -o jsonpath='{.data.token}' 2>/dev/null | base64 -d)
echo "$TOKEN"
echo ""

echo "=== 4. TEST WITH TOKEN ==="
curl -s -H "Authorization: Bearer $TOKEN" http://workflows.mrrobot.fs/api/v1/info 2>&1
echo ""

echo "=== 5. TEST API VERSION ==="
curl -s -H "Authorization: Bearer $TOKEN" http://workflows.mrrobot.fs/api/v1/version 2>&1
echo ""

echo "DONE"
