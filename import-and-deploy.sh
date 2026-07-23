#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== IMPORTING 35 MCP IMAGES INTO K3S CONTAINERD ==="
echo ""

TAR_FILE="/mnt/c/Users/German/mcp-all-images.tar"

if [ ! -f "$TAR_FILE" ]; then
  echo "ERROR: Tar file not found at $TAR_FILE"
  exit 1
fi

echo "  Tar file size: $(du -h $TAR_FILE | cut -f1)"
echo ""

echo "=== Importing images into K3s containerd ==="
k3s ctr images import "$TAR_FILE" 2>&1 | tail -20
echo ""

echo "=== Verify images in containerd ==="
k3s ctr images ls 2>/dev/null | grep "harbor.mrrobot.fs/ghl/mcp-" | wc -l | xargs echo "  Images found:"
echo ""

echo "=== Generate and apply K8s manifests ==="
cd /tmp/mcps-deploy 2>/dev/null || {
  rm -rf /tmp/mcps-deploy
  mkdir -p /tmp/mcps-deploy
  cd /tmp/mcps-deploy
  tar -xzf /mnt/c/Users/German/mcps-deploy.tar.gz
}
pip install pyyaml -q 2>/dev/null
python3 k8s/generate_manifests.py 2>&1
echo ""

echo "=== Apply manifests ==="
k3s kubectl apply -f k8s/all-mcps.yaml 2>&1 | grep -cE "created|configured" | xargs echo "  Resources created:"
echo ""

echo "=== Wait 60s for pods ==="
sleep 60
echo ""

echo "=== Pod status ==="
k3s kubectl get pods -n mcps 2>&1
echo ""

RUNNING=$(k3s kubectl get pods -n mcps --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
TOTAL_PODS=$(k3s kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l)
echo "  Running: ${RUNNING}/${TOTAL_PODS}"
echo ""

echo "=== Services ==="
k3s kubectl get svc -n mcps 2>&1 | head -20
echo ""

echo "=== Ingress ==="
k3s kubectl get ingress -n mcps 2>&1
echo ""

echo "DONE"
