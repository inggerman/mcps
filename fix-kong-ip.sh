#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. CHECK CURRENT KONG PROXY ==="
kubectl get svc kong-kong-proxy -n kong -o yaml 2>&1 | grep -E "externalIPs|loadBalancerIP|clusterIP|nodePort|port" | head -10
echo ""

echo "=== 2. PATCH KONG TO ADD TAILSCALE IP AS EXTERNAL IP ==="
kubectl patch svc kong-kong-proxy -n kong -p '{"spec":{"externalIPs":["100.68.63.120"]}}' 2>&1
echo ""

echo "=== 3. CHECK KONG SVC AFTER PATCH ==="
kubectl get svc kong-kong-proxy -n kong 2>&1
echo ""

echo "=== 4. TEST FROM WSL - PORT 80 VIA TAILSCALE IP ==="
curl -sI -H "Host: gitea.mrrobot.fs" http://100.68.63.120/ 2>&1 | head -5
echo ""

echo "=== 5. CHECK K3S NODE EXTERNAL IPs ==="
kubectl get nodes -o jsonpath='{.items[0].status.addresses}' 2>&1
echo ""
echo ""

echo "=== 6. CHECK IF 192.168.100.210 IS STILL ON AN INTERFACE ==="
ip addr 2>&1 | grep "192.168.100"
echo ""

echo "DONE"
