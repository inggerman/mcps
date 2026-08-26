#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== KONG PODS ==="
kubectl get pods -n kong 2>&1
echo ""

echo "=== KONG SVC ==="
kubectl get svc -n kong 2>&1
echo ""

echo "=== GITEA INGRESS ==="
kubectl get ingress -n gitea 2>&1
echo ""

echo "=== ALL INGRESSES ==="
kubectl get ingress -A 2>&1
echo ""

echo "=== GITEA SVC ==="
kubectl get svc -n gitea 2>&1
echo ""

echo "=== KONG PROXY SVC ==="
kubectl get svc -n kong -o wide 2>&1
echo ""

echo "=== CHECK DNS FROM WSL ==="
nslookup gitea.mrrobot.fs 2>&1 || echo "DNS FAIL"
echo ""

echo "=== CHECK /etc/hosts ==="
cat /etc/hosts 2>&1
echo ""

echo "=== CURL GITEA FROM WSL ==="
curl -sI http://gitea.mrrobot.fs/ 2>&1 | head -10
echo ""

echo "DONE"
