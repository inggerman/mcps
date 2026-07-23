#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== MCP PODS ==="
TOTAL=$(kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l)
RUNNING=$(kubectl get pods -n mcps --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
echo "Total: $TOTAL  Running: $RUNNING"

echo ""
echo "=== GITEA PODS ==="
kubectl get pods -n gitea 2>/dev/null

echo ""
echo "=== GITEA ACTIONS ==="
kubectl get pods -A 2>/dev/null | grep -i runner || echo "No runner pods found"

echo ""
echo "=== RECENT MCP EVENTS ==="
kubectl get events -n mcps --sort-by=.lastTimestamp 2>/dev/null | tail -5

echo ""
echo "=== GITEA WORKFLOWS ==="
kubectl get pods -n gitea 2>/dev/null

echo "DONE"
