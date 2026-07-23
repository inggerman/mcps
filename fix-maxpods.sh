#!/bin/bash
export KUBECONFIG=/home/german/.kube/config

echo "=== 1. TOTAL POD COUNT ==="
k3s kubectl get pods -A --no-headers 2>/dev/null | wc -l | xargs echo "  Current pods:"
echo ""

echo "=== 2. PODS PER NAMESPACE ==="
k3s kubectl get pods -A --no-headers 2>/dev/null | awk '{print $1}' | sort | uniq -c | sort -rn
echo ""

echo "=== 3. CHECK K3S MAX-PODS SETTING ==="
ps aux | grep k3s | grep -o -- '--max-pods[^ ]*' || echo "  No --max-pods flag set (default 110)"
echo ""

echo "=== 4. INCREASE MAX-PODS ==="
# Check current K3s service config
cat /etc/systemd/system/k3s.service 2>/dev/null | grep -E "ExecStart|max-pods" || echo "  Checking K3s config file..."
cat /etc/rancher/k3s/config.yaml 2>/dev/null || echo "  No config.yaml found"
echo ""

echo "=== 5. SET MAX-PODS TO 200 ==="
# Add max-pods to K3s config
if [ -f /etc/rancher/k3s/config.yaml ]; then
  if ! grep -q "maxPods" /etc/rancher/k3s/config.yaml; then
    echo "maxPods: 200" >> /etc/rancher/k3s/config.yaml
    echo "  Added maxPods: 200 to config.yaml"
  fi
else
  echo "maxPods: 200" > /etc/rancher/k3s/config.yaml
  echo "  Created config.yaml with maxPods: 200"
fi
echo ""

echo "=== 6. RESTART K3S ==="
systemctl restart k3s 2>/dev/null || k3s-killall.sh 2>/dev/null && k3s server --max-pods=200 &
echo "  K3s restarting..."
sleep 20
echo ""

echo "=== 7. VERIFY K3S IS BACK ==="
k3s kubectl get nodes 2>&1
echo ""

echo "=== 8. CHECK PODS AGAIN ==="
k3s kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l | xargs echo "  MCP pods:"
RUNNING=$(k3s kubectl get pods -n mcps --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
TOTAL=$(k3s kubectl get pods -n mcps --no-headers 2>/dev/null | wc -l)
echo "  Running: ${RUNNING}/${TOTAL}"
echo ""

echo "DONE"
