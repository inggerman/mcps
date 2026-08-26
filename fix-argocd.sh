#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PATCH ARGOCD TO INSECURE MODE (HTTP) ==="
kubectl patch cm argocd-cmd-params-cm -n argocd -p '{"data":{"server.insecure":"true"}}' 2>&1
echo ""

echo "=== 2. RESTART ARGOCD SERVER ==="
kubectl rollout restart deploy argocd-server -n argocd 2>&1
echo ""

echo "=== 3. WAIT FOR ROLLOUT ==="
kubectl rollout status deploy argocd-server -n argocd --timeout=60s 2>&1
echo ""

echo "=== 4. CHECK PODS ==="
kubectl get pods -n argocd 2>&1
echo ""

echo "=== 5. WAIT 5s ==="
sleep 5
echo ""

echo "=== 6. TEST FROM WSL ==="
curl -sI http://argocd.mrrobot.fs/ 2>&1 | head -10
echo ""

echo "=== 7. ARGOCD APPLICATIONS ==="
kubectl get applications -A 2>&1
echo ""

echo "DONE"
