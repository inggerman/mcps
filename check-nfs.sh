#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. NFS PROVISIONER PODS ==="
kubectl get pods -A 2>&1 | grep -i nfs
echo ""

echo "=== 2. NFS PROVISIONER DEPLOYMENT ==="
kubectl get deploy -A 2>&1 | grep -i nfs
echo ""

echo "=== 3. CHECK IN ALL NAMESPACES ==="
kubectl get pods -A 2>&1 | grep -i "nfs\|subdir"
echo ""

echo "=== 4. CHECK PVC mcp-workspace ==="
kubectl describe pvc mcp-workspace -n mcps 2>&1 | tail -10
echo ""

echo "=== 5. PODS NOT PENDING (already running) ==="
kubectl get pods -n mcps --field-selector=status.phase=Running 2>&1
echo ""

echo "=== 6. PODS THAT DON'T NEED workspace PVC ==="
# Pods without workspace mount should be able to start
kubectl get pods -n mcps --no-headers 2>&1 | grep -v Pending | head -10
echo ""

echo "DONE"
