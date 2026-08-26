#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. SCALE NFS PROVISIONER ==="
kubectl scale deploy nfs-subdir-provisioner-nfs-subdir-external-provisioner -n nfs-storage --replicas=1 2>&1
echo ""

echo "=== 2. WAIT 15s ==="
sleep 15
echo ""

echo "=== 3. NFS POD ==="
kubectl get pods -n nfs-storage 2>&1
echo ""

echo "=== 4. PVC STATUS ==="
kubectl get pvc -n mcps 2>&1
echo ""

echo "=== 5. WAIT 30s FOR PVC BINDING ==="
sleep 30
echo ""

echo "=== 6. PVC STATUS ==="
kubectl get pvc -n mcps 2>&1
echo ""

echo "=== 7. MCP PODS ==="
kubectl get pods -n mcps 2>&1 | head -15
echo ""

echo "=== 8. ARGOCD STATUS ==="
kubectl get application mcp-services -n argocd 2>&1
echo ""

echo "DONE"
