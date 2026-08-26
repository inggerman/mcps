#!/bin/bash
sleep 30
export KUBECONFIG=/home/german/.kube/config

echo "=== K3S STATUS ==="
systemctl is-active k3s 2>&1
echo ""

echo "=== UNKNOWN PODS ==="
kubectl get pods -A --field-selector=status.phase=Unknown 2>&1
echo ""

echo "=== NOT RUNNING ==="
kubectl get pods -A --field-selector=status.phase!=Running 2>&1
echo ""

echo "=== K3S JOURNAL ==="
journalctl -u k3s --no-pager -n 30 2>&1
echo ""

echo "=== DMESG (last 20) ==="
dmesg 2>&1 | tail -20
echo ""

echo "DONE"
