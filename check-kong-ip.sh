#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== KONG LB IP ==="
kubectl get svc kong-kong-proxy -n kong -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>&1
echo ""

echo "=== WSL IP ==="
hostname -I 2>&1
echo ""

echo "=== IP ADDR ==="
ip addr show eth0 2>&1 | grep inet
echo ""

echo "=== CURL KONG IP ==="
curl -sI http://192.168.100.210/ 2>&1 | head -5
echo ""

echo "=== CURL GITEA VIA HOST HEADER ==="
curl -sI -H "Host: gitea.mrrobot.fs" http://192.168.100.210/ 2>&1 | head -10
echo ""

echo "=== CURL HARBOR VIA HOST HEADER ==="
curl -sI -H "Host: harbor.mrrobot.fs" http://192.168.100.210/ 2>&1 | head -10
echo ""

echo "=== CURL ARGOCD VIA HOST HEADER ==="
curl -sI -H "Host: argocd.mrrobot.fs" http://192.168.100.210/ 2>&1 | head -10
echo ""

echo "DONE"
