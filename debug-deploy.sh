#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. NAMESPACE ==="
k3s kubectl get namespace mcps 2>&1
echo ""

echo "=== 2. DEPLOYMENTS ==="
k3s kubectl get deploy -n mcps 2>&1 | head -20
echo ""

echo "=== 3. PVCs ==="
k3s kubectl get pvc -n mcps 2>&1
echo ""

echo "=== 4. EVENTS ==="
k3s kubectl get events -n mcps --sort-by=.lastTimestamp 2>&1 | tail -30
echo ""

echo "=== 5. CHECK ONE DEPLOYMENT ==="
k3s kubectl describe deploy mcp-tabular -n mcps 2>&1 | tail -30
echo ""

echo "=== 6. CHECK KYVERNO POLICIES ==="
k3s kubectl get cpol 2>&1
echo ""

echo "=== 7. CHECK STORAGE CLASS ==="
k3s kubectl get sc 2>&1
echo ""

echo "DONE"
