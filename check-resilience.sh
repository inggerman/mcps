#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. K3S AUTO-START ==="
echo "  k3s.service enabled:"
systemctl is-enabled k3s 2>&1
echo ""

echo "=== 2. WSL BOOT COMMAND ==="
cat /etc/wsl.conf 2>/dev/null || echo "  No /etc/wsl.conf"
echo ""

echo "=== 3. CHECK IF K3S STARTS ON BOOT ==="
ls -la /etc/systemd/system/multi-user.target.wants/k3s.service 2>&1
echo ""

echo "=== 4. DEPLOYMENTS WITH RESTARTPOLICY ==="
kubectl get deploy -A -o json 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
total=0
for item in data['items']:
    total+=1
print(f'  Total deployments: {total}')
" 2>/dev/null
echo ""

echo "=== 5. STS COUNT ==="
kubectl get sts -A -o json 2>/dev/null | python3 -c "
import json,sys
data=json.load(sys.stdin)
total=0
for item in data['items']:
    total+=1
print(f'  Total STS: {total}')
" 2>/dev/null
echo ""

echo "=== 6. PVs ==="
kubectl get pv 2>&1 | head -20
echo ""

echo "=== 7. PVCs ==="
kubectl get pvc -A 2>&1 | head -20
echo ""

echo "=== 8. CRITICAL DEPLOYMENTS REPLICAS ==="
kubectl get deploy -A -o wide 2>&1 | grep -E "harbor|gitea|argocd|n8n|mcps" | head -20
echo ""

echo "=== 9. CHECK HARBOR STS ==="
kubectl get sts -n harbor 2>&1
echo ""

echo "=== 10. CHECK RABBITMQ ==="
kubectl get pods -n rabbitmq 2>&1
echo ""

echo "=== 11. CHECK MINIO ==="
kubectl get pods -n minio 2>&1
echo ""

echo "=== 12. CHECK ALL NS WITH PODS ==="
kubectl get pods -A --no-headers 2>/dev/null | awk '{print $1}' | sort -u
echo ""

echo "DONE"
