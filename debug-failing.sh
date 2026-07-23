#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. CHECK ALL FAILING PODS ==="
for POD in mcp-github mcp-prompt-engineer mcp-gob-mexico mcp-project-memory; do
  PODNAME=$(k3s kubectl get pods -n mcps -l app=$POD -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  echo "--- $POD ($PODNAME) ---"
  k3s kubectl logs $PODNAME -n mcps --tail=10 2>&1
  echo ""
done
echo ""

echo "=== 2. CHECK mcp-docker AFTER PATCH ==="
k3s kubectl get pod -n mcps -l app=mcp-docker 2>&1
echo ""

echo "=== 3. CHECK SHARED MODULE IN IMAGES ==="
# The issue is that some Dockerfiles don't copy the shared/ directory
# Let's check which MCPs have this issue
echo "  Checking Dockerfiles for shared module..."
for mcp in mcp-github mcp-prompt-engineer mcp-gob-mexico mcp-project-memory; do
  echo -n "    $mcp: "
  grep -c "shared" /tmp/mcps-deploy/$mcp/Dockerfile 2>/dev/null || echo "0"
done
echo ""

echo "=== 4. CHECK WHICH DOCKERFILES COPY shared ==="
for mcp in $(ls -d /tmp/mcps-deploy/mcp-*/); do
  name=$(basename $mcp)
  has_shared=$(grep -c "shared" $mcp/Dockerfile 2>/dev/null || echo "0")
  if [ "$has_shared" = "0" ]; then
    echo "  MISSING shared: $name"
  fi
done
echo ""

echo "DONE"
