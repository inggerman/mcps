#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. Import fixed images ==="
k3s ctr images import /mnt/c/Users/German/mcp-fixed-images.tar 2>&1 | tail -5
echo ""

echo "=== 2. Verify images in containerd ==="
k3s ctr images ls 2>/dev/null | grep -E "mcp-github|mcp-prompt-engineer|mcp-gob-mexico|mcp-project-memory" | wc -l | xargs echo "  Fixed images found:"
echo ""

echo "=== 3. Delete failing pods to force restart ==="
for mcp in mcp-github mcp-prompt-engineer mcp-gob-mexico mcp-project-memory; do
  PODNAME=$(k3s kubectl get pods -n mcps -l app=$mcp -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  if [ -n "$PODNAME" ]; then
    echo "  Deleting $PODNAME..."
    k3s kubectl delete pod $PODNAME -n mcps --grace-period=0 --force 2>&1 | head -1
  fi
done
echo ""

echo "=== 4. Wait 45s ==="
sleep 45
echo ""

echo "=== 5. POD STATUS ==="
k3s kubectl get pods -n mcps 2>&1
echo ""

RUNNING=$(k3s kubectl get pods -n mcps --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
TOTAL=$(k3s kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l)
echo "  Running: ${RUNNING}/${TOTAL}"
echo ""

echo "=== 6. CHECK FIXED PODS LOGS ==="
for mcp in mcp-github mcp-prompt-engineer mcp-gob-mexico mcp-project-memory; do
  PODNAME=$(k3s kubectl get pods -n mcps -l app=$mcp -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  echo "--- $mcp ($PODNAME) ---"
  k3s kubectl logs $PODNAME -n mcps --tail=5 2>&1
  echo ""
done
echo ""

echo "DONE"
