#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. CHECK CURRENT CONFIG ==="
cat /etc/rancher/k3s/config.yaml 2>/dev/null || echo "  No config.yaml"
echo ""

echo "=== 2. FIX CONFIG ==="
cat > /etc/rancher/k3s/config.yaml << 'EOF'
maxPods: 200
kubelet-arg:
  - "max-pods=200"
EOF
echo "  Config written:"
cat /etc/rancher/k3s/config.yaml
echo ""

echo "=== 3. CHECK K3S SERVICE ==="
cat /etc/systemd/system/k3s.service 2>/dev/null | head -20
echo ""

echo "=== 4. RESTART K3S VIA SYSTEMD ==="
systemctl restart k3s 2>/dev/null || {
  echo "  systemctl not available, trying direct restart..."
  killall k3s 2>/dev/null
  sleep 5
  k3s server --config /etc/rancher/k3s/config.yaml &
  sleep 20
}
echo "  K3s restarted"
echo ""

echo "=== 5. VERIFY ==="
sleep 10
k3s kubectl get nodes 2>&1
echo ""

echo "=== 6. CHECK POD LIMIT ==="
k3s kubectl describe node | grep -A5 "Allocatable:" | grep pods
echo ""

echo "=== 7. CHECK MCP PODS ==="
k3s kubectl get pods -n mcps 2>&1 | head -20
echo ""

RUNNING=$(k3s kubectl get pods -n mcps --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
TOTAL=$(k3s kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l)
echo "  Running: ${RUNNING}/${TOTAL}"
echo ""

echo "DONE"
