#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. CRICTL IMAGES FOR FAILING MCPS ==="
k3s crictl images 2>/dev/null | grep -E "mcp-github|mcp-prompt|mcp-gob|mcp-project-memory" 2>&1
echo ""

echo "=== 2. ALL CRICTL IMAGES COUNT ==="
k3s crictl images 2>/dev/null | grep "mcp-" | wc -l | xargs echo "  Total MCP images:"
echo ""

echo "=== 3. CHECK IMAGE ARCHITECTURE ==="
for mcp in mcp-github mcp-project-memory; do
  echo -n "  $mcp: "
  k3s crictl inspecti harbor.mrrobot.fs/ghl/${mcp}:latest 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status',{}).get('reference','?'))" 2>/dev/null || echo "inspect failed"
done
echo ""

echo "=== 4. TRY RUNNING CONTAINER IN K3S CONTAINERD ==="
# Check if the image actually has the files
for mcp in mcp-github mcp-project-memory; do
  echo "  --- $mcp ---"
  k3s crictl run --rm harbor.mrrobot.fs/ghl/${mcp}:latest 2>/dev/null || echo "  crictl run not supported"
  # Try using kubectl debug instead
  PODNAME=$(k3s kubectl get pods -n mcps -l app=$mcp -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  if [ -n "$PODNAME" ]; then
    k3s kubectl exec $PODNAME -n mcps -- ls /app/src/ 2>&1 || echo "  exec failed"
    k3s kubectl exec $PODNAME -n mcps -- python -c "import sys; print(sys.path)" 2>&1 || echo "  exec failed"
  fi
done
echo ""

echo "=== 5. CHECK mcp-gob-mexico (different error - transport issue) ==="
# The error shows it's running in stdio mode, not streamable-http
PODNAME=$(k3s kubectl get pods -n mcps -l app=mcp-gob-mexico -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
k3s kubectl exec $PODNAME -n mcps -- env 2>&1 | grep MCP_ 2>&1 || echo "  exec failed"
echo ""

echo "DONE"
