#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. WSL CURRENT IPs ==="
ip addr show 2>&1 | grep "inet " | grep -v "127.0.0.1"
echo ""

echo "=== 2. KONG LB EXTERNAL IP ==="
kubectl get svc kong-kong-proxy -n kong 2>&1
echo ""

echo "=== 3. K3S NODE IP ==="
kubectl get nodes -o wide 2>&1
echo ""

echo "=== 4. CHECK IF 192.168.100.210 EXISTS ==="
ip addr 2>&1 | grep "192.168.100" || echo "  NOT FOUND - this IP no longer exists"
echo ""

echo "=== 5. TAILSCALE IP ==="
tailscale ip -4 2>&1 || echo "  tailscale not found"
echo ""

echo "=== 6. WSL NETWORK MODE ==="
cat /etc/wsl.conf 2>&1
echo ""

echo "=== 7. CHECK WINDOWS HOSTS FILE ==="
cat /mnt/c/Windows/System32/drivers/etc/hosts 2>&1 | grep -E "mrrobot|100.68" | head -30
echo ""

echo "DONE"
