#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. CHECK MCP-GOB-MEXICO FULL LOGS ==="
kubectl logs -n mcps deploy/mcp-gob-mexico --tail=50 2>&1 | head -30

echo ""
echo "=== 2. CHECK MCP-GOB-MEXICO STARTUP ERROR ==="
kubectl logs -n mcps deploy/mcp-gob-mexico --previous --tail=30 2>&1 | head -30

echo ""
echo "=== 3. DESCRIBE POD ==="
kubectl describe pod -n mcps -l app.kubernetes.io/name=mcp-gob-mexico 2>&1 | tail -30

echo "DONE"
