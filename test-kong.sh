#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. CHECK IF HOSTS FILE WAS UPDATED ==="
# Test from inside WSL if the DNS resolves correctly
ping -c 1 -W 2 mcp-tabular.mrrobot.fs 2>&1 | head -2
echo ""

echo "=== 2. TEST ACCESS VIA KONG PROXY IP DIRECTLY ==="
# Test with curl using --resolve to bypass DNS
KONG_IP="192.168.100.210"
echo "  Testing mcp-tabular via Kong (${KONG_IP})..."
curl -s --connect-timeout 5 -X POST "http://${KONG_IP}/mcp" \
  -H "Host: mcp-tabular.mrrobot.fs" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>&1 | head -5
echo ""

echo "  Testing mcp-calendar via Kong..."
curl -s --connect-timeout 5 -X POST "http://${KONG_IP}/mcp" \
  -H "Host: mcp-calendar.mrrobot.fs" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>&1 | head -5
echo ""

echo "  Testing mcp-github via Kong..."
curl -s --connect-timeout 5 -X POST "http://${KONG_IP}/mcp" \
  -H "Host: mcp-github.mrrobot.fs" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' 2>&1 | head -5
echo ""

echo "=== 3. CHECK KONG ROUTES ==="
k3s kubectl get httproutes -n mcps 2>&1 || echo "  No HTTPRoutes in mcps namespace"
k3s kubectl get ingress -n mcps 2>&1
echo ""

echo "=== 4. CHECK KONG INGRESS CLASS ==="
k3s kubectl get ingressclass 2>&1
echo ""

echo "=== 5. CHECK IF KONG PROCESSES MCP INGRESS ==="
# The ingress has no class assigned - Kong might not pick it up
# Let's check Kong's proxy upstreams
k3s kubectl get proxyroutes -n mcps 2>&1 || echo "  No ProxyRoutes"
echo ""

echo "DONE"
