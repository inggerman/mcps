#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== 1. API LOGS (new pod) ==="
kubectl logs -n agents-platform agents-platform-api-595c6c6dbb-r57v7 --tail=20 2>&1
echo ""

echo "=== 2. WORKER LOGS ==="
kubectl logs -n agents-platform agents-platform-worker-5bf7fcb477-28z75 --tail=20 2>&1
echo ""

echo "=== 3. DAEMON LOGS ==="
kubectl logs -n agents-platform agents-platform-daemon-777b455667-2cl5k --tail=20 2>&1
echo ""

echo "=== 4. MCP WEB SEARCH LOGS ==="
kubectl logs -n agents-platform mcp-web-search-669fdd468b-zlmrj --tail=10 2>&1
echo ""

echo "=== 5. MCP SOURCE VALIDATOR LOGS ==="
kubectl logs -n agents-platform mcp-source-validator-555ffbb968-7v4wp --tail=10 2>&1
echo ""

echo "DONE"
