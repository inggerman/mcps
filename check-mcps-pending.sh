#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. PVCS ==="
kubectl get pvc -n mcps 2>&1
echo ""

echo "=== 2. EVENTS (last 10) ==="
kubectl get events -n mcps --sort-by=.lastTimestamp 2>&1 | tail -10
echo ""

echo "=== 3. NFS PROVISIONER ==="
kubectl get pods -A | grep nfs 2>&1
echo ""

echo "=== 4. STORAGE CLASSES ==="
kubectl get sc 2>&1
echo ""

echo "=== 5. CHECK POD CONDITIONS ==="
kubectl describe pod mcp-agent-runner-695967bcf-6bbvf -n mcps 2>&1 | grep -A10 "Events:" | head -15
echo ""

echo "DONE"
