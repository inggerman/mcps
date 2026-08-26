#!/bin/bash
export KUBECONFIG=/home/german/.kube/config
export PATH=/usr/local/bin:/usr/bin:$PATH

echo "=== API LOGS ==="
kubectl logs -n agents-platform agents-platform-api-6bd687686-hfsl9 --tail=15 2>&1
echo ""

echo "=== WORKER LOGS ==="
kubectl logs -n agents-platform agents-platform-worker-84bb8b5589-297m6 --tail=15 2>&1
echo ""

echo "=== DAEMON LOGS ==="
kubectl logs -n agents-platform agents-platform-daemon-7c49947959-jzvmp --tail=10 2>&1
echo ""

echo "=== MCP WEB SEARCH LOGS ==="
kubectl logs -n agents-platform mcp-web-search-5c5c978b49-8tgn7 --tail=10 2>&1
echo ""

echo "=== MCP SOURCE VALIDATOR LOGS ==="
kubectl logs -n agents-platform mcp-source-validator-654b48ff9-bmq9x --tail=10 2>&1
echo ""

echo "DONE"
